"""Self-installer for missing external tools (nmap, whatweb, rustscan, arp-scan, netdiscover)."""

import shutil
import subprocess
from core.logger import PirateLogger as Log

OS_MAP = {
    "Ubuntu/Debian (apt)": {
        "cmd": "sudo apt update && sudo apt install -y",
        "tools": {
            "nmap": "nmap",
            "whatweb": "whatweb",
            "rustscan": "rustscan",
            "arp-scan": "arp-scan",
            "netdiscover": "netdiscover",
        },
    },
    "Arch Linux (pacman)": {
        "cmd": "sudo pacman -S --noconfirm",
        "tools": {
            "nmap": "nmap",
            "whatweb": "whatweb",
            "rustscan": "rustscan",
            "arp-scan": "arp-scan",
            "netdiscover": "netdiscover",
        },
    },
    "Fedora/RHEL (dnf)": {
        "cmd": "sudo dnf install -y",
        "tools": {
            "nmap": "nmap",
            "whatweb": "whatweb",
            "rustscan": "rustscan",
            "arp-scan": "arp-scan",
            "netdiscover": "netdiscover",
        },
    },
}


def check_tool_installed(tool_name: str) -> bool:
    """Double verification to check if a tool is installed."""
    if shutil.which(tool_name) is not None:
        return True
    try:
        res = subprocess.run(
            [tool_name, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            return True
    except Exception:
        pass
    return False


def check_and_install_tools() -> None:
    """Check required external tools and offer interactive installation if missing."""
    tools = ["nmap", "whatweb", "rustscan", "arp-scan", "netdiscover"]
    for tool in tools:
        if check_tool_installed(tool):
            Log.good(f"Tool '{tool}' is installed.")
            continue

        Log.warn(f"Tool '{tool}' is not installed on this system.")
        try:
            import questionary
        except ImportError:
            Log.warn(f"Skipping interactive installer for '{tool}' (questionary not available).")
            continue

        try:
            install_confirm = questionary.confirm(
                f"Tool '{tool}' is not installed. Do you want to install it?",
                default=False
            ).ask()
        except (KeyboardInterrupt, Exception):
            print()
            Log.info("Installation prompt cancelled.")
            continue

        if not install_confirm:
            Log.info(f"Skipping installation of '{tool}'.")
            continue

        os_choices = [*list(OS_MAP.keys()), "Cancel"]
        try:
            os_choice = questionary.select(
                "Select your operating system / package manager:",
                choices=os_choices
            ).ask()
        except (KeyboardInterrupt, Exception):
            print()
            Log.info("OS selection cancelled.")
            continue

        if not os_choice or os_choice == "Cancel":
            Log.info("Installation cancelled.")
            continue

        os_config = OS_MAP.get(os_choice)
        if not os_config:
            continue

        pkg_name = os_config.get("tools", {}).get(tool)
        if not pkg_name:
            Log.bad(f"Tool {tool} is not available via package manager. Please install manually.")
            continue

        base_cmd = os_config.get("cmd", "")
        # Remove trailing '-y' or '--noconfirm' so user can answer y/n themselves
        tokens = base_cmd.split()
        cleaned_tokens = [t for t in tokens if t not in ("-y", "--noconfirm")]
        cmd = f"{' '.join(cleaned_tokens)} {pkg_name}"

        Log.info(f"Command to execute: {cmd}")
        try:
            exec_confirm = questionary.confirm(
                "Execute this command?",
                default=False
            ).ask()
        except (KeyboardInterrupt, Exception):
            print()
            Log.info("Command execution prompt cancelled.")
            continue

        if not exec_confirm:
            Log.info("Installation aborted by user.")
            continue

        Log.info(f"Running installation for {tool}...")
        try:
            result = subprocess.run(cmd, shell=True)
            if result.returncode == 0:
                Log.good(f"Successfully installed '{tool}'!")
            else:
                Log.bad(f"Installation failed with return code {result.returncode}. Returning to menu.")
        except Exception as e:
            Log.bad(f"Installation failed: {e}. Returning to menu.")
