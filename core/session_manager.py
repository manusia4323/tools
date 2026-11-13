"""Pengelolaan cookie sesi dan metadata lokal."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from core.config import load_config


class SessionManager:
    def __init__(self, session_dir: str | None = None) -> None:
        config = load_config()
        if session_dir is None:
            configured_dir = Path(config["SESSION_DIR"])
            if not configured_dir.is_absolute():
                configured_dir = Path(__file__).resolve().parent.parent / configured_dir
            self.session_dir = configured_dir
        else:
            self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _normalize_host(host: str) -> str:
        value = host.strip()
        parsed = urlsplit(value if "://" in value else f"//{value}")
        hostname = parsed.hostname
        if not hostname:
            raise ValueError(f"Host tidak valid: {host}")
        return hostname.rstrip(".").lower()

    def _cookie_path(self, host: str) -> Path:
        hostname = self._normalize_host(host)
        safe_host = re.sub(r"[^a-z0-9.-]", "_", hostname)
        return self.session_dir / f"{safe_host}.json"

    def _meta_path(self, host: str) -> Path:
        cookie_path = self._cookie_path(host)
        return cookie_path.with_name(f"{cookie_path.stem}.meta.json")

    @staticmethod
    def _read_json(path: Path) -> Any:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _read_cookie_data(self, host: str) -> dict[str, Any] | list[dict[str, Any]] | None:
        path = self._cookie_path(host)
        if not path.exists():
            return None
        data = self._read_json(path)
        if isinstance(data, dict):
            return data
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            return data
        raise ValueError(f"Format cookie di {path.name} tidak valid.")

    def _read_meta(self, host: str) -> dict[str, Any]:
        path = self._meta_path(host)
        if not path.exists():
            return {}
        data = self._read_json(path)
        if not isinstance(data, dict):
            raise ValueError(f"Format metadata di {path.name} tidak valid.")
        return data

    @staticmethod
    def _file_timestamps(path: Path) -> tuple[str, str]:
        stat = path.stat()
        created_timestamp = getattr(stat, "st_birthtime", stat.st_ctime)
        created_at = datetime.fromtimestamp(
            created_timestamp, timezone.utc
        ).isoformat()
        updated_at = datetime.fromtimestamp(
            stat.st_mtime, timezone.utc
        ).isoformat()
        return created_at, updated_at

    @staticmethod
    def _cookie_count(data: dict[str, Any] | list[dict[str, Any]] | None) -> int:
        if data is None:
            return 0
        return len(data)

    def list(self) -> list[dict[str, Any]]:
        sessions: list[dict[str, Any]] = []
        for path in sorted(self.session_dir.glob("*.json")):
            if path.name.endswith(".meta.json"):
                continue

            host = path.stem
            data = self._read_cookie_data(host)
            meta = self._read_meta(host)
            file_created, file_updated = self._file_timestamps(path)
            sessions.append(
                {
                    "host": host,
                    "path": str(path),
                    "cookie_count": self._cookie_count(data),
                    "created_at": meta.get("created_at", file_created),
                    "updated_at": meta.get("updated_at", file_updated),
                    "has_meta": self._meta_path(host).is_file(),
                }
            )
        return sorted(sessions, key=lambda session: session["host"])

    def load(self, host: str) -> dict[str, Any]:
        data = self._read_cookie_data(host)
        if data is None:
            return {}
        if isinstance(data, dict):
            return data
        return {
            str(cookie["name"]): cookie.get("value", "")
            for cookie in data
            if isinstance(cookie.get("name"), str)
        }

    def load_records(self, host: str) -> list[dict[str, Any]]:
        """Muat record lengkap agar requester tetap menyimpan atribut cookie."""
        data = self._read_cookie_data(host)
        if data is None:
            raise FileNotFoundError(f"Cookie untuk {host} tidak ditemukan.")
        if isinstance(data, list):
            return data
        return [
            {
                "name": name,
                "value": value,
                "domain": "",
                "path": "/",
                "secure": False,
                "expires": None,
                "rest": {},
            }
            for name, value in data.items()
        ]

    def save(
        self,
        host: str,
        cookies: dict[str, Any] | list[dict[str, Any]],
        meta: dict[str, Any] | None = None,
    ) -> str:
        """Simpan cookie dan, jika diminta, metadata sesi."""
        cookie_path = self._cookie_path(host)
        normalized_host = self._normalize_host(host)
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        with cookie_path.open("w", encoding="utf-8") as file:
            json.dump(cookies, file, indent=2, ensure_ascii=False)

        if meta is not None:
            meta_path = self._meta_path(normalized_host)
            previous_meta = self._read_meta(normalized_host)
            now = datetime.now(timezone.utc).isoformat()
            meta_data = {
                **meta,
                "host": normalized_host,
                "created_at": previous_meta.get("created_at", now),
                "updated_at": now,
            }
            with meta_path.open("w", encoding="utf-8") as file:
                json.dump(meta_data, file, indent=2, ensure_ascii=False)

        return str(cookie_path)

    def info(self, host: str) -> dict[str, Any] | None:
        cookie_path = self._cookie_path(host)
        if not cookie_path.is_file():
            return None

        normalized_host = self._normalize_host(host)
        data = self._read_cookie_data(normalized_host)
        meta = self._read_meta(normalized_host)
        file_created, file_updated = self._file_timestamps(cookie_path)
        return {
            **meta,
            "host": normalized_host,
            "cookie_count": self._cookie_count(data),
            "created_at": meta.get("created_at", file_created),
            "updated_at": meta.get("updated_at", file_updated),
            "has_meta": self._meta_path(normalized_host).is_file(),
        }

    def delete(self, host: str) -> bool:
        cookie_path = self._cookie_path(host)
        meta_path = self._meta_path(host)
        deleted = False
        for path in (cookie_path, meta_path):
            try:
                path.unlink()
                deleted = True
            except FileNotFoundError:
                pass
        return deleted

    def mask_cookies(self, host: str) -> dict[str, str]:
        return {
            name: f"*** ({len(str(value))} chars)"
            for name, value in self.load(host).items()
        }
