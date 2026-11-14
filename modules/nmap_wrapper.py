"""Nmap wrapper for network and port scanning."""

import subprocess
import sys
from dataclasses import dataclass
from typing import Any

from core.logger import PirateLogger as Log
from core.models import Finding


@dataclass
class NmapResult:
    """Result of an Nmap scan."""
    target: str
    profile: str
    output: str
    returncode: int


# 6 Nmap profiles as requested
NMAP_PROFILES = {
    "1": {
        "name": "Quick Top 100 Ports",
        "description": "Fast scan of the top 100 common TCP ports",
        "args": ["-T4", "--top-ports", "100", "-v"],
    },
    "2": {
        "name": "Full TCP Port Scan",
        "description": "Comprehensive scan of all 65535 TCP ports",
        "args": ["-p-", "-T4", "-v"],
    },
    "3": {
        "name": "Service & Version Detection",
        "description": "Scan top ports and probe for service/version info (-sV)",
        "args": ["-sV", "--top-ports", "1000", "-T4"],
    },
    "4": {
        "Name": "OS Detection & Script Scan",
        "description": "Aggressive OS detection, version detection, script scanning, and traceroute (-A)",
        "args": ["-A", "-T4"],
    },
    "5": {
        "name": "Vuln Script Scan",
        "description": "Scan using vulnerability detection scripts (--script vuln)",
        "args": ["--script", "vuln", "-T4"],
    },
    "6": {
        "name": "Stealth SYN Scan",
        "description": "Half-open TCP SYN stealth scan (requires root/sudo)",
        "args": ["-sS", "-T4", "--top-ports", "100"],
    },
}


def check_nmap() -> bool:
    """Check if nmap is installed and available in PATH."""
    import shutil
    return shutil.which("nmap") is not None


def print_nmap_profiles() -> None:
    """Print available Nmap profiles in a clean table format."""
    Log.info("Available Nmap Profiles:")
    print(f"  {'ID':<5} {'Profile Name':<30} {'Description'}")
    print(f"  {'-'*5} {'-'*30} {'-'*40}")
    for pid, profile in NMAP_PROFILES.items():
        # Handle potential key case variations
        pname = profile.get("name") or profile.get("Name", "")
        pdesc = profile.get("description", "")
        print(f"  {pid:<5} {pname:<30} {pdesc}")


def run_nmap(target: str, profile_id: str, extra_args: list[str] | None = None) -> NmapResult:
    """Run an Nmap scan against a target using a specified profile.

    Streams output live to the terminal.

    Args:
        target: Hostname or IP address to scan
        profile_id: ID of the profile (1-6)
        extra_args: Additional command line arguments to append

    Returns:
        NmapResult object containing output and return code
    """
    if profile_id not in NMAP_PROFILES:
        Log.bad(f"Invalid Nmap profile ID: {profile_id}. Choose between 1 and 6.")
        return NmapResult(target=target, profile=profile_id, output="", returncode=1)

    profile = NMAP_PROFILES[profile_id]
    pname = profile.get("name") or profile.get("Name", "")
    args_list = profile.get("args", []).copy()

    if extra_args:
        args_list.extend(extra_args)

    cmd = ["nmap", *args_list, target]
    Log.info(f"Running Nmap Profile [{profile_id}] '{pname}' on target: {target}")
    Log.info(f"Command: {' '.join(cmd)}")
    Log.separator()

    output_lines: list[str] = []
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if process.stdout:
            for line in process.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                output_lines.append(line)

        process.wait()
        returncode = process.returncode
    except FileNotFoundError:
        Log.bad("Error: 'nmap' binary not found in system PATH. Please install nmap.")
        returncode = 127
    except Exception as e:
        Log.bad(f"Error executing nmap: {e}")
        returncode = 1

    Log.separator()
    if returncode == 0:
        Log.good("Nmap scan completed successfully.")
    else:
        Log.warn(f"Nmap scan finished with return code {returncode}.")

    return NmapResult(
        target=target,
        profile=pname,
        output="".join(output_lines),
        returncode=returncode,
    )
