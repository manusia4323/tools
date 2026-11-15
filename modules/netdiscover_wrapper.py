"""Netdiscover wrapper for active and passive ARP reconnaissance."""

import shutil
import subprocess
from core.logger import PirateLogger as Log


def check_netdiscover() -> bool:
    """Check if netdiscover is installed and available in PATH."""
    return shutil.which("netdiscover") is not None


def run_netdiscover(interface: str = "", subnet: str = "") -> bool:
    """Run netdiscover against network.

    Streams output live to the terminal.
    netdiscover requires root/sudo privileges.

    Args:
        interface: Network interface name (e.g. eth0, wlan0).
        subnet: Target subnet (e.g. 192.168.1.0/24). If empty, auto-discovers.

    Returns:
        True if successfully executed, False otherwise
    """
    if not check_netdiscover():
        Log.bad("Error: 'netdiscover' binary not found in system PATH. Please install netdiscover.")
        return False

    cmd = ["sudo", "netdiscover"]
    if interface.strip():
        cmd.extend(["-i", interface.strip()])
    if subnet.strip():
        cmd.extend(["-r", subnet.strip()])

    Log.info(
        f"Running Netdiscover"
        + (f" on interface: {interface.strip()}" if interface.strip() else "")
        + (f" for subnet: {subnet.strip()}" if subnet.strip() else "")
    )
    Log.info(f"Command: {' '.join(cmd)}")
    Log.separator()

    try:
        # Use subprocess.run directly so user can interact with sudo password prompt and interactive TUI
        result = subprocess.run(cmd)
        Log.separator()
        if result.returncode == 0:
            Log.good("Netdiscover completed successfully.")
            return True
        else:
            Log.warn(f"Netdiscover finished with return code {result.returncode}.")
            return False
    except KeyboardInterrupt:
        print()
        Log.warn("Netdiscover interrupted by user.")
        return False
    except FileNotFoundError:
        Log.bad("Error: 'sudo' or 'netdiscover' binary not found.")
        return False
    except Exception as e:
        Log.bad(f"Error executing netdiscover: {e}")
        return False
