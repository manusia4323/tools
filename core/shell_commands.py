"""Antarmuka shell interaktif untuk The Pirates."""

import cmd
import json
import shlex
import time
from pathlib import Path
from urllib.parse import urlparse

import questionary

from core.logger import PirateLogger
from core.menu_registry import MENU_STRUCTURE
from core.scope_manager import ScopeManager


# Opsi global yang di main.py harus berada SEBELUM subcommand.
_GLOBAL_OPTIONS_WITH_VALUE = ("--output", "--out-dir")


def _split_global_options(tokens: list[str]) -> tuple[list[str], list[str]]:
    """Pisahkan opsi global (--output, --out-dir) dari token lainnya."""
    globals_: list[str] = []
    rest: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        matched = False
        for option in _GLOBAL_OPTIONS_WITH_VALUE:
            if token == option and index + 1 < len(tokens):
                globals_.extend([token, tokens[index + 1]])
                index += 2
                matched = True
                break
            if token.startswith(f"{option}="):
                globals_.append(token)
                index += 1
                matched = True
                break
        if not matched:
            rest.append(token)
            index += 1
    return globals_, rest


def _parse_args(command_name: str, arg_string: str):
    """Parse argumen CLI menggunakan build_parser() dari main.py."""
    from main import build_parser

    parser = build_parser()
    global_tokens, rest = _split_global_options(shlex.split(arg_string))
    argv = [*global_tokens, command_name, *rest]
    try:
        return parser.parse_args(argv)
    except SystemExit:
        PirateLogger.warn(f"Argumen tidak valid untuk '{command_name}'.")
        return None


class PirateShell(cmd.Cmd):
    """Shell interaktif berbasis cmd.Cmd untuk alat The Pirates."""

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
                encoding="utf-8"
            )
        except Exception:
            pass

    def preloop(self) -> None:
        """Jalankan menu interaktif sebelum loop cmd jika bukan advanced mode."""
        if not self.advanced_mode:
            self.do_menu()

    def postcmd(self, stop: bool, line: str) -> bool:
        """Setelah perintah di advanced mode selesai, tanya user kembali ke Menu Utama."""
        if stop:
            return stop
        if not self.advanced_mode:
            return stop

        try:
            choice = questionary.confirm(
                "Kembali ke Menu Utama (Console Mode)?",
                default=True
            ).ask()
            if choice:
                self.advanced_mode = False
                self.do_menu()
        except (KeyboardInterrupt, Exception):
            print()
        return stop

    def do_menu(self) -> None:
        """Tampilkan menu interaktif berbasis kategori."""
        while not self.advanced_mode:
            try:
                categories = list(MENU_STRUCTURE.keys())
                choices = [*categories, "Advanced Mode", "Exit"]

                cat_sel = questionary.select(
                    f"The Pirates Console (Target: {self.target or 'None'}) — Select Category:",
                    choices=choices
                ).ask()

                if cat_sel is None:
                    # User pressed Ctrl+C or exited prompt
                    if self._handle_ctrl_c_exit():
                        break
                    continue

                if cat_sel == "Exit":
                    self.do_exit("")
                    break

                if cat_sel == "Advanced Mode":
                    self.advanced_mode = True
                    PirateLogger.good("Entering Advanced Mode (Type 'help' for commands, or type 'menu' to return).")
                    break

                # Submenu items
                sub_items = MENU_STRUCTURE[cat_sel]
                sub_choices = [f"{item['name']} — {item['desc']}" for item in sub_items]
                sub_choices.append("Back")

                sub_sel = questionary.select(
                    f"Category: {cat_sel}",
                    choices=sub_choices
                ).ask()

                if sub_sel is None or sub_sel == "Back":
                    continue

                # Find selected item handler
                selected_name = sub_sel.split(" — ")[0]
                handler_name = ""
                for item in sub_items:
                    if item["name"] == selected_name:
                        handler_name = item["handler"]
                        break

                if handler_name and hasattr(self, handler_name):
                    handler_func = getattr(self, handler_name)
                    handler_func("")

            except KeyboardInterrupt:
                print()
                if self._handle_ctrl_c_exit():
                    break
            except Exception as e:
                PirateLogger.bad(f"Terjadi kesalahan pada menu: {e}")

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

    def do_console(self, arg: str) -> None:
        """Kembali ke Console Menu Utama.

        Penggunaan: console
        """
        self.advanced_mode = False
        self.do_menu()

    def do_target(self, arg: str) -> None:
        """Atur atau lihat target URL.

        Penggunaan: target set <URL> | show | clear
        """
        parts = arg.split(None, 1)
        if not parts:
            if not arg.strip():
                # Wizard mode if called without args
                try:
                    action = questionary.select(
                        "Target Management:",
                        choices=["Set Target", "Show Target", "Clear Target", "Cancel"]
                    ).ask()
                    if action == "Set Target":
                        url_input = questionary.text("Enter target URL (e.g. http://example.com):").ask()
                        if url_input:
                            self.target = url_input.strip()
                            self._save_target()
                            PirateLogger.good(f"Target disetel: {self.target}")
                    elif action == "Show Target":
                        if not self.target:
                            PirateLogger.warn("Belum ada target yang diatur.")
                        else:
                            PirateLogger.info(f"Target: {self.target}")
                    elif action == "Clear Target":
                        self.target = ""
                        self._save_target()
                        PirateLogger.info("Target dibersihkan.")
                except (KeyboardInterrupt, Exception):
                    print()
                return

            PirateLogger.warn("Gunakan: target set <URL> | show | clear")
            return

        sub = parts[0].lower()

        if sub == "set":
            if len(parts) < 2:
                PirateLogger.warn("Gunakan: target set <URL>")
                return
            self.target = parts[1].strip()
            self._save_target()
            PirateLogger.good(f"Target disetel: {self.target}")
        elif sub == "show":
            if not self.target:
                PirateLogger.warn("Belum ada target yang diatur.")
            else:
                PirateLogger.info(f"Target: {self.target}")
        elif sub == "clear":
            self.target = ""
            self._save_target()
            PirateLogger.info("Target dibersihkan.")
        else:
            PirateLogger.warn(f"Subcommand target tidak dikenal: {sub}")

    def do_scope(self, arg: str) -> None:
        """Kelola scope whitelist.

        Penggunaan: scope add <URL> | list | clear
        """
        parts = arg.split(None, 1)
        if not parts:
            if not arg.strip():
                try:
                    action = questionary.select(
                        "Scope Management:",
                        choices=["Add Target to Scope", "List Scope", "Clear Scope", "Cancel"]
                    ).ask()
                    if action == "Add Target to Scope":
                        url_to_add = self.target or questionary.text("Enter URL to add to scope:").ask()
                        if url_to_add:
                            if self.scope.add(url_to_add.strip()):
                                PirateLogger.good(f"Added to scope: {url_to_add.strip()}")
                            else:
                                PirateLogger.info(f"Already in scope: {url_to_add.strip()}")
                    elif action == "List Scope":
                        urls = self.scope.list()
                        if not urls:
                            PirateLogger.info("Scope is empty.")
                        else:
                            PirateLogger.info("Allowed URLs:")
                            for u in urls:
                                print(f"  - {u}")
                    elif action == "Clear Scope":
                        self.scope.clear()
                        PirateLogger.good("Scope cleared.")
                except (KeyboardInterrupt, Exception):
                    print()
                return

            PirateLogger.warn("Gunakan: scope add <URL> | list | clear")
            return

        sub = parts[0].lower()

        if sub == "add":
            if len(parts) < 2:
                PirateLogger.warn("Gunakan: scope add <URL>")
                return
            url = parts[1].strip()
            if self.scope.add(url):
                PirateLogger.good(f"Added to scope: {url}")
            else:
                PirateLogger.info(f"Already in scope: {url}")
        elif sub == "list":
            urls = self.scope.list()
            if not urls:
                PirateLogger.info("Scope is empty.")
            else:
                PirateLogger.info("Allowed URLs:")
                for u in urls:
                    print(f"  - {u}")
        elif sub == "clear":
            self.scope.clear()
            PirateLogger.good("Scope cleared.")
        else:
            PirateLogger.warn(f"Subcommand scope tidak dikenal: {sub}")

    def do_recon(self, arg: str) -> None:
        """Jalankan recon terhadap target.

        Penggunaan: recon [--output json|md] [--out-dir DIR] [--no-save]
        """
        if not self.target:
            PirateLogger.warn("Target belum diatur. Gunakan 'target set <URL>' terlebih dahulu.")
            try:
                set_now = questionary.confirm("Do you want to set a target now?", default=True).ask()
                if set_now:
                    url_input = questionary.text("Enter target URL:").ask()
                    if url_input:
                        self.target = url_input.strip()
                        self._save_target()
                    else:
                        return
                else:
                    return
            except (KeyboardInterrupt, Exception):
                print()
                return

        if not self.scope.is_allowed(self.target):
            PirateLogger.bad(f"Target not in scope. Add it with: scope add {self.target}")
            try:
                add_now = questionary.confirm("Do you want to add this target to scope now?", default=True).ask()
                if add_now:
                    self.scope.add(self.target)
                    PirateLogger.good(f"Added to scope: {self.target}")
                else:
                    return
            except (KeyboardInterrupt, Exception):
                print()
                return

        from main import run_recon

        full_arg = f"-u {self.target} {arg}" if not arg.strip() else f"-u {self.target} {arg}"
        args = _parse_args("recon", full_arg)
        if args is None:
            return
        run_recon(args)
        if hasattr(args, 'report_path') and args.report_path:
            PirateLogger.info(f"📁 Report saved to: {args.report_path}")

    def do_crawl(self, arg: str) -> None:
        """Jalankan crawl terhadap target.

        Penggunaan: crawl [--depth N] [--max-pages N] [--delay N]
                           [--no-robots] [--output json|md]
        """
        if not self.target:
            PirateLogger.warn("Target belum diatur. Gunakan 'target set <URL>' terlebih dahulu.")
            try:
                set_now = questionary.confirm("Do you want to set a target now?", default=True).ask()
                if set_now:
                    url_input = questionary.text("Enter target URL:").ask()
                    if url_input:
                        self.target = url_input.strip()
                        self._save_target()
                    else:
                        return
                else:
                    return
            except (KeyboardInterrupt, Exception):
                print()
                return

        if not self.scope.is_allowed(self.target):
            PirateLogger.bad(f"Target not in scope. Add it with: scope add {self.target}")
            try:
                add_now = questionary.confirm("Do you want to add this target to scope now?", default=True).ask()
                if add_now:
                    self.scope.add(self.target)
                    PirateLogger.good(f"Added to scope: {self.target}")
                else:
                    return
            except (KeyboardInterrupt, Exception):
                print()
                return

        from main import cmd_crawl

        args = _parse_args("crawl", f"-u {self.target} {arg}")
        if args is None:
            return
        cmd_crawl(args)
        if hasattr(args, 'report_path') and args.report_path:
            PirateLogger.info(f"📁 Report saved to: {args.report_path}")

    def do_profile(self, arg: str) -> None:
        """Run security profiling against target.

        Usage: profile [--output json|md] [--out-dir DIR] [--no-save]
        """
        if not self.target:
            PirateLogger.warn("Target belum diatur. Gunakan 'target set <URL>' terlebih dahulu.")
            try:
                set_now = questionary.confirm("Do you want to set a target now?", default=True).ask()
                if set_now:
                    url_input = questionary.text("Enter target URL:").ask()
                    if url_input:
                        self.target = url_input.strip()
                        self._save_target()
                    else:
                        return
                else:
                    return
            except (KeyboardInterrupt, Exception):
                print()
                return

        if not self.scope.is_allowed(self.target):
            PirateLogger.bad(f"Target not in scope. Add it with: scope add {self.target}")
            try:
                add_now = questionary.confirm("Do you want to add this target to scope now?", default=True).ask()
                if add_now:
                    self.scope.add(self.target)
                    PirateLogger.good(f"Added to scope: {self.target}")
                else:
                    return
            except (KeyboardInterrupt, Exception):
                print()
                return

        from main import cmd_profile_main

        args = _parse_args("profile", f"-u {self.target} {arg}")
        if args is None:
            return
        cmd_profile_main(args)
        if hasattr(args, 'report_path') and args.report_path:
            PirateLogger.info(f"📁 Report saved to: {args.report_path}")

    def do_nmap(self, arg: str) -> None:
        """Run nmap port scans.

        Usage: nmap list | use -p <profile_id> -t <target> [extra_args...]
        """
        from modules.nmap_wrapper import print_nmap_profiles, run_nmap

        # If called interactively without arguments
        if not arg.strip():
            try:
                action = questionary.select(
                    "Nmap Port Scanner:",
                    choices=["List Profiles", "Run Scan", "Cancel"]
                ).ask()
                if action == "List Profiles":
                    print_nmap_profiles()
                    return
                elif action == "Run Scan":
                    target_mode = questionary.select(
                        "Target Selection:",
                        choices=["Use current target (auto-parsed)", "Custom hostname/IP"]
                    ).ask()
                    if target_mode is None or target_mode == "Cancel":
                        return

                    target_host = ""
                    if "current target" in target_mode:
                        if not self.target:
                            PirateLogger.warn("No current target set. Please enter custom hostname/IP.")
                            target_host = questionary.text("Enter target hostname or IP:").ask()
                        else:
                            parsed = urlparse(self.target)
                            target_host = parsed.hostname or self.target
                            PirateLogger.info(f"Using parsed target host: {target_host}")
                    else:
                        raw_input_target = questionary.text("Enter target (URL or IP/hostname):").ask()
                        if not raw_input_target:
                            return
                        if "://" in raw_input_target:
                            parsed = urlparse(raw_input_target)
                            target_host = parsed.hostname or raw_input_target
                        else:
                            target_host = raw_input_target.strip()

                    if not target_host:
                        return

                    profile_choices = [
                        "1: Quick Top 100 Ports",
                        "2: Full TCP Port Scan",
                        "3: Service & Version Detection",
                        "4: OS Detection & Script Scan",
                        "5: Vuln Script Scan",
                        "6: Stealth SYN Scan"
                    ]
                    prof_sel = questionary.select("Select Nmap Profile:", choices=profile_choices).ask()
                    if not prof_sel:
                        return
                    profile_id = prof_sel.split(":")[0].strip()

                    run_nmap(target_host, profile_id)
                    return
                else:
                    return
            except (KeyboardInterrupt, Exception):
                print()
                return

        args = _parse_args("nmap", arg)
        if args is None:
            return
        if args.nmap_command == "list":
            print_nmap_profiles()
        elif args.nmap_command == "use":
            if not args.profile or not args.target:
                PirateLogger.warn("Usage: nmap use -p <profile_id> -t <target>")
                return
            target_host = args.target
            if "://" in target_host:
                parsed = urlparse(target_host)
                target_host = parsed.hostname or target_host
            run_nmap(target_host, args.profile, args.extra_args)

    def do_whatweb(self, arg: str) -> None:
        """Jalankan WhatWeb terhadap target.

        Penggunaan: whatweb
        """
        if not self.target:
            PirateLogger.warn("Target belum diatur. Gunakan 'target set <URL>' terlebih dahulu.")
            try:
                set_now = questionary.confirm("Do you want to set a target now?", default=True).ask()
                if set_now:
                    url_input = questionary.text("Enter target URL:").ask()
                    if url_input:
                        self.target = url_input.strip()
                        self._save_target()
                    else:
                        return
                else:
                    return
            except (KeyboardInterrupt, Exception):
                print()
                return

        if not self.scope.is_allowed(self.target):
            PirateLogger.bad(f"Target not in scope. Add it with: scope add {self.target}")
            try:
                add_now = questionary.confirm("Do you want to add this target to scope now?", default=True).ask()
                if add_now:
                    self.scope.add(self.target)
                    PirateLogger.good(f"Added to scope: {self.target}")
                else:
                    return
            except (KeyboardInterrupt, Exception):
                print()
                return

        from main import cmd_whatweb

        args = _parse_args("whatweb", f"-u {self.target} {arg}")
        if args is None:
            return
        cmd_whatweb(args)

    def do_sessions(self, arg: str) -> None:
        """Kelola sesi cookie tersimpan.

        Penggunaan: sessions list | info -H <host> | delete -H <host>
        """
        from main import run_sessions

        args = _parse_args("sessions", arg)
        if args is None:
            return
        run_sessions(args)

    def do_wordlists(self, arg: str) -> None:
        """Kelola wordlist lokal.

        Penggunaan: wordlists list | show -n <name> | find -n <name>
        """
        from main import run_wordlists

        args = _parse_args("wordlists", arg)
        if args is None:
            return
        run_wordlists(args)

    def do_cookies(self, arg: str) -> None:
        """Tampilkan cookie tersimpan untuk host.

        Penggunaan: cookies -H <host>
        """
        from main import run_cookies

        args = _parse_args("cookies", arg)
        if args is None:
            return
        run_cookies(args.host)

    def do_reports(self, arg: str) -> None:
        """List or show saved reports.

        Usage: reports list | show
        """
        from core.config import load_config

        config = load_config()
        reports_dir = Path(config.get("REPORT_DIR", "reports"))

        parts = arg.split(None, 1)
        if not parts:
            if not arg.strip():
                try:
                    action = questionary.select(
                        "Reports Management:",
                        choices=["List Reports", "Show Report", "Cancel"]
                    ).ask()
                    if action == "List Reports":
                        if not reports_dir.exists():
                            PirateLogger.info("No reports directory found.")
                            return
                        reports = []
                        for ext in ("*.json", "*.md"):
                            reports.extend(reports_dir.glob(ext))
                        if not reports:
                            PirateLogger.info("No reports found.")
                        else:
                            PirateLogger.info("Available reports:")
                            for r in sorted(reports):
                                print(f"  - {r.name}")
                    elif action == "Show Report":
                        if not reports_dir.exists():
                            PirateLogger.info("No reports directory found.")
                            return
                        reports = []
                        for ext in ("*.json", "*.md"):
                            reports.extend(reports_dir.glob(ext))
                        if not reports:
                            PirateLogger.info("No reports found.")
                            return
                        rep_choices = [r.name for r in sorted(reports)]
                        chosen_rep = questionary.select("Select report to view:", choices=rep_choices).ask()
                        if chosen_rep:
                            report_path = reports_dir / chosen_rep
                            if report_path.suffix == ".json":
                                data = json.loads(report_path.read_text(encoding="utf-8"))
                                PirateLogger.info("Report Summary:")
                                print(f"  Target: {data.get('target', 'N/A')}")
                                findings = data.get('findings', [])
                                print(f"  Total: {len(findings)} findings")
                                links = sum(1 for f in findings if f.get('type') == 'link')
                                forms = sum(1 for f in findings if f.get('type') == 'form')
                                print(f"  Links: {links}")
                                print(f"  Forms: {forms}")
                            else:
                                PirateLogger.info(f"Report path: {report_path}")
                except (KeyboardInterrupt, Exception):
                    print()
                return

            PirateLogger.warn("Usage: reports list | show")
            return

        sub = parts[0].lower()

        if sub == "list":
            if not reports_dir.exists():
                PirateLogger.info("No reports directory found.")
                return
            reports = []
            for ext in ("*.json", "*.md"):
                reports.extend(reports_dir.glob(ext))
            if not reports:
                PirateLogger.info("No reports found.")
            else:
                PirateLogger.info("Available reports:")
                for r in sorted(reports):
                    print(f"  - {r.name}")
        elif sub == "show":
            if len(parts) < 2:
                PirateLogger.warn("Usage: reports show <filename>")
                return
            filename = parts[1].strip()
            report_path = reports_dir / filename
            if not report_path.exists():
                PirateLogger.bad(f"Report not found: {filename}")
                return
            try:
                if report_path.suffix == ".json":
                    data = json.loads(report_path.read_text(encoding="utf-8"))
                    PirateLogger.info("Report Summary:")
                    print(f"  Target: {data.get('target', 'N/A')}")
                    findings = data.get('findings', [])
                    print(f"  Total: {len(findings)} findings")
                    links = sum(1 for f in findings if f.get('type') == 'link')
                    forms = sum(1 for f in findings if f.get('type') == 'form')
                    print(f"  Links: {links}")
                    print(f"  Forms: {forms}")
                else:
                    PirateLogger.info("Use 'cat' to view markdown reports.")
            except Exception as e:
                PirateLogger.bad(f"Error reading report: {e}")
        else:
            PirateLogger.warn(f"Subcommand reports tidak dikenal: {sub}")

    def do_exit(self, arg: str) -> bool:
        """Keluar dari shell interaktif."""
        print("Sampai jumpa, Kapten!")
        return True

    def do_EOF(self, arg: str) -> bool:
        """Keluar dengan Ctrl+D."""
        print("Sampai jumpa, Kapten!")
        return True
