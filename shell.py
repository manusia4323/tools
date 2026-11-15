"""Interactive shell for The Pirates with Skull Pirate ASCII art and self-installer."""

from colorama import Fore, Style, init
from core.installer import check_and_install_tools
from core.shell_commands import PirateShell

SKULL_BANNER = """

                                           .---------++++++
                                      .----+++++++++++++++++++++.
                                  .--+++++++++++++++++###+..-#   -+
                                -+++++++-  .---+########-
                               ++       -#########+  -.         -####+
                                  .##############+         +##########-
                               +########+  .###-      -###############-
                           .########+--    ###    .######################
                          -#########-      -   +#########################.
                         -#######-.- .-     ########################+#####.
                         .#########         ############ #########.  #######
                          #######-          -####################    #######
                          #####.  -.          .###############      .######.
                          -#    .##           -#############+    .   ######
                                 #            ###-.########    .     ######
                                  .           . .########     -.     +###+
                                               ##########             .##
                         -##                  ##### ###+.+++--.       +###
                        ####.               .###.     ####+###+  -..#######+
                        .#####---+#-..--..+####       .#####################
                           +##################    +#.  +#################+
                            .#################-  .###  +#######+  -#####
                              ################++.  ...-##+ #####  +####.
                                    ###################### +###    .###
                                      ##################### ##-
                                     +###  +##########++###
                                      ##-      -####   +####+#
                                      #.       +###+   +#####-
                                      ##+      ####     ####-
                                      .#-      ####    - -##
                                               +###     .
"""


def main() -> None:
    """Run the interactive shell with Skull Pirate ASCII art, self-installer, and menu system."""
    init(autoreset=True)
    print(Fore.RED + SKULL_BANNER)
    print(Fore.CYAN + "Welcome to The Pirates. Type 'help' to see available commands.")
    print(Style.RESET_ALL)

    # Run self-installer check before menu / cmdloop starts
    check_and_install_tools()

    shell = PirateShell()
    shell.cmdloop()


if __name__ == "__main__":
    main()
