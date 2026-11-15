"""Interactive shell interface for The Pirates using modular mixin architecture."""

import cmd
import json
import time
from pathlib import Path

import questionary

from core.commands import BaseCommandsMixin, NetworkCommandsMixin, WebCommandsMixin
from core.commands.utils import _parse_args, _split_global_options
from core.logger import PirateLogger
from core.menu_registry import MENU_TREE
from core.scope_manager import ScopeManager


class PirateShell(WebCommandsMixin, NetworkCommandsMixin, BaseCommandsMixin, cmd.Cmd):
    """Interactive command shell for The Pirates combining modular command mixins."""

    prompt = "pirates> "

    def __init__(self) -> None:
        super().__init__()
        self.target: str = ""
        self.scope = ScopeManager()
        self.advanced_mode: bool = False
        self._load_saved_target()
        self._last_ctrl_c: float = 0.0

    def _load_saved_target(self) -> None:
        """Muat target dari sessions/current_target.json jika ada."""
        target_file = Path("sessions/current_target.json")
        if target_file.exists():
            try:
                data = json.loads(target_file.read_text(encoding="utf-8"))
                self.target = data.get("target", "")
            except Exception:
                pass

    def _save_target(self) -> None:
        """Simpan target ke sessions/current_target.json."""
        target_file = Path("sessions/current_target.json")
        target_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            target_file.write_text(
                json.dumps({"target": self.target}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            pass

    def preloop(self) -> None:
        """Jalankan menu interaktif sebelum loop cmd jika bukan advanced mode."""
        if not self.advanced_mode:
            self.show_menu()

    def postcmd(self, stop: bool, line: str) -> bool:
        """Setelah perintah di advanced mode selesai, tanya user kembali ke Menu Utama."""
        if stop:
            return stop
        if not self.advanced_mode:
            return stop

        try:
            choice = questionary.confirm(
                "Kembali ke Menu Utama (Console Mode)?",
                default=True,
            ).ask()
            if choice:
                self.advanced_mode = False
                self.show_menu()
        except (KeyboardInterrupt, Exception):
            print()
        return stop

    def _handle_ctrl_c_exit(self) -> bool:
        """Tangani Ctrl+C bertingkat pada menu utama."""
        now = time.time()
        if now - self._last_ctrl_c < 2.0:
            print("\nSampai jumpa, Kapten!")
            return True
        else:
            self._last_ctrl_c = now
            print("\n[!] Press Ctrl+C again within 2 seconds to exit.")
            return False

    def show_menu(self) -> None:
        """Tampilkan menu interaktif berbasis MENU_TREE dengan navigasi rekursif."""
        while not self.advanced_mode:
            try:
                should_exit = self._display_menu_level(MENU_TREE, breadcrumbs=[])
                if should_exit or self.advanced_mode:
                    break
            except KeyboardInterrupt:
                print()
                if self._handle_ctrl_c_exit():
                    break
            except Exception as e:
                PirateLogger.bad(f"Terjadi kesalahan pada menu: {e}")
                break

    def _display_menu_level(self, current_node: dict, breadcrumbs: list[str]) -> bool:
        """Navigasi level menu secara rekursif.

        Args:
            current_node: Dictionary node kategori atau root MENU_TREE
            breadcrumbs: Hierarki navigasi saat ini (e.g. ['Network Tools', 'Port Scanners'])

        Returns:
            True jika user memilih Exit (keluar program), False jika kembali ke parent
        """
        is_root = len(breadcrumbs) == 0
        items = current_node.get("items", {}) if not is_root else current_node

        # Kategori placeholder / kosong (e.g. OSINT, Cracker, Listener)
        if not is_root and not items:
            cat_name = breadcrumbs[-1]
            PirateLogger.info(f"Kategori '{cat_name}' belum memiliki tool (Coming Soon).")
            return False

        while not self.advanced_mode:
            try:
                choices_map: dict[str, tuple[str, dict]] = {}
                display_choices: list[str] = []

                target_str = f"Target: {self.target or 'None'}"
                if is_root:
                    prompt_title = f"The Pirates Console ({target_str}) — Select Category:"
                else:
                    path_str = " > ".join(breadcrumbs)
                    prompt_title = f"{path_str} ({target_str}) — Select Option:"

                for name, data in items.items():
                    desc = data.get("desc", "")
                    label = f"{name} — {desc}" if desc else name
                    display_choices.append(label)
                    choices_map[label] = (name, data)

                if is_root:
                    display_choices.append("Advanced Mode")
                    display_choices.append("Exit")
                else:
                    display_choices.append("Back")

                selection = questionary.select(
                    prompt_title,
                    choices=display_choices,
                ).ask()

                if selection is None:
                    # User menekan Ctrl+C saat prompt aktif
                    if is_root:
                        if self._handle_ctrl_c_exit():
                            return True
                        continue
                    else:
                        # Kembali ke level sebelumnya
                        return False

                if is_root:
                    if selection == "Exit":
                        self.do_exit("")
                        return True
                    if selection == "Advanced Mode":
                        self.advanced_mode = True
                        PirateLogger.good("Entering Advanced Mode (Type 'help' for commands, or type 'menu' to return).")
                        return False

                if not is_root and selection == "Back":
                    return False

                selected_name, selected_data = choices_map[selection]

                # Jika item memiliki 'items', ini adalah sub-kategori
                if "items" in selected_data:
                    should_exit = self._display_menu_level(selected_data, [*breadcrumbs, selected_name])
                    if should_exit or self.advanced_mode:
                        return should_exit
                elif "handler" in selected_data:
                    # Leaf action: panggil handler method
                    handler_name = selected_data["handler"]
                    if hasattr(self, handler_name):
                        handler_func = getattr(self, handler_name)
                        handler_func("")
                    else:
                        PirateLogger.warn(f"Handler '{handler_name}' belum diimplementasikan.")

                    if self.advanced_mode:
                        return False

            except KeyboardInterrupt:
                print()
                if is_root:
                    if self._handle_ctrl_c_exit():
                        return True
                else:
                    return False
            except Exception as e:
                PirateLogger.bad(f"Terjadi kesalahan pada menu: {e}")
                return False

        return False
