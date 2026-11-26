"""input() with an editable pre-filled default, like a web form field."""

import readline


def read_line(prompt: str, default: str) -> str:
    readline.set_startup_hook(lambda: readline.insert_text(default))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()
