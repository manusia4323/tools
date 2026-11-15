"""Base shell commands mixin (target, scope, reports, utilities, menu, exit)."""

import json
from pathlib import Path

import questionary

from core.commands.utils import _parse_args
from core.config import load_config
from core.logger import PirateLogger


class BaseCommandsMixin:
    """Mixin for base and utility shell commands."""

    def do_menu(self, arg: str = "") -> None:
        """Tampilkan menu interaktif utama.

        Penggunaan: menu
        """
        self.advanced_mode = False
        if hasattr(self, "show_menu"):
            self.show_menu()

    def do_console(self, arg: str = "") -> None:
        """Kembali ke Console Menu Utama.

        Penggunaan: console
        """
        self.advanced_mode = False
        if hasattr(self, "show_menu"):
            self.show_menu()

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
                        choices=["Set Target", "Show Target", "Clear Target", "Cancel"],
                    ).ask()
                    if action == "Set Target":
                        url_input = questionary.text("Enter target URL (e.g. http://example.com):").ask()
                        if url_input:
                            self.target = url_input.strip()
                            if hasattr(self, "_save_target"):
                                self._save_target()
                            PirateLogger.good(f"Target disetel: {self.target}")
                    elif action == "Show Target":
                        if not self.target:
                            PirateLogger.warn("Belum ada target yang diatur.")
                        else:
                            PirateLogger.info(f"Target: {self.target}")
                    elif action == "Clear Target":
                        self.target = ""
                        if hasattr(self, "_save_target"):
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
            if hasattr(self, "_save_target"):
                self._save_target()
            PirateLogger.good(f"Target disetel: {self.target}")
        elif sub == "show":
            if not self.target:
                PirateLogger.warn("Belum ada target yang diatur.")
            else:
                PirateLogger.info(f"Target: {self.target}")
        elif sub == "clear":
            self.target = ""
            if hasattr(self, "_save_target"):
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
                        choices=["Add Target to Scope", "List Scope", "Clear Scope", "Cancel"],
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

    def do_reports(self, arg: str) -> None:
        """List or show saved reports.

        Usage: reports list | show
        """
        config = load_config()
        reports_dir = Path(config.get("REPORT_DIR", "reports"))

        parts = arg.split(None, 1)
        if not parts:
            if not arg.strip():
                while True:
                    try:
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
                        choices = [*rep_choices, "Back to Menu"]

                        chosen_rep = questionary.select(
                            "Select report to view:",
                            choices=choices,
                        ).ask()

                        if chosen_rep is None or chosen_rep == "Back to Menu":
                            break

                        report_path = reports_dir / chosen_rep
                        if not report_path.exists():
                            PirateLogger.bad(f"Report not found: {chosen_rep}")
                            continue

                        if report_path.suffix == ".json":
                            try:
                                data = json.loads(report_path.read_text(encoding="utf-8"))
                                PirateLogger.info("Report Summary:")
                                print(f"  Target: {data.get('target', 'N/A')}")
                                findings = data.get("findings", [])
                                print(f"  Total: {len(findings)} findings")
                                links = sum(1 for f in findings if f.get("type") == "link")
                                forms = sum(1 for f in findings if f.get("type") == "form")
                                print(f"  Links: {links}")
                                print(f"  Forms: {forms}")
                            except Exception as e:
                                PirateLogger.bad(f"Error reading JSON report: {e}")
                        elif report_path.suffix == ".md":
                            try:
                                content = report_path.read_text(encoding="utf-8")
                                lines = content.splitlines()[:20]
                                PirateLogger.info(f"Report: {chosen_rep} (First 20 lines):")
                                for line in lines:
                                    print(line)
                            except Exception as e:
                                PirateLogger.bad(f"Error reading markdown report: {e}")
                        else:
                            PirateLogger.info(f"Report path: {report_path}")

                    except KeyboardInterrupt:
                        print()
                        break
                    except Exception as e:
                        PirateLogger.bad(f"Terjadi kesalahan saat melihat laporan: {e}")
                        break
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
                    findings = data.get("findings", [])
                    print(f"  Total: {len(findings)} findings")
                    links = sum(1 for f in findings if f.get("type") == "link")
                    forms = sum(1 for f in findings if f.get("type") == "form")
                    print(f"  Links: {links}")
                    print(f"  Forms: {forms}")
                elif report_path.suffix == ".md":
                    lines = report_path.read_text(encoding="utf-8").splitlines()[:20]
                    PirateLogger.info(f"Report: {filename} (First 20 lines):")
                    for line in lines:
                        print(line)
                else:
                    PirateLogger.info("Use 'cat' to view report.")
            except Exception as e:
                PirateLogger.bad(f"Error reading report: {e}")
        else:
            PirateLogger.warn(f"Subcommand reports tidak dikenal: {sub}")

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

    def do_exit(self, arg: str = "") -> bool:
        """Keluar dari shell interaktif."""
        print("Sampai jumpa, Kapten!")
        return True

    def do_EOF(self, arg: str = "") -> bool:
        """Keluar dengan Ctrl+D."""
        print("Sampai jumpa, Kapten!")
        return True
