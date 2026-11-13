"""Konfigurasi dasar The Pirates.

Contoh config.toml:
DEFAULT_TIMEOUT = 15
DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
SESSION_DIR = "sessions"
REPORT_DIR = "reports"
wordlist_dir = "/home/server/hack/wordlists"
VERIFY_SSL = false
MAX_REDIRECTS = 5

Hapus atau kosongkan wordlist_dir untuk memakai wordlists/ lokal.
"""

import tomllib
from pathlib import Path
from typing import Any

from core.logger import PirateLogger as Log


DEFAULT_TIMEOUT = 15
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
SESSION_DIR = "sessions"
REPORT_DIR = "reports"
WORDLIST_DIR = "wordlists"
VERIFY_SSL = False
MAX_REDIRECTS = 5


def load_config(path: str | Path = "config.toml") -> dict[str, Any]:
    """Muat konfigurasi TOML dan gabungkan dengan nilai bawaan."""
    config: dict[str, Any] = {
        "DEFAULT_TIMEOUT": DEFAULT_TIMEOUT,
        "DEFAULT_UA": DEFAULT_UA,
        "SESSION_DIR": SESSION_DIR,
        "REPORT_DIR": REPORT_DIR,
        "WORDLIST_DIR": WORDLIST_DIR,
        "wordlist_dir": None,
        "VERIFY_SSL": VERIFY_SSL,
        "MAX_REDIRECTS": MAX_REDIRECTS,
    }

    config_path = Path(path)
    if not config_path.exists():
        return config

    with config_path.open("rb") as config_file:
        config.update(tomllib.load(config_file))
    if config.get("wordlist_dir"):
        config["WORDLIST_DIR"] = config["wordlist_dir"]
    return config


def get_wordlist_dir() -> str:
    """Pilih gudang wordlist terkonfigurasi atau folder lokal."""
    config = load_config()
    configured_dir = config.get("wordlist_dir")
    if configured_dir:
        if Path(configured_dir).is_dir():
            return str(configured_dir)
        Log.warn(
            f"Folder wordlist di config tidak ditemukan: {configured_dir}. "
            f"Pakai folder lokal '{WORDLIST_DIR}'."
        )
    return WORDLIST_DIR
