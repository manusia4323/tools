"""Self-installer for external tools with multi-method installation support."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import questionary

from core.logger import PirateLogger as Log
from core.tool_registry import TOOL_REGISTRY


def detect_os() -> str:
    """Detect the operating system / package manager.

    Returns:
        str: "apt", "pacman", "dnf", or "unknown"
    """
    try:
        import distro
        os_id = distro.id().lower()
        if os_id in ("ubuntu", "debian"):
            return "apt"
        elif os_id in ("arch", "manjaro"):
            return "pacman"
        elif os_id in ("fedora", "rhel", "centos"):
            return "dnf"
    except ImportError:
        pass

    # Fallback: check for package manager binaries
    if shutil.which("apt") is not None:
        return "apt"
    elif shutil.which("pacman") is not None:
        return "pacman"
    elif shutil.which("dnf") is not None:
        return "dnf"

    return "unknown"


def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed via shutil.which or --version check.

    Args:
        tool_name: Name of the tool binary to check

    Returns:
        bool: True if tool is found, False otherwise
    """
    if shutil.which(tool_name) is not None:
        return True
    try:
        result = subprocess.run(
            [tool_name, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True
    except Exception:
        pass
    return False


def check_and_install_tools() -> None:
    """Check all tools in TOOL_REGISTRY and offer interactive installation."""
    detected_os = detect_os()

    if detected_os == "unknown":
        Log.warn("Could not detect OS/package manager. Skipping auto-install.")
        return

    Log.good(f"Detected OS: {detected_os}")

    for tool_name, tool_info in TOOL_REGISTRY.items():
        # Determine the binary name (usually same as tool_name)
        binary_name = tool_info.get("binary_name", tool_name)

        # Check if already installed
        if check_tool_installed(binary_name):
            Log.good(f"✓ '{tool_name}' is installed.")
            continue

        Log.warn(f"✗ '{tool_name}' is not installed.")

        # Determine install command based on OS
        install_cmd = None
        install_method = None
        install_methods = tool_info.get("install", {})

        # Priority: OS-specific, then pip, then go, then cargo, then git, then aur
        if detected_os in install_methods and install_methods[detected_os]:
            install_cmd = install_methods[detected_os]
            install_method = detected_os
        elif "pip" in install_methods and install_methods["pip"]:
            install_cmd = install_methods["pip"]
            install_method = "pip"
        elif "go" in install_methods and install_methods["go"]:
            if tool_info.get("requires_go", False):
                if shutil.which("go") is None:
                    Log.warn(f"'{tool_name}' requires Go. Install Go first. Skipping.")
                    continue
            install_cmd = install_methods["go"]
            install_method = "go"
        elif "cargo" in install_methods and install_methods["cargo"]:
            if shutil.which("cargo") is None:
                Log.warn(f"'{tool_name}' requires Cargo. Install Rust first. Skipping.")
                continue
            install_cmd = install_methods["cargo"]
            install_method = "cargo"
        elif "aur" in install_methods and install_methods["aur"]:
            if detected_os == "pacman":
                if shutil.which("yay") is None and shutil.which("paru") is None:
                    Log.warn(f"'{tool_name}' requires AUR. Install yay/paru first. Skipping.")
                    continue
                # Use yay or paru
                aur_helper = "yay" if shutil.which("yay") else "paru"
                install_cmd = install_methods["aur"].replace("yay", aur_helper)
                install_method = "aur"
            else:
                Log.warn(f"'{tool_name}' only available on Arch AUR. Skipping.")
                continue
        elif "gem" in install_methods and install_methods["gem"]:
            if shutil.which("gem") is None:
                Log.warn(f"'{tool_name}' requires Ruby gems. Install Ruby first. Skipping.")
                continue
            install_cmd = install_methods["gem"]
            install_method = "gem"
        elif "git" in install_methods and install_methods["git"]:
            install_cmd = install_methods["git"]
            install_method = "git"

        if not install_cmd:
            Log.warn(f"No installation method available for '{tool_name}' on {detected_os}. Skipping.")
            continue

        # Ask user for confirmation
        Log.info(f"Installation method: {install_method}")
        Log.info(f"Command: {install_cmd}")
        try:
            confirm = questionary.confirm(
                f"Install '{tool_name}'?",
                default=False
            ).ask()
        except (KeyboardInterrupt, Exception):
            print()
            Log.info(f"Skipping '{tool_name}'.")
            continue

        if not confirm:
            Log.info(f"Skipping '{tool_name}'.")
            continue

        # Execute installation
        Log.info(f"Installing '{tool_name}'...")
        try:
            result = subprocess.run(
                install_cmd,
                shell=True,
                timeout=300,
            )
            if result.returncode == 0:
                Log.good(f"✓ Successfully installed '{tool_name}'.")
            else:
                Log.bad(f"✗ Installation of '{tool_name}' failed with return code {result.returncode}.")
        except subprocess.TimeoutExpired:
            Log.bad(f"✗ Installation of '{tool_name}' timed out.")
        except Exception as e:
            Log.bad(f"✗ Error installing '{tool_name}': {e}")


def check_wpscan_token() -> str | None:
    """Check or prompt for WPScan API token.

    Returns:
        str: API token if found/entered, None if skipped
    """
    token_file = Path("sessions/wpscan_token.txt")
    token_file.parent.mkdir(parents=True, exist_ok=True)

    # Check if token already saved
    if token_file.exists():
        try:
            token = token_file.read_text(encoding="utf-8").strip()
            if token:
                Log.good("WPScan token loaded from sessions/wpscan_token.txt")
                return token
        except Exception:
            pass

    # Prompt user
    Log.info("WPScan API Token is needed for certain features.")
    try:
        token = input("Enter WPScan API Token (leave empty to skip): ").strip()
    except KeyboardInterrupt:
        print()
        return None

    if token:
        try:
            token_file.write_text(token, encoding="utf-8")
            Log.good("WPScan token saved to sessions/wpscan_token.txt")
            return token
        except Exception as e:
            Log.bad(f"Error saving WPScan token: {e}")
            return token
    else:
        # Create empty file to avoid re-prompting
        try:
            token_file.write_text("", encoding="utf-8")
        except Exception:
            pass
        Log.info("WPScan token skipped.")
        return None


def get_wpscan_token() -> str | None:
    """Retrieve WPScan token if available.

    Returns:
        str: API token if exists, None otherwise
    """
    token_file = Path("sessions/wpscan_token.txt")
    if token_file.exists():
        try:
            token = token_file.read_text(encoding="utf-8").strip()
            return token if token else None
        except Exception:
            pass
    return None
