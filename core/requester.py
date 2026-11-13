"""Pembungkus requests.Session dan penyimpanan cookie lokal."""

from http.cookiejar import Cookie
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import requests

from core.session_manager import SessionManager


class RequestError(Exception):
    """Error request atau penyimpanan cookie yang bisa ditampilkan ke pengguna."""


class PirateRequester:
    """Mengirim request ke satu target dan mengelola cookie sesi."""

    def __init__(
        self,
        proxy: str | None = None,
        sessions_dir: str | Path | None = None,
        timeout: float = 15,
    ) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            }
        )
        self.timeout = timeout
        self.sessions_dir = Path(
            sessions_dir or Path(__file__).resolve().parent.parent / "sessions"
        )
        self._session_manager: SessionManager | None = None
        self._last_host: str | None = None
        if proxy:
            self.session.proxies.update({"http": proxy, "https": proxy})

    @property
    def session_manager(self) -> SessionManager:
        if self._session_manager is None:
            self._session_manager = SessionManager(str(self.sessions_dir))
        return self._session_manager

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        return self._request("POST", url, **kwargs)

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            raise RequestError(f"Request ke {url} gagal: {exc}") from exc

    @staticmethod
    def _host_name(host_or_url: str) -> str:
        value = host_or_url.strip()
        parsed = urlsplit(value if "://" in value else f"//{value}")
        hostname = parsed.hostname
        if not hostname:
            raise RequestError(f"Host tidak valid: {host_or_url}")
        return hostname.rstrip(".").lower()

    def _cookie_path(self, host_or_url: str) -> Path:
        host = self._host_name(host_or_url)
        return self.session_manager._cookie_path(host)

    def save_cookies(self, host_or_url: str) -> Path:
        """Simpan cookie yang berlaku untuk host ini ke berkas JSON."""
        host = self._host_name(host_or_url)
        cookies = []
        for cookie in self.session.cookies:
            domain = cookie.domain.lstrip(".").lower()
            if domain and host != domain and not host.endswith(f".{domain}"):
                continue
            cookies.append(
                {
                    "name": cookie.name,
                    "value": cookie.value,
                    "domain": cookie.domain,
                    "path": cookie.path,
                    "secure": cookie.secure,
                    "expires": cookie.expires,
                    "rest": cookie._rest,
                }
            )

        try:
            path = Path(self.session_manager.save(host, cookies))
        except OSError as exc:
            raise RequestError(f"Gagal menyimpan cookie: {exc}") from exc
        self._last_host = host
        return path

    def load_cookies(self, host_or_url: str) -> list[dict[str, Any]]:
        """Muat cookie host dari JSON ke session dan kembalikan datanya."""
        host = self._host_name(host_or_url)
        path = self._cookie_path(host)
        try:
            data = self.session_manager.load_records(host)
        except FileNotFoundError as exc:
            raise RequestError(
                f"Belum ada cookie tersimpan untuk {host}."
            ) from exc
        except (OSError, ValueError) as exc:
            raise RequestError(f"Gagal membaca cookie: {exc}") from exc

        loaded: list[dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                raise RequestError(f"Format cookie di {path.name} tidak valid.")
            cookie = Cookie(
                version=0,
                name=item["name"],
                value=str(item.get("value", "")),
                port=None,
                port_specified=False,
                domain=str(item.get("domain", "")),
                domain_specified=bool(item.get("domain")),
                domain_initial_dot=str(item.get("domain", "")).startswith("."),
                path=str(item.get("path", "/")),
                path_specified=True,
                secure=bool(item.get("secure", False)),
                expires=item.get("expires"),
                discard=item.get("expires") is None,
                comment=None,
                comment_url=None,
                rest=item.get("rest", {}),
                rfc2109=False,
            )
            self.session.cookies.set_cookie(cookie)
            loaded.append(item)
        return loaded

    def save_session_meta(self, meta: dict[str, Any]) -> None:
        """Simpan metadata untuk host terakhir yang cookie-nya disimpan."""
        if self._last_host is None:
            raise RequestError("Simpan cookie terlebih dahulu sebelum metadata sesi.")
        try:
            cookies = self.session_manager.load_records(self._last_host)
            self.session_manager.save(self._last_host, cookies, meta=meta)
        except (OSError, ValueError) as exc:
            raise RequestError(f"Gagal menyimpan metadata sesi: {exc}") from exc
