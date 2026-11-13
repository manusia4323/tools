"""CLI inventarisasi teknis satu website yang diizinkan."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from core.config import load_config
from core.logger import PirateLogger
from core.models import Finding, ScanResult
from core.reporter import Reporter
from core.resources import find_wordlist, list_wordlists, load_wordlist
from core.requester import PirateRequester, RequestError
from core.session_manager import SessionManager
from modules.login_finder import find_login_page
from modules.tech_detect import detect_technologies


def build_parser() -> argparse.ArgumentParser:
    config = load_config()
    parser = argparse.ArgumentParser(
        prog="the-pirates",
        description="Bantu dokumentasikan teknologi dari satu website yang diizinkan.",
    )
    parser.add_argument(
        "--output",
        choices=("term", "json", "md"),
        default="term",
        help="Format laporan (term, json, atau md).",
    )
    parser.add_argument(
        "--out-dir",
        default=config["REPORT_DIR"],
        help="Folder untuk menyimpan laporan.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    recon = commands.add_parser("recon", help="Periksa satu halaman website.")
    recon.add_argument("-u", "--url", required=True, help="URL website yang diperiksa.")
    recon.add_argument("--proxy", help="Proxy opsional, misalnya http://127.0.0.1:8080.")
    recon.add_argument("--no-save", action="store_true", help="Jangan simpan cookie ke disk.")

    cookies = commands.add_parser("cookies", help="Tampilkan cookie yang tersimpan.")
    cookies.add_argument("-H", "--host", required=True, help="Host, misalnya example.com.")

    sessions = commands.add_parser("sessions", help="Kelola sesi cookie tersimpan.")
    session_commands = sessions.add_subparsers(
        dest="sessions_command",
        required=True,
    )
    session_commands.add_parser("list", help="Tampilkan daftar sesi.")

    session_info = session_commands.add_parser("info", help="Tampilkan detail sesi.")
    session_info.add_argument("-H", "--host", required=True, help="Host sesi.")

    session_delete = session_commands.add_parser(
        "delete",
        help="Hapus sesi setelah konfirmasi.",
    )
    session_delete.add_argument("-H", "--host", required=True, help="Host sesi.")

    wordlists = commands.add_parser("wordlists", help="Lihat wordlist lokal.")
    wordlist_commands = wordlists.add_subparsers(
        dest="wordlists_command",
        required=True,
    )
    wordlist_commands.add_parser("list", help="Tampilkan daftar wordlist.")

    wordlist_show = wordlist_commands.add_parser(
        "show",
        help="Tampilkan beberapa baris wordlist.",
    )
    wordlist_show.add_argument("-n", "--name", required=True, help="Nama file wordlist.")

    wordlist_find = wordlist_commands.add_parser(
        "find",
        help="Cari wordlist berdasarkan nama file.",
    )
    wordlist_find.add_argument("-n", "--name", required=True, help="Nama yang dicari.")
    return parser


def run_recon(args: argparse.Namespace) -> int:
    result = ScanResult(
        target=args.url,
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    requester = PirateRequester(proxy=args.proxy)
    PirateLogger.info(f"Mengambil satu halaman: {args.url}")
    response = requester.get(args.url)

    technologies = detect_technologies(
        response.headers,
        response.cookies,
        response.text,
    )
    for technology in technologies:
        for evidence in technology["evidence"]:
            result.add(
                Finding(
                    type="tech",
                    severity="info",
                    url=args.url,
                    evidence=str(evidence),
                    confidence="high",
                    detail={"tech": str(technology["technology"])},
                )
            )

    login = find_login_page(response.text, response.url)
    if login["is_login"]:
        for reason in login["reasons"]:
            result.add(
                Finding(
                    type="login-page",
                    severity="info",
                    url=args.url,
                    evidence=str(reason),
                    confidence="medium",
                    detail={
                        "form_action": login["form_action"],
                        "form_method": login["method"],
                        "username_fields": (
                            [login["username_field"]]
                            if login["username_field"]
                            else []
                        ),
                    },
                )
            )

    if not args.no_save:
        saved_path = requester.save_cookies(response.url)
        PirateLogger.good(f"Cookie disimpan di {saved_path}")
        requester.save_session_meta(
            {
                "source": "recon",
                "has_login_page": bool(login["is_login"]),
                "technologies": [
                    str(technology["technology"]) for technology in technologies
                ],
            }
        )

    result.finished_at = datetime.now(timezone.utc).isoformat()
    reporter = Reporter(result)
    if args.output == "term":
        reporter.to_terminal()
    else:
        host = urlparse(args.url).netloc or "target"
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        extension = "json" if args.output == "json" else "md"
        output_path = Path(args.out_dir) / f"{host}-{timestamp}.{extension}"
        if args.output == "json":
            reporter.to_json(str(output_path))
        else:
            reporter.to_markdown(str(output_path))
    return 0


def run_cookies(host: str) -> int:
    requester = PirateRequester()
    cookies = requester.load_cookies(host)
    if not cookies:
        PirateLogger.warn(f"Belum ada cookie tersimpan untuk {host}.")
        return 0
    PirateLogger.info(f"Cookie tersimpan untuk {host}:")
    for cookie in cookies:
        PirateLogger.good(f"{cookie['name']} = {cookie.get('value', '')}")
    return 0


def run_sessions(args: argparse.Namespace) -> int:
    manager = SessionManager()
    if args.sessions_command == "list":
        sessions = manager.list()
        if not sessions:
            PirateLogger.warn("Belum ada sesi tersimpan.")
            return 0
        for session in sessions:
            PirateLogger.info(
                f"{session['host']} | {session['cookie_count']} | "
                f"{session['created_at']} | {session['updated_at']}"
            )
        return 0

    host = args.host
    if args.sessions_command == "info":
        session = manager.info(host)
        if session is None:
            PirateLogger.warn(f"Sesi untuk {host} tidak ditemukan.")
            return 0

        PirateLogger.info(f"Host: {session['host']}")
        PirateLogger.info(f"Jumlah cookie: {session['cookie_count']}")
        PirateLogger.info(f"Dibuat: {session['created_at']}")
        PirateLogger.info(f"Diperbarui: {session['updated_at']}")
        excluded = {
            "host",
            "cookie_count",
            "created_at",
            "updated_at",
            "has_meta",
        }
        PirateLogger.info("Metadata:")
        meta_items = [(key, value) for key, value in session.items() if key not in excluded]
        if meta_items:
            for key, value in meta_items:
                PirateLogger.info(f"  {key}: {value}")
        else:
            PirateLogger.info("  Tidak ada metadata.")

        PirateLogger.info("Cookie (tersamarkan):")
        masked_cookies = manager.mask_cookies(host)
        if masked_cookies:
            for name, value in masked_cookies.items():
                PirateLogger.info(f"  {name}: {value}")
        else:
            PirateLogger.info("  Tidak ada cookie.")
        return 0

    confirmation = input(f"Hapus sesi untuk {host}? [y/N] ")
    if confirmation.strip().lower() == "y":
        if manager.delete(host):
            PirateLogger.good(f"Sesi untuk {host} berhasil dihapus.")
        else:
            PirateLogger.info(f"Sesi untuk {host} tidak ditemukan.")
    else:
        PirateLogger.info("Penghapusan sesi dibatalkan.")
    return 0


def run_wordlists(args: argparse.Namespace) -> int:
    if args.wordlists_command == "list":
        wordlists = list_wordlists()
        if not wordlists:
            PirateLogger.warn("Belum ada wordlist.")
            return 0

        was_debug_enabled = PirateLogger.debug_enabled
        PirateLogger.debug_enabled = True
        try:
            for wordlist in wordlists:
                if wordlist["type"] == "dir":
                    PirateLogger.debug(f"[dir]  {wordlist['name']}")
                else:
                    PirateLogger.info(
                        f"[file] {wordlist['name']}  ({wordlist['lines']} baris)"
                    )
        finally:
            PirateLogger.debug_enabled = was_debug_enabled
        return 0

    if args.wordlists_command == "find":
        matches = find_wordlist(args.name)
        if not matches:
            PirateLogger.warn(
                f"Tidak ada wordlist yang cocok dengan '{args.name}'."
            )
            return 0
        for match in matches:
            PirateLogger.info(match)
        return 0

    try:
        entries = load_wordlist(args.name)
    except FileNotFoundError as exc:
        PirateLogger.bad(str(exc))
        return 1

    was_debug_enabled = PirateLogger.debug_enabled
    PirateLogger.debug_enabled = True
    try:
        for entry in entries[:10]:
            PirateLogger.debug(entry)
    finally:
        PirateLogger.debug_enabled = was_debug_enabled
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "recon":
            parsed_url = urlparse(args.url)
            if parsed_url.scheme not in ("http", "https") or not parsed_url.hostname:
                parser.error("URL harus memakai http:// atau https:// dan memiliki host.")
            return run_recon(args)
        if args.command == "cookies":
            return run_cookies(args.host)
        if args.command == "sessions":
            return run_sessions(args)
        if args.command == "wordlists":
            return run_wordlists(args)
    except RequestError as exc:
        PirateLogger.bad(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

