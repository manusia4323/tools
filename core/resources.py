"""Helper untuk menyiapkan dan membaca wordlist lokal."""

import os
from pathlib import Path
from typing import Any

from core import config


def _wordlist_dir() -> Path:
    return Path(config.get_wordlist_dir())


def ensure_wordlist_dir() -> str:
    """Pastikan folder wordlist tersedia dan kembalikan lokasi foldernya."""
    directory = _wordlist_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return str(directory)


def load_wordlist(name: str) -> list[str]:
    """Muat satu wordlist dan lewati baris kosong atau komentar."""
    directory = _wordlist_dir()
    requested_path = Path(name)
    path = requested_path if requested_path.is_absolute() else directory / requested_path
    return _read_wordlist(path, name)


def _read_wordlist(path: Path, name: str) -> list[str]:
    try:
        with path.open("r", encoding="utf-8") as file:
            return [
                line
                for raw_line in file
                if (line := raw_line.strip()) and not line.startswith("#")
            ]
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Wordlist '{name}' tidak ditemukan (dicari di {path.resolve()})"
        ) from exc


def list_wordlists() -> list[dict[str, Any]]:
    """Tampilkan file dan folder yang ada tepat di dalam gudang."""
    directory = _wordlist_dir()
    if not directory.is_dir():
        return []

    directories = [
        {
            "name": path.name,
            "path": str(path.resolve()),
            "lines": None,
            "type": "dir",
        }
        for path in directory.iterdir()
        if path.is_dir()
    ]
    files = [
        {
            "name": path.name,
            "path": str(path.resolve()),
            "lines": len(_read_wordlist(path, path.name)),
            "type": "file",
        }
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() == ".txt"
    ]
    directories.sort(key=lambda wordlist: str(wordlist["name"]).casefold())
    files.sort(key=lambda wordlist: str(wordlist["name"]).casefold())
    return directories + files


def find_wordlist(name: str) -> list[str]:
    """Cari nama file TXT sampai empat tingkat di bawah gudang."""
    directory = _wordlist_dir()
    if not directory.is_dir():
        return []

    needle = name.casefold()
    matches: list[str] = []

    def raise_walk_error(error: OSError) -> None:
        raise error

    for current_dir, subdirs, filenames in os.walk(
        directory,
        onerror=raise_walk_error,
    ):
        current_path = Path(current_dir)
        depth = len(current_path.relative_to(directory).parts)
        subdirs.sort(key=str.casefold)
        if depth >= 4:
            subdirs.clear()

        for filename in filenames:
            if filename.lower().endswith(".txt") and needle in filename.casefold():
                relative_path = (current_path / filename).relative_to(directory)
                matches.append(relative_path.as_posix())

    return sorted(matches, key=str.casefold)[:50]


ensure_wordlist_dir()
