"""RustScan wrapper for ultra-fast port scanning."""

import shutil
import subprocess
import sys
from dataclasses import dataclass

from core.logger import PirateLogger as Log


@dataclass
class RustScanResult:
    """Result of a RustScan scan."""
    target: str
    profile: str
    output: str
    returncode: int


RUSTSCAN_PROFILES = {
    "1": {
        "name": "Fast Scan (1-10000)",
        "description": "Fast scan of ports 1 to 10000",
        "args": ["-r", "1-10000"],
    },
    "2": {
        "name": "Full Scan (1-65535)",
        "description": "Comprehensive scan of all 65535 ports",
        "args": ["-r", "1-65535"],
    },
    "3": {
        "name": "Top Ports & Nmap Service Scan",
        "description": "Fast scan with Nmap service version detection (-sV)",
        "args": ["-r", "1-10000", "--", "-sV"],
    },
}


def check_rustscan() -> bool:
    """Check if rustscan is installed and available in PATH."""
    if shutil.which("rustscan") is not None:
        return True
    try:
        res = subprocess.run(
            ["rustscan", "--version"],
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


def print_rustscan_profiles() -> None:
    """Print available RustScan profiles in a clean table format."""
    Log.info("Available RustScan Profiles:")
    print(f"  {'ID':<5} {'Profile Name':<30} {'Description'}")
    print(f"  {'-'*5} {'-'*30} {'-'*40}")
    for pid, profile in RUSTSCAN_PROFILES.items():
        pname = profile.get("name", "")
        pdesc = profile.get("description", "")
        print(f"  {pid:<5} {pname:<30} {pdesc}")


def run_rustscan(target: str, profile_num: str, extra_args: list[str] | None = None) -> RustScanResult:
    """Run a RustScan scan against a target using a specified profile.

    Streams output live to the terminal.

    Args:
        target: Hostname or IP address to scan
        profile_num: ID of the profile (e.g. 1, 2, 3)
        extra_args: Additional command line arguments to append

    Returns:
        RustScanResult object containing output and return code
    """
    if not check_rustscan():
        Log.bad("Error: 'rustscan' binary not found in system PATH. Please install rustscan.")
        return RustScanResult(target=target, profile=profile_num, output="", returncode=127)

    profile_id = str(profile_num).strip()
    if profile_id not in RUSTSCAN_PROFILES:
        Log.bad(f"Invalid RustScan profile ID: {profile_id}. Available: {list(RUSTSCAN_PROFILES.keys())}")
        return RustScanResult(target=target, profile=profile_id, output="", returncode=1)

    profile = RUSTSCAN_PROFILES[profile_id]
    pname = profile.get("name", "")
    args_list = profile.get("args", []).copy()

    if extra_args:
        args_list.extend(extra_args)

    cmd = ["rustscan", "-a", target, *args_list]
    Log.info(f"Running RustScan Profile [{profile_id}] '{pname}' on target: {target}")
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
        Log.bad("Error: 'rustscan' binary not found in system PATH. Please install rustscan.")
        returncode = 127
    except KeyboardInterrupt:
        Log.warn("RustScan scan interrupted by user.")
        returncode = 130
    except Exception as e:
        Log.bad(f"Error executing rustscan: {e}")
        returncode = 1

    Log.separator()
    if returncode == 0:
        Log.good("RustScan completed successfully.")
    else:
        Log.warn(f"RustScan finished with return code {returncode}.")

    return RustScanResult(
        target=target,
        profile=pname,
        output="".join(output_lines),
        returncode=returncode,
    )
