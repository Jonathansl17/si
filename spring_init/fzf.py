"""fzf runner: fuzzy search as you type, single or multi selection."""

import shutil
import subprocess
from dataclasses import dataclass

from . import config, messages
from .errors import AbortedError, SiError


@dataclass(frozen=True)
class Row:
    key: str
    columns: tuple[str, ...]
    preview: str = ""


class Fzf:
    def __init__(self, binary: str = config.FZF_BINARY):
        self._binary = shutil.which(binary)

    def available(self) -> bool:
        return self._binary is not None

    def pick(self, prompt: str, rows: list[Row], multi: bool = False,
             header: str = "") -> list[str]:
        """Return the keys of the chosen rows, in display order."""
        if not self._binary:
            raise SiError(messages.ERR_FZF_MISSING)
        lines = [self._line(row) for row in rows]
        result = subprocess.run(self._command(prompt, multi, header), input="\n".join(lines),
                                stdout=subprocess.PIPE, text=True, check=False)
        if result.returncode in (config.FZF_EXIT_ABORTED, config.FZF_EXIT_NO_MATCH):
            raise AbortedError(messages.ABORTED)
        if result.returncode != 0:
            raise SiError(messages.ERR_FZF_STATUS.format(status=result.returncode))
        sep = config.FZF_FIELD_SEPARATOR
        return [line.split(sep, 1)[0] for line in result.stdout.splitlines() if line]

    @staticmethod
    def _line(row: Row) -> str:
        fields = (row.key, *row.columns, row.preview)
        return config.FZF_FIELD_SEPARATOR.join(f.replace("\t", " ") for f in fields)

    def _command(self, prompt: str, multi: bool, header: str) -> list[str]:
        command = [
            self._binary, "--prompt", f"{prompt} > ", "--height", config.FZF_HEIGHT,
            "--layout", "reverse", "--border", "--delimiter", config.FZF_FIELD_SEPARATOR,
            "--with-nth", "2..-2", "--tabstop", config.FZF_TABSTOP,
        ]
        if multi:
            command += ["--multi", "--bind", "tab:toggle+clear-query+first", "--bind", "change:first",
                        "--preview", "echo {-1}", "--preview-window", "down,3,wrap"]
        if header:
            command += ["--header", header]
        return command
