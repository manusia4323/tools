"""Antarmuka shell interaktif untuk The Pirates."""

import cmd
import shlex

from core.logger import PirateLogger
from core.scope_manager import ScopeManager


# Opsi global yang di main.py harus berada SEBELUM subcommand.
_GLOBAL_OPTIONS_WITH_VALUE = ("--output", "--out-dir")


def _split_global_options(tokens: list[str]) -> tuple[list[str], list[str]]:
    """Pisahkan opsi global (--output, --out-dir) dari token lainnya.

    Di main.py, opsi global harus ditulis sebelum subcommand
    (`the-pirates --output json recon ...`). Fungsi ini mengizinkan pengguna
    menaruhnya di mana saja dalam baris shell, karena hasil akhirnya dipindah
    ke depan sebelum di-parse.
    """
    globals_: list[str] = []
    rest: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        matched = False
        for option in _GLOBAL_OPTIONS_WITH_VALUE:
            if token == option and index + 1 < len(tokens):
                globals_.extend([token, tokens[index + 1]])
                index += 2
                matched = True
                break
            if token.startswith(f"{option}="):
                globals_.append(token)
                index += 1
                matched = True
                break
        if not matched:
            rest.append(token)
            index += 1
    return globals_, rest


def _parse_args(command_name: str, arg_string: str):
    """Parse argumen CLI menggunakan build_parser() dari main.py.

    Mengembalikan argparse.Namespace, atau None jika parsing gagal.
    Memastikan perintah di console identik dengan perintah `python main.py`.
    """
    from main import build_parser

    parser = build_parser()
    global_tokens, rest = _split_global_options(shlex.split(arg_string))
    argv = [*global_tokens, command_name, *rest]
    try:
        return parser.parse_args(argv)
    except SystemExit:
        PirateLogger.warn(f"Argumen tidak valid untuk '{command_name}'.")
        return None


class PirateShell(cmd.Cmd):
    """Shell interaktif berbasis cmd.Cmd untuk alat The Pirates."""

    prompt = "pirates> "

    def __init__(self) -> None:
        super().__init__()
        self.target: str = ""
        self.scope = ScopeManager()

    def do_target(self, arg: str) -> None:
        """Atur atau lihat target URL.

        Penggunaan: target set <URL> | show | clear
        """
        parts = arg.split(None, 1)
        if not parts:
            PirateLogger.warn("Gunakan: target set <URL> | show | clear")
            return

        sub = parts[0].lower()

        if sub == "set":
            if len(parts) < 2:
                PirateLogger.warn("Gunakan: target set <URL>")
                return
            self.target = parts[1].strip()
            PirateLogger.good(f"Target disetel: {self.target}")
        elif sub == "show":
            if not self.target:
                PirateLogger.warn("Belum ada target yang diatur.")
            else:
                PirateLogger.info(f"Target: {self.target}")
        elif sub == "clear":
            self.target = ""
            PirateLogger.info("Target dibersihkan.")
        else:
            PirateLogger.warn(f"Subcommand target tidak dikenal: {sub}")

    def do_scope(self, arg: str) -> None:
        """Kelola scope whitelist.

        Penggunaan: scope add <URL> | list | clear
        """
        parts = arg.split(None, 1)
        if not parts:
            PirateLogger.warn("Gunakan: scope add <URL> | list | clear")
            return

        sub = parts[0].lower()

        if sub == "add":
            if len(parts) < 2:
                PirateLogger.warn("Gunakan: scope add <URL>")
                return
            url = parts[1].strip()
            if self.scope.add(url):
                PirateLogger.good(f"Added to scope: {url}")
            else:
                PirateLogger.info(f"Already in scope: {url}")
        elif sub == "list":
            urls = self.scope.list()
            if not urls:
                PirateLogger.info("Scope is empty.")
            else:
                PirateLogger.info("Allowed URLs:")
                for url in urls:
                    print(f"  - {url}")
        elif sub == "clear":
            self.scope.clear()
            PirateLogger.good("Scope cleared.")
        else:
            PirateLogger.warn(f"Subcommand scope tidak dikenal: {sub}")

    def do_recon(self, arg: str) -> None:
        """Jalankan recon terhadap target.

        Penggunaan: recon [--output json|md] [--out-dir DIR] [--no-save]
        """
        if not self.target:
            PirateLogger.warn("Target belum diatur. Gunakan 'target set <URL>'.")
            return
        if not self.scope.is_allowed(self.target):
            PirateLogger.bad(f"Target not in scope. Add it with: scope add {self.target}")
            return
        from main import run_recon

        args = _parse_args("recon", f"-u {self.target} {arg}")
        if args is None:
            return
        run_recon(args)

    def do_crawl(self, arg: str) -> None:
        """Jalankan crawl terhadap target.

        Penggunaan: crawl [--depth N] [--max-pages N] [--delay N]
                           [--no-robots] [--output json|md]
        """
        if not self.target:
            PirateLogger.warn("Target belum diatur. Gunakan 'target set <URL>'.")
            return
        if not self.scope.is_allowed(self.target):
            PirateLogger.bad(f"Target not in scope. Add it with: scope add {self.target}")
            return
        from main import cmd_crawl

        args = _parse_args("crawl", f"-u {self.target} {arg}")
        if args is None:
            return
        cmd_crawl(args)

    def do_whatweb(self, arg: str) -> None:
        """Jalankan WhatWeb terhadap target.

        Penggunaan: whatweb
        """
        if not self.target:
            PirateLogger.warn("Target belum diatur. Gunakan 'target set <URL>'.")
            return
        if not self.scope.is_allowed(self.target):
            PirateLogger.bad(f"Target not in scope. Add it with: scope add {self.target}")
            return
        from main import cmd_whatweb

        args = _parse_args("whatweb", f"-u {self.target} {arg}")
        if args is None:
            return
        cmd_whatweb(args)

    def do_sessions(self, arg: str) -> None:
        """Kelola sesi cookie tersimpan.

        Penggunaan: sessions list | info -H <host> | delete -H <host>
        """
        from main import run_sessions

        args = _parse_args("sessions", arg)
        if args is None:
            return
        run_sessions(args)

    def do_wordlists(self, arg: str) -> None:
        """Kelola wordlist lokal.

        Penggunaan: wordlists list | show -n <name> | find -n <name>
        """
        from main import run_wordlists

        args = _parse_args("wordlists", arg)
        if args is None:
            return
        run_wordlists(args)

    def do_cookies(self, arg: str) -> None:
        """Tampilkan cookie tersimpan untuk host.

        Penggunaan: cookies -H <host>
        """
        from main import run_cookies

        args = _parse_args("cookies", arg)
        if args is None:
            return
        run_cookies(args.host)

    def do_exit(self, arg: str) -> bool:
        """Keluar dari shell interaktif."""
        print("Sampai jumpa, Kapten!")
        return True

    def do_EOF(self, arg: str) -> bool:
        """Keluar dengan Ctrl+D."""
        print("Sampai jumpa, Kapten!")
        return True
