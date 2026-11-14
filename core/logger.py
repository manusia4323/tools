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

    @classmethod
    def banner(cls, text: str) -> None:
        """Print text with top and bottom border lines."""
        border = "=" * 50
        cls._write("*", Fore.CYAN, border)
        cls._write("*", Fore.CYAN, f"  {text}")
        cls._write("*", Fore.CYAN, border)

    @classmethod
    def separator(cls) -> None:
        """Print a thin separator line."""
        cls._write("", Fore.CYAN, "-" * 50)