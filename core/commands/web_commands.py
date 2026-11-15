"""Web analysis shell commands mixin (recon, crawl, profile, autopilot)."""

import questionary

from core.commands.utils import _parse_args
from core.logger import PirateLogger


class WebCommandsMixin:
    """Mixin for web reconnaissance, crawling, profiling, and autopilot commands."""

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
                        if hasattr(self, "_save_target"):
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
        if hasattr(args, "report_path") and args.report_path:
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
                        if hasattr(self, "_save_target"):
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

        if not arg.strip():
            try:
                max_pages_input = questionary.text("Max pages (default 50):", default="50").ask()
                if max_pages_input is None:
                    return
                max_pages = max_pages_input.strip() or "50"

                depth_input = questionary.text("Depth (default 2):", default="2").ask()
                if depth_input is None:
                    return
                depth = depth_input.strip() or "2"

                delay_input = questionary.text("Delay in seconds (default 0.5):", default="0.5").ask()
                if delay_input is None:
                    return
                delay = delay_input.strip() or "0.5"

                ignore_robots = questionary.confirm("Ignore robots.txt?").ask()
                if ignore_robots is None:
                    return

                save_report = questionary.confirm("Save report to file?").ask()
                if save_report is None:
                    return

                output_format = None
                if save_report:
                    output_format = questionary.select("Format:", choices=["json", "md"]).ask()
                    if output_format is None:
                        return

                crawl_args = f"-u {self.target} --max-pages {max_pages} --depth {depth} --delay {delay}"
                if ignore_robots:
                    crawl_args += " --no-robots"
                if output_format:
                    crawl_args += f" --output {output_format}"

                args = _parse_args("crawl", crawl_args)
                if args is None:
                    return
                cmd_crawl(args)
                if hasattr(args, "report_path") and args.report_path:
                    PirateLogger.info(f"📁 Report saved to: {args.report_path}")
            except (KeyboardInterrupt, Exception) as e:
                if not isinstance(e, KeyboardInterrupt):
                    PirateLogger.bad(f"Terjadi kesalahan saat crawl: {e}")
                else:
                    print()
                return
        else:
            args = _parse_args("crawl", f"-u {self.target} {arg}")
            if args is None:
                return
            cmd_crawl(args)
            if hasattr(args, "report_path") and args.report_path:
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
                        if hasattr(self, "_save_target"):
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

        from main import run_profile

        args = _parse_args("profile", f"-u {self.target} {arg}")
        if args is None:
            return
        run_profile(args)
        if hasattr(args, "report_path") and args.report_path:
            PirateLogger.info(f"📁 Report saved to: {args.report_path}")

    def do_autopilot(self, arg: str = "") -> None:
        """Jalankan autopilot recon, profiling, dan crawling otomatis terhadap target.

        Penggunaan: autopilot
        """
        if not self.target:
            PirateLogger.warn("Target belum diatur. Gunakan 'target set <URL>' terlebih dahulu.")
            try:
                set_now = questionary.confirm("Do you want to set a target now?", default=True).ask()
                if set_now:
                    url_input = questionary.text("Enter target URL:").ask()
                    if url_input:
                        self.target = url_input.strip()
                        if hasattr(self, "_save_target"):
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

        PirateLogger.info(f"Starting Autopilot scan on {self.target}...")
        PirateLogger.info("[1/3] Running Recon...")
        self.do_recon("")
        PirateLogger.info("[2/3] Running Web Profiler...")
        self.do_profile("")
        PirateLogger.info("[3/3] Running Crawler...")
        self.do_crawl("")
        PirateLogger.good("Autopilot sequence completed.")
