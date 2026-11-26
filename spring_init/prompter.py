"""Interactive prompts. Every prompt accepts 'q' to return to the previous one."""

from . import config, messages
from .errors import AbortedError, GoBack
from .fzf import Fzf, Row
from .metadata import Dependency, SelectField

NONE_KEY = "-"


class Prompter:
    def __init__(self, fzf: Fzf, read_line):
        self._fzf = fzf
        self._read_line = read_line

    def choose(self, label: str, field: SelectField, current: str | None) -> str:
        """Single choice; the current value is listed first so ENTER keeps it."""
        ordered = sorted(field.choices, key=lambda c: c.id != current)
        rows = [Row(c.id, (c.name, messages.DEFAULT_MARK if c.id == current else ""))
                for c in ordered]
        return self._fzf.menu(label, rows, messages.MENU_HEADER)

    def text(self, label: str, default: str) -> str:
        """Free text; empty keeps the default shown in brackets."""
        template = messages.TEXT_PROMPT if default else messages.TEXT_PROMPT_EMPTY
        value = self._ask(template.format(label=label, default=default)).strip()
        return value or default

    def dependencies(self, available: list[Dependency], chosen: list[str]) -> list[str]:
        """Fuzzy multi-select. Already chosen ids are listed first."""
        ordered = sorted(available, key=lambda d: d.id not in chosen)
        width = max((len(d.id) for d in ordered), default=0)
        rows = [Row(NONE_KEY, (" " * width, messages.DEPS_NONE, ""), "")]
        rows += [Row(d.id, (d.id.ljust(width), d.name, f"[{d.group}]"), d.description)
                 for d in ordered]
        marked = tuple(i for i, row in enumerate(rows) if row.key in chosen)
        try:
            picked = self._fzf.search(messages.LABEL_DEPENDENCIES, rows, messages.DEPS_HEADER,
                                      marked)
        except GoBack as back:
            raise GoBack(_real(back.kept or [])) from back
        return _real(picked)

    def confirm(self, summary: str) -> bool:
        print(summary)
        answer = self._ask(messages.CONFIRM_GENERATE).strip().lower()
        return answer in messages.CONFIRM_YES

    def _ask(self, prompt: str) -> str:
        try:
            answer = self._read_line(prompt)
        except (EOFError, KeyboardInterrupt) as exc:
            raise AbortedError(messages.ABORTED) from exc
        if answer.strip() == config.BACK_KEY:
            raise GoBack()
        return answer


def _real(keys: list[str]) -> list[str]:
    return [key for key in keys if key != NONE_KEY]
