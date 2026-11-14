"""Interactive shell for The Pirates with Skull Pirate ASCII art."""

from colorama import Fore, Style, init
from core.shell_commands import PirateShell

SKULL_BANNER = r"""
        ___
       /   \
      |     |
      |     |
       \___/
     .-'   '-.
    /         \
   |  _     _  |
   | ( )   ( ) |
   |     ^     |
    \   'v'   /
     '.     .'
   _.-'|   |'-._
  {    |===|    }
   '-.._____..-'
   / / / | \ \ \
  /_/ /  |  \ \_\
"""


def main() -> None:
    """Run the interactive shell with Skull Pirate ASCII art and welcome message."""
    init(autoreset=True)
    print(Fore.RED + SKULL_BANNER)
    print(Fore.CYAN + "Welcome to The Pirates. Type 'help' to see available commands.")
    print(Style.RESET_ALL)
    shell = PirateShell()
    shell.cmdloop()


if __name__ == "__main__":
    main()
