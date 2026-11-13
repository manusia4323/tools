"""Logger kecil dengan warna untuk output CLI."""

from colorama import Fore, Style, init

init(autoreset=True)


class PirateLogger:
    """Menampilkan pesan singkat dengan level dan warna."""

    debug_enabled = False

    @classmethod
    def _write(cls, prefix: str, color: str, message: str) -> None:
        print(f"{color}[{prefix}] {message}{Style.RESET_ALL}")

    @classmethod
    def info(cls, message: str) -> None:
        cls._write("*", Fore.CYAN, message)

    @classmethod
    def good(cls, message: str) -> None:
        cls._write("+", Fore.GREEN, message)

    @classmethod
    def warn(cls, message: str) -> None:
        cls._write("!", Fore.YELLOW, message)

    @classmethod
    def bad(cls, message: str) -> None:
        cls._write("-", Fore.RED, message)

    @classmethod
    def debug(cls, message: str) -> None:
        if cls.debug_enabled:
            cls._write("~", Fore.MAGENTA, message)
