"""Network tools shell commands mixin (nmap, rustscan, arpscan, netdiscover, whatweb)."""

import shlex
from urllib.parse import urlparse

import questionary

from core.commands.utils import _parse_args
from core.logger import PirateLogger


class NetworkCommandsMixin:
    """Mixin for network scanning and discovery commands."""

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
                    choices=["List Profiles", "Run Scan", "Cancel"],
                ).ask()
                if action == "List Profiles":
                    print_nmap_profiles()
                    return
                elif action == "Run Scan":
                    target_mode = questionary.select(
                        "Target Selection:",
                        choices=["Use current target (auto-parsed)", "Custom hostname/IP"],
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
                        "6: Stealth SYN Scan",
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

    def do_rustscan(self, arg: str) -> None:
        """Run RustScan fast port scan.

        Usage: rustscan [target] [profile_num] [extra_args...]
        """
        from modules.rustscan_wrapper import RUSTSCAN_PROFILES, print_rustscan_profiles, run_rustscan

        parts = shlex.split(arg) if arg.strip() else []

        if not parts:
            try:
                # 1. Check target
                target_mode = questionary.select(
                    "Target Selection for RustScan:",
                    choices=["Use current target (auto-parsed)", "Custom hostname/IP", "Cancel"],
                ).ask()
                if not target_mode or target_mode == "Cancel":
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

                # 2. Show profiles table
                print_rustscan_profiles()

                # 3. Ask profile number via questionary
                profile_choices = [
                    f"{pid}: {p.get('name', '')} — {p.get('description', '')}"
                    for pid, p in RUSTSCAN_PROFILES.items()
                ]
                profile_choices.append("Cancel")

                selected_prof = questionary.select(
                    "Select RustScan Profile:",
                    choices=profile_choices,
                ).ask()

                if not selected_prof or selected_prof == "Cancel":
                    return

                profile_num = selected_prof.split(":")[0].strip()

                # 4. Run rustscan
                run_rustscan(target_host, profile_num)
            except (KeyboardInterrupt, Exception) as e:
                if not isinstance(e, KeyboardInterrupt):
                    PirateLogger.bad(f"Error in RustScan: {e}")
                else:
                    print()
                return
        else:
            # Called with arguments: rustscan <target> [profile_num] [extra_args...]
            target_host = parts[0]
            if "://" in target_host:
                parsed = urlparse(target_host)
                target_host = parsed.hostname or target_host

            profile_num = parts[1] if len(parts) > 1 else "1"
            extra_args = parts[2:] if len(parts) > 2 else None
            run_rustscan(target_host, profile_num, extra_args)

    def do_arpscan(self, arg: str) -> None:
        """Run Arp-Scan on local network.

        Usage: arpscan [interface]
        """
        from modules.arpscan_wrapper import run_arpscan

        interface = arg.strip()
        if not interface:
            try:
                interface_input = questionary.text(
                    "Enter network interface (leave empty for default, e.g. eth0, wlan0):"
                ).ask()
                if interface_input is None:
                    return
                interface = interface_input.strip()
            except (KeyboardInterrupt, Exception) as e:
                if not isinstance(e, KeyboardInterrupt):
                    PirateLogger.bad(f"Error in Arp-Scan: {e}")
                else:
                    print()
                return

        run_arpscan(interface)

    def do_netdiscover(self, arg: str) -> None:
        """Run Netdiscover active/passive ARP recon.

        Usage: netdiscover [interface] [subnet]
        """
        from modules.netdiscover_wrapper import run_netdiscover

        parts = shlex.split(arg) if arg.strip() else []
        if not parts:
            try:
                interface_input = questionary.text(
                    "Enter network interface (leave empty for default, e.g. eth0, wlan0):"
                ).ask()
                if interface_input is None:
                    return
                interface = interface_input.strip()

                subnet_input = questionary.text(
                    "Enter target subnet (leave empty for auto, e.g. 192.168.1.0/24):"
                ).ask()
                if subnet_input is None:
                    return
                subnet = subnet_input.strip()
            except (KeyboardInterrupt, Exception) as e:
                if not isinstance(e, KeyboardInterrupt):
                    PirateLogger.bad(f"Error in Netdiscover: {e}")
                else:
                    print()
                return
        else:
            interface = parts[0].strip()
            subnet = parts[1].strip() if len(parts) > 1 else ""

        run_netdiscover(interface, subnet)

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

        from main import cmd_whatweb

        args = _parse_args("whatweb", f"-u {self.target} {arg}")
        if args is None:
            return
        cmd_whatweb(args)
