"""Fingerprint teknologi dari respons yang sudah diambil."""

import re
from collections.abc import Mapping


def detect_technologies(
    headers: Mapping[str, str],
    cookies: object,
    html: str,
) -> list[dict[str, object]]:
    """Kembalikan teknologi unik beserta bukti yang ditemukan."""
    findings: dict[str, list[str]] = {}

    def add(technology: str, evidence: str) -> None:
        findings.setdefault(technology, [])
        if evidence not in findings[technology]:
            findings[technology].append(evidence)

    for header_name, technology_patterns in {
        "server": (
            (r"\bnginx\b", "Nginx"),
            (r"\bapache\b", "Apache"),
            (r"\bmicrosoft-iis\b|\biis\b", "Microsoft IIS"),
            (r"\bcaddy\b", "Caddy"),
            (r"\bcloudflare\b", "Cloudflare"),
        ),
        "x-powered-by": (
            (r"\bphp\b", "PHP"),
            (r"\bexpress\b", "Express"),
            (r"\basp\.net\b", "ASP.NET"),
            (r"\bnext\.js\b", "Next.js"),
            (r"\bpython\b", "Python"),
        ),
        "x-generator": (
            (r"\bwordpress\b", "WordPress"),
            (r"\bdrupal\b", "Drupal"),
            (r"\bjoomla\b", "Joomla"),
        ),
    }.items():
        value = next((v for k, v in headers.items() if k.lower() == header_name), "")
        for pattern, technology in technology_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                add(technology, f"Header {header_name}: {value}")

    for name in _cookie_names(cookies):
        for pattern, technology in (
            (r"^phpsessid$", "PHP"),
            (r"^jsessionid$", "Java"),
            (r"^laravel_session$", "Laravel"),
            (r"^connect\.sid$", "Express"),
            (r"^csrftoken$", "Django"),
            (r"^sessionid$", "Django"),
            (r"^_session_id$", "Ruby on Rails"),
        ):
            if re.search(pattern, name, re.IGNORECASE):
                add(technology, f"Cookie {name}")

    for pattern, technology in (
        (r"wp-content|wp-includes", "WordPress"),
        (r"__NEXT_DATA__", "Next.js"),
        (r"\bng-version\s*=", "Angular"),
        (r"/_next/static/", "Next.js"),
        (r"drupalSettings", "Drupal"),
        (r"cdn\.shopify\.com", "Shopify"),
    ):
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            add(technology, f"Pola HTML: {match.group(0)}")

    return [
        {"technology": technology, "evidence": evidence}
        for technology, evidence in findings.items()
    ]


def _cookie_names(cookies: object) -> list[str]:
    if hasattr(cookies, "keys"):
        return [str(name) for name in cookies.keys()]  # type: ignore[union-attr]
    if isinstance(cookies, (list, tuple)):
        names = []
        for cookie in cookies:
            name = getattr(cookie, "name", None)
            if name is None and isinstance(cookie, dict):
                name = cookie.get("name")
            if name is not None:
                names.append(str(name))
        return names
    return []
