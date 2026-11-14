"""Scope manager for allowed URLs whitelist."""

import json
from pathlib import Path

from core.logger import PirateLogger


class ScopeManager:
    """Manages a whitelist of allowed URLs for scanning."""

    def __init__(self, scope_file: str | None = None) -> None:
        if scope_file is None:
            scope_file = Path(__file__).parent.parent / "sessions" / "scope.json"
        self.scope_file = Path(scope_file)
        self._whitelist: list[str] = []
        self._load()

    def _load(self) -> None:
        """Load whitelist from file."""
        if self.scope_file.exists():
            try:
                data = json.loads(self.scope_file.read_text(encoding="utf-8"))
                self._whitelist = data.get("whitelist", [])
            except (json.JSONDecodeError, OSError):
                self._whitelist = []

    def _save(self) -> None:
        """Save whitelist to file."""
        self.scope_file.parent.mkdir(parents=True, exist_ok=True)
        self.scope_file.write_text(
            json.dumps({"whitelist": self._whitelist}, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def add(self, url: str) -> bool:
        """Add a URL to the whitelist.

        Returns True if added, False if already exists.
        """
        url = url.strip().rstrip("/")
        if url in self._whitelist:
            return False
        self._whitelist.append(url)
        self._save()
        return True

    def list(self) -> list[str]:
        """Return the list of allowed URLs."""
        return self._whitelist.copy()

    def clear(self) -> None:
        """Clear all URLs from the whitelist."""
        self._whitelist = []
        self._save()

    def is_allowed(self, url: str) -> bool:
        """Check if a URL is in the whitelist.

        Checks both exact match and domain match.
        """
        url = url.strip().rstrip("/")
        if url in self._whitelist:
            return True

        # Also check if domain matches any whitelisted URL
        try:
            from urllib.parse import urlparse
            url_domain = urlparse(url).netloc
            for allowed in self._whitelist:
                allowed_domain = urlparse(allowed).netloc
                if url_domain == allowed_domain:
                    return True
        except Exception:
            pass

        return False