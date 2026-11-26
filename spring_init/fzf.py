"""fzf runner: arrow-key menus and fuzzy multi-select, both with 'q' to go back."""

import shutil
import subprocess
from dataclasses import dataclass

from . import config, messages
from .errors import AbortedError, GoBack, SiError

_BACK_ACTION = f"print({config.BACK_SENTINEL})+accept"
# In a search box 'q' is also a letter: it only means "back" while the query is empty.
# The marked-row count rides on the sentinel because, with nothing marked, fzf would
# print the row under the cursor as if it had been chosen.
_BACK_KEEPING_MARKS = (
    f'[ -z {{q}} ] && echo "print({config.BACK_SENTINEL}$FZF_SELECT_COUNT)+accept" '
    f'|| echo "put({config.BACK_KEY})"'
)


@dataclass(frozen=True)
class Row:
    key: str
    columns: tuple[str, ...]
    preview: str = ""


class Fzf:
    def __init__(self, binary: str = config.FZF_BINARY):
        self._binary = shutil.which(binary)

    def menu(self, prompt: str, rows: list[Row], header: str) -> str:
        """Pick one row with arrows or j/k; no search, so 'q' always goes back."""
        return self._run(rows, self._base(prompt, header) + self._menu_options())[0]

    def search(self, prompt: str, rows: list[Row], header: str,
               marked: tuple[int, ...] = ()) -> list[str]:
        """Fuzzy multi-select; rows at the 0-based `marked` indexes start selected."""
        command = self._base(prompt, header) + self._search_options()
        if marked:
            toggles = "+".join(f"pos({index + 1})+toggle" for index in marked)
            command += ["--bind", f"load:{toggles}+first"]
        return self._run(rows, command)

    def _run(self, rows: list[Row], command: list[str]) -> list[str]:
        if not self._binary:
            raise SiError(messages.ERR_FZF_MISSING)
        result = subprocess.run(command, input="\n".join(map(_line, rows)),
                                stdout=subprocess.PIPE, text=True, check=False)
        if result.returncode in (config.FZF_EXIT_ABORTED, config.FZF_EXIT_NO_MATCH):
            raise AbortedError(messages.ABORTED)
        if result.returncode != 0:
            raise SiError(messages.ERR_FZF_STATUS.format(status=result.returncode))
        lines = [line for line in result.stdout.splitlines() if line]
        if lines and lines[0].startswith(config.BACK_SENTINEL):
            raise GoBack(_marked_keys(lines))
        return list(map(_key, lines))

    def _base(self, prompt: str, header: str) -> list[str]:
        return [
            self._binary, "--prompt", f"{prompt} > ", "--height", config.FZF_HEIGHT,
            "--layout", "reverse", "--border", "--header", header,
            "--delimiter", config.FZF_FIELD_SEPARATOR, "--with-nth", "2..-2",
            "--tabstop", config.FZF_TABSTOP,
        ]

    @staticmethod
    def _menu_options() -> list[str]:
        return ["--disabled", "--no-info", "--bind", "j:down,k:up",
                "--bind", f"{config.BACK_KEY}:{_BACK_ACTION}"]

    @staticmethod
    def _search_options() -> list[str]:
        return [
            "--multi", "--with-shell", config.FZF_SHELL,
            "--bind", "tab:toggle+clear-query+first", "--bind", "change:first",
            "--bind", f"{config.BACK_KEY}:transform:{_BACK_KEEPING_MARKS}",
            "--preview", "echo {-1}", "--preview-window", "down,3,wrap",
        ]


def _line(row: Row) -> str:
    fields = (row.key, *row.columns, row.preview)
    return config.FZF_FIELD_SEPARATOR.join(f.replace(config.FZF_FIELD_SEPARATOR, " ")
                                           for f in fields)


def _key(line: str) -> str:
    return line.split(config.FZF_FIELD_SEPARATOR, 1)[0]


def _marked_keys(lines: list[str]) -> list[str] | None:
    """Keys marked when 'q' was pressed; None for menus, which have no marks."""
    count = lines[0][len(config.BACK_SENTINEL):]
    if not count.isdigit():
        return None
    return list(map(_key, lines[1:])) if int(count) else []
