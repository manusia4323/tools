"""WhatWeb wrapper for deep technology fingerprinting."""

import shutil
import subprocess
import sys
from core.logger import PirateLogger as Log


def check_whatweb() -> bool:
    """Check if whatweb is installed and available in PATH."""
    return shutil.which("whatweb") is not None


def run_whatweb(target: str) -> bool:
    """Run whatweb scan against a target with aggressiveness level 3.

    Streams output live to the terminal.

    Args:
        target: Target URL or hostname

    Returns:
        True if successfully executed, False otherwise
    """
    if not check_whatweb():
        Log.bad("WhatWeb is not installed on this system. Please install it to use this feature.")
        return False

    cmd = ["whatweb", "-a", "3", target]
    Log.info(f"Running WhatWeb on target: {target}")
    Log.info(f"Command: {' '.join(cmd)}")
    Log.separator()

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

        process.wait()
        returncode = process.returncode
    except FileNotFoundError:
        Log.bad("Error: 'whatweb' binary not found in system PATH.")
        return False
    except KeyboardInterrupt:
        Log.warn("WhatWeb scan interrupted by user.")
        return False
    except Exception as e:
        Log.bad(f"Error executing whatweb: {e}")
        return False

    Log.separator()
    if returncode == 0:
        Log.good("WhatWeb scan completed successfully.")
        return True
    else:
        Log.warn(f"WhatWeb scan finished with return code {returncode}.")
        return False
