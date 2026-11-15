"""Self-installer for missing external tools (nmap, whatweb)."""

import shutil
import subprocess
from core.logger import PirateLogger as Log


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
    tools = ["nmap", "whatweb"]
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

        try:
            os_choice = questionary.select(
                "Select your operating system / package manager:",
                choices=[
                    "Ubuntu/Debian (apt)",
                    "Arch Linux (pacman)",
                    "Fedora (dnf)",
                    "Cancel"
                ]
            ).ask()
        except (KeyboardInterrupt, Exception):
            print()
            Log.info("OS selection cancelled.")
            continue

        if not os_choice or "Cancel" in os_choice:
            Log.info("Installation cancelled.")
            continue

        cmd = ""
        if "apt" in os_choice:
            cmd = f"sudo apt update && sudo apt install -y {tool}"
        elif "pacman" in os_choice:
            cmd = f"sudo pacman -S --noconfirm {tool}"
        elif "dnf" in os_choice:
            cmd = f"sudo dnf install -y {tool}"

        if not cmd:
            continue

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
