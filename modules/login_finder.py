"""Pemeriksaan sederhana apakah respons tampak seperti halaman login."""

import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup


LOGIN_KEYWORDS = ("login", "log in", "signin", "sign in", "masuk")
USERNAME_HINTS = ("user", "email", "login", "account", "identifier")


def find_login_page(html: str, url: str) -> dict[str, Any]:
    """Analisis satu halaman dan kembalikan sinyal serta detail formulir."""
    soup = BeautifulSoup(html, "html.parser")
    reasons: list[str] = []
    password_input = soup.find("input", attrs={"type": re.compile(r"^password$", re.I)})

    if password_input:
        reasons.append("Ada input bertipe password.")

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    headings = [tag.get_text(" ", strip=True) for tag in soup.find_all("h1")]
    keyword_matches = []
    for location, value in [("judul", title), *[("h1", heading) for heading in headings], ("URL", url)]:
        lowered = value.lower()
        matches = [word for word in LOGIN_KEYWORDS if word in lowered]
        if matches:
            keyword_matches.append(f"Kata '{matches[0]}' ditemukan di {location}.")
    reasons.extend(keyword_matches)

    form = password_input.find_parent("form") if password_input else None
    if form is None:
        forms = soup.find_all("form")
        form = forms[0] if forms else None

    username_field = _guess_username_field(form, password_input) if form else None
    action = form.get("action", "") if form else None
    if action is not None:
        action = urljoin(url, action)
    method = form.get("method", "get").lower() if form else None

    return {
        "is_login": bool(password_input or keyword_matches),
        "reasons": reasons,
        "form_action": action,
        "method": method,
        "username_field": username_field,
    }


def _guess_username_field(form: Any, password_input: Any) -> str | None:
    for field in form.find_all(["input", "select"]):
        if field is password_input or field.get("disabled") is not None:
            continue
        field_type = field.get("type", "text").lower()
        if field_type not in ("text", "email", "tel", "search") and field.name == "input":
            continue
        name = field.get("name") or field.get("id")
        if not name:
            continue
        hint = f"{name} {field.get('id', '')} {field.get('placeholder', '')}".lower()
        if any(word in hint for word in USERNAME_HINTS) or field_type == "email":
            return str(name)
    return None
