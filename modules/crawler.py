"""Crawler ringan untuk memetakan link dan form di website yang diizinkan."""

import time
import warnings
from collections import deque
from typing import Any
from urllib.parse import urldefrag, urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

from core.logger import PirateLogger
from core.requester import PirateRequester, RequestError


class Crawler:
    def __init__(
        self,
        requester: PirateRequester,
        start_url: str,
        max_depth: int = 2,
        max_pages: int = 50,
        delay: float = 0.5,
        same_domain_only: bool = True,
        no_robots: bool = False,
    ) -> None:
        normalized_start = self._normalize_url(start_url)
        if normalized_start is None:
            raise ValueError(f"URL awal tidak valid: {start_url}")

        self.requester = requester
        self.start_url = normalized_start
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = max(0.0, delay)
        self.same_domain_only = same_domain_only
        self.no_robots = no_robots
        self._start_domain = (urlsplit(self.start_url).hostname or "").lower()
        self._links: list[str] = []
        self._link_set: set[str] = set()
        self._forms: list[dict[str, Any]] = []
        self._form_indexes: dict[tuple[str, str], int] = {}
        self._visited: list[str] = []
        self._visited_set: set[str] = set()
        self._queue: deque[tuple[str, int]] = deque()
        self._queued: set[str] = set()
        self._request_count = 0
        self._robots: RobotFileParser | None = None

    @staticmethod
    def _normalize_url(url: str, base_url: str | None = None) -> str | None:
        absolute_url = urldefrag(urljoin(base_url or url, url)).url
        parsed = urlsplit(absolute_url)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
            return None
        return absolute_url

    def _request(self, url: str, **kwargs: Any) -> requests.Response:
        if self._request_count:
            time.sleep(self.delay)
        self._request_count += 1
        return self.requester.get(url, **kwargs)

    def _load_robots(self) -> bool:
        if not self.same_domain_only or self.no_robots:
            return True

        robots_url = urljoin(self.start_url, "/robots.txt")
        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            response = self._request(robots_url)
        except RequestError as exc:
            response = getattr(exc.__cause__, "response", None)
            if getattr(response, "status_code", None) == 404:
                parser.parse([])
            else:
                PirateLogger.warn(f"Gagal membaca robots.txt; crawl dihentikan: {exc}")
                return False
        else:
            parser.parse(response.text.splitlines())
        self._robots = parser
        return True

    def _same_domain(self, url: str) -> bool:
        parsed = urlsplit(url)
        return (
            not self.same_domain_only
            or (parsed.hostname or "").lower() == self._start_domain
        )

    def _allowed(self, url: str) -> bool:
        if not self._same_domain(url):
            return False
        if self._robots is not None and not self._robots.can_fetch("*", url):
            return False
        return True

    def _add_form(self, action: str, method: str, inputs: list[str]) -> None:
        key = (action, method)
        if key in self._form_indexes:
            existing_inputs = self._forms[self._form_indexes[key]]["inputs"]
            for name in inputs:
                if name not in existing_inputs:
                    existing_inputs.append(name)
            return

        self._form_indexes[key] = len(self._forms)
        self._forms.append(
            {
                "action": action,
                "method": method,
                "inputs": inputs,
            }
        )

    def _extract_page(self, html: str, page_url: str, depth: int) -> None:
        soup = BeautifulSoup(html, "html.parser")
        for anchor in soup.find_all("a", href=True):
            link = self._normalize_url(str(anchor["href"]), page_url)
            if link is None or not self._same_domain(link):
                continue
            if link not in self._link_set:
                self._link_set.add(link)
                self._links.append(link)
            if depth < self.max_depth and link not in self._queued:
                self._queue.append((link, depth + 1))
                self._queued.add(link)

        for form in soup.find_all("form"):
            raw_action = form.get("action") or page_url
            action = urldefrag(urljoin(page_url, str(raw_action))).url
            method = str(form.get("method", "get")).lower()
            inputs: list[str] = []
            for field in form.find_all("input", attrs={"name": True}):
                name = str(field.get("name", "")).strip()
                if name and name not in inputs:
                    inputs.append(name)
            self._add_form(action, method, inputs)

    def crawl(self) -> None:
        self._links.clear()
        self._link_set.clear()
        self._forms.clear()
        self._form_indexes.clear()
        self._visited.clear()
        self._visited_set.clear()
        self._queue.clear()
        self._queued.clear()
        self._request_count = 0
        self._robots = None

        if not self._load_robots() or self.max_pages <= 0:
            return

        self._queue.append((self.start_url, 0))
        self._queued.add(self.start_url)
        while self._queue and len(self._visited) < self.max_pages:
            url, depth = self._queue.popleft()
            if url in self._visited_set or not self._allowed(url):
                continue

            self._visited_set.add(url)
            self._visited.append(url)
            try:
                response = self._request(url, allow_redirects=False)
            except RequestError as exc:
                PirateLogger.warn(f"Gagal membuka halaman {url}: {exc}")
                continue

            if 300 <= response.status_code < 400:
                location = response.headers.get("Location")
                redirect_url = (
                    self._normalize_url(location, response.url) if location else None
                )
                if (
                    redirect_url is not None
                    and redirect_url not in self._visited_set
                    and redirect_url not in self._queued
                    and self._allowed(redirect_url)
                ):
                    self._queue.append((redirect_url, depth))
                    self._queued.add(redirect_url)
                continue

            self._extract_page(response.text, response.url, depth)

    def get_links(self) -> list[str]:
        return list(self._links)

    def get_forms(self) -> list[dict[str, Any]]:
        return [
            {**form, "inputs": list(form["inputs"])}
            for form in self._forms
        ]

    def get_visited(self) -> list[str]:
        return list(self._visited)
