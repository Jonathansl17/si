"""input() with readline editing and an editable pre-filled value, like a web form field."""

import readline


def read_line(prompt: str, prefill: str = "") -> str:
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()
