"""input() with readline line editing (arrows, history, Ctrl-A/E)."""

import readline  # noqa: F401  importing it is what enables line editing in input()


def read_line(prompt: str) -> str:
    return input(prompt)
