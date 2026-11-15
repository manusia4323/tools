"""Arp-Scan wrapper for local network discovery."""

import shutil
import subprocess
from core.logger import PirateLogger as Log


def check_arpscan() -> bool:
    """Check if arp-scan is installed and available in PATH."""
    return shutil.which("arp-scan") is not None


def run_arpscan(interface: str = "") -> bool:
    """Run arp-scan against local network.

    Streams output live to the terminal.
    arp-scan requires root/sudo privileges.

    Args:
        interface: Network interface name (e.g. eth0, wlan0). If empty, uses default.

    Returns:
        True if successfully executed, False otherwise
    """
    if not check_arpscan():
        Log.bad("Error: 'arp-scan' binary not found in system PATH. Please install arp-scan.")
        return False

    cmd = ["sudo", "arp-scan"]
    if interface.strip():
        cmd.append(f"--interface={interface.strip()}")
    cmd.append("--localnet")

    Log.info(f"Running Arp-Scan on local network" + (f" (interface: {interface.strip()})" if interface.strip() else ""))
    Log.info(f"Command: {' '.join(cmd)}")
    Log.separator()

    try:
        # Use subprocess.run directly so user can interact with sudo password prompt via terminal
        result = subprocess.run(cmd)
        Log.separator()
        if result.returncode == 0:
            Log.good("Arp-Scan completed successfully.")
            return True
        else:
            Log.warn(f"Arp-Scan finished with return code {result.returncode}.")
            return False
    except KeyboardInterrupt:
        print()
        Log.warn("Arp-Scan interrupted by user.")
        return False
    except FileNotFoundError:
        Log.bad("Error: 'sudo' or 'arp-scan' binary not found.")
        return False
    except Exception as e:
        Log.bad(f"Error executing arp-scan: {e}")
        return False
