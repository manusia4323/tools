"""Command parsing utilities for shell commands."""

import shlex
from core.logger import PirateLogger

_GLOBAL_OPTIONS_WITH_VALUE = ("--output", "--out-dir")


def _split_global_options(tokens: list[str]) -> tuple[list[str], list[str]]:
    """Pisahkan opsi global (--output, --out-dir) dari token lainnya."""
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
    """Parse argumen CLI menggunakan build_parser() dari main.py."""
    from main import build_parser

    parser = build_parser()
    global_tokens, rest = _split_global_options(shlex.split(arg_string))
    argv = [*global_tokens, command_name, *rest]
    try:
        return parser.parse_args(argv)
    except SystemExit:
        PirateLogger.warn(f"Argumen tidak valid untuk '{command_name}'.")
        return None
