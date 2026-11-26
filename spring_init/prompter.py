"""Interactive prompts: fzf for choices, readline for editable text."""

from . import messages
from .errors import AbortedError
from .fzf import Fzf, Row
from .metadata import Dependency, SelectField

NONE_KEY = "-"
TEXT_PROMPT = "{label}: "


class Prompter:
    def __init__(self, fzf: Fzf, read_line):
        self._fzf = fzf
        self._read_line = read_line

    def choose(self, label: str, field: SelectField, current: str | None) -> str:
        """Single choice; the current value is listed first so ENTER keeps it."""
        ordered = sorted(field.choices, key=lambda c: c.id != current)
        rows = [Row(c.id, (c.name, messages.DEFAULT_MARK if c.id == current else ""))
                for c in ordered]
        return self._fzf.pick(label, rows)[0]

    def text(self, label: str, default: str) -> str:
        try:
            value = self._read_line(TEXT_PROMPT.format(label=label), default)
        except (EOFError, KeyboardInterrupt) as exc:
            raise AbortedError(messages.ABORTED) from exc
        return value.strip() or default

    def dependencies(self, available: list[Dependency], chosen: list[str]) -> list[str]:
        """Fuzzy multi-select. Already chosen ids are listed first."""
        ordered = sorted(available, key=lambda d: d.id not in chosen)
        width = max((len(d.id) for d in ordered), default=0)
        rows = [Row(NONE_KEY, (" " * width, messages.DEPS_NONE, ""), "")]
        rows += [Row(d.id, (d.id.ljust(width), d.name, f"[{d.group}]"), d.description)
                 for d in ordered]
        picked = self._fzf.pick(messages.LABEL_DEPENDENCIES, rows, multi=True,
                                header=messages.DEPS_HEADER)
        return [key for key in picked if key != NONE_KEY]

    def confirm(self, summary: str) -> bool:
        print(summary)
        try:
            answer = input(messages.CONFIRM_GENERATE)
        except (EOFError, KeyboardInterrupt) as exc:
            raise AbortedError(messages.ABORTED) from exc
        return answer.strip().lower() in messages.CONFIRM_YES
