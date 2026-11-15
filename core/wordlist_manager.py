"""Wordlist management for password cracking and fuzzing."""

import json
import os
import subprocess
from pathlib import Path

import questionary

from core.logger import PirateLogger as Log


def ensure_wordlist() -> str:
    """Ensure a wordlist is available, prompting user if needed.

    Priority:
    1. /usr/share/wordlists/rockyou.txt
    2. /usr/share/wordlists/rockyou.txt.gz (decompress if needed)
    3. User selection menu (download RockYou, clone SecLists, custom path)

    Returns:
        str: Path to wordlist directory or file

    Raises:
        Exception: If user cancels or no wordlist available
    """
    config_file = Path("sessions/wordlist_config.json")
    config_file.parent.mkdir(parents=True, exist_ok=True)

    # Priority 1: /usr/share/wordlists/rockyou.txt
    if os.path.exists("/usr/share/wordlists/rockyou.txt"):
        Log.good("✓ Found RockYou wordlist at /usr/share/wordlists/rockyou.txt")
        config = {"wordlist_path": "/usr/share/wordlists/rockyou.txt"}
        try:
            config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
        except Exception:
            pass
        return "/usr/share/wordlists/rockyou.txt"

    # Priority 2: /usr/share/wordlists/rockyou.txt.gz (decompress)
    if os.path.exists("/usr/share/wordlists/rockyou.txt.gz"):
        Log.info("Found compressed RockYou at /usr/share/wordlists/rockyou.txt.gz")
        output_path = Path("sessions/wordlists/rockyou.txt")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            decompress = questionary.confirm(
                "Decompress rockyou.txt.gz to sessions/wordlists/? (This may take a moment)",
                default=True
            ).ask()
        except (KeyboardInterrupt, Exception):
            print()
            decompress = False

        if decompress:
            Log.info("Decompressing rockyou.txt.gz...")
            try:
                subprocess.run(
                    f"gunzip -c /usr/share/wordlists/rockyou.txt.gz > {output_path}",
                    shell=True,
                    timeout=600,
                    check=True,
                )
                Log.good(f"✓ Decompressed to {output_path}")
                config = {"wordlist_path": str(output_path)}
                config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
                return str(output_path)
            except Exception as e:
                Log.bad(f"Error decompressing: {e}")

    # Priority 3: User selection menu
    Log.info("RockYou wordlist not found on system. Showing options...")

    choices = [
        "Download RockYou (134 MB)",
        "Clone SecLists (~2 GB)",
        "Use custom path",
        "Cancel",
    ]

    try:
        selection = questionary.select(
            "Choose wordlist source:",
            choices=choices
        ).ask()
    except (KeyboardInterrupt, Exception):
        print()
        raise Exception("Wordlist selection cancelled by user.")

    if selection == "Download RockYou (134 MB)":
        return _download_rockyou()

    elif selection == "Clone SecLists (~2 GB)":
        return _clone_seclists()

    elif selection == "Use custom path":
        return _custom_wordlist_path()

    else:
        raise Exception("Wordlist selection cancelled.")


def _download_rockyou() -> str:
    """Download RockYou wordlist from GitHub.

    Returns:
        str: Path to downloaded wordlist

    Raises:
        Exception: If download fails
    """
    output_path = Path("sessions/wordlists/rockyou.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    url = "https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt"

    Log.info(f"Downloading RockYou from {url}...")
    Log.info("This may take several minutes (134 MB)...")

    try:
        result = subprocess.run(
            f"curl -L -o {output_path} {url}",
            shell=True,
            timeout=600,
        )
        if result.returncode == 0 and output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            Log.good(f"✓ Downloaded RockYou to {output_path} ({size_mb:.1f} MB)")
            config = {"wordlist_path": str(output_path)}
            config_file = Path("sessions/wordlist_config.json")
            config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
            return str(output_path)
        else:
            raise Exception("Download failed or file not created.")
    except subprocess.TimeoutExpired:
        Log.bad("Download timed out. Please try again later.")
        raise
    except Exception as e:
        Log.bad(f"Error downloading RockYou: {e}")
        raise


def _clone_seclists() -> str:
    """Clone SecLists repository.

    Returns:
        str: Path to cloned SecLists directory

    Raises:
        Exception: If clone fails
    """
    seclists_path = Path.home() / "hack" / "wordlists" / "SecLists"

    Log.info(f"Cloning SecLists to {seclists_path}...")
    Log.info("This may take a few minutes (~2 GB)...")

    try:
        seclists_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            f"git clone --depth 1 https://github.com/danielmiessler/SecLists {seclists_path}",
            shell=True,
            timeout=600,
        )
        if result.returncode == 0 and seclists_path.exists():
            Log.good(f"✓ Cloned SecLists to {seclists_path}")
            config = {"wordlist_path": str(seclists_path)}
            config_file = Path("sessions/wordlist_config.json")
            config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
            return str(seclists_path)
        else:
            raise Exception("Clone failed.")
    except subprocess.TimeoutExpired:
        Log.bad("Clone timed out. Please check your internet connection.")
        raise
    except Exception as e:
        Log.bad(f"Error cloning SecLists: {e}")
        raise


def _custom_wordlist_path() -> str:
    """Prompt user for custom wordlist path.

    Returns:
        str: Validated path to wordlist

    Raises:
        Exception: If path is invalid or user cancels
    """
    try:
        custom_path = input("Enter wordlist path or directory: ").strip()
    except KeyboardInterrupt:
        print()
        raise Exception("Custom path cancelled.")

    if not custom_path:
        raise Exception("No path provided.")

    custom_path = os.path.expanduser(custom_path)

    if not os.path.exists(custom_path):
        Log.bad(f"Path does not exist: {custom_path}")
        raise Exception("Invalid path.")

    # Show info about the path
    if os.path.isdir(custom_path):
        try:
            count = sum(1 for _ in Path(custom_path).rglob("*") if _.is_file())
            size_mb = sum(f.stat().st_size for f in Path(custom_path).rglob("*") if f.is_file()) / (1024 * 1024)
            Log.info(f"Directory: {count} files, {size_mb:.1f} MB")
        except Exception:
            Log.info(f"Directory: {custom_path}")
    elif os.path.isfile(custom_path):
        size_mb = os.path.getsize(custom_path) / (1024 * 1024)
        Log.info(f"File: {size_mb:.1f} MB")

    Log.good(f"✓ Using wordlist: {custom_path}")
    config = {"wordlist_path": custom_path}
    config_file = Path("sessions/wordlist_config.json")
    config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return custom_path


def get_wordlist_path() -> str:
    """Get the path to configured wordlist, or prompt to configure if not set.

    Returns:
        str: Path to wordlist directory or file

    Raises:
        Exception: If wordlist cannot be located or user cancels
    """
    config_file = Path("sessions/wordlist_config.json")

    # Try to load existing config
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text(encoding="utf-8"))
            wordlist_path = config.get("wordlist_path")
            if wordlist_path and os.path.exists(wordlist_path):
                Log.good(f"✓ Using configured wordlist: {wordlist_path}")
                return wordlist_path
        except Exception:
            pass

    # Config doesn't exist or is invalid, ensure wordlist
    return ensure_wordlist()
