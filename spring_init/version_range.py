"""Spring Initializr version parsing and range matching.

Ranges follow the Initializr syntax: "1.2.0" means ">= 1.2.0", while
"[1.2.0,2.0.0)" uses inclusive brackets and exclusive parentheses.
"""

import re
from dataclasses import dataclass

from . import messages
from .errors import ValidationError

_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[.-]([A-Za-z][A-Za-z-]*?)(\d*))?$")
_QUALIFIER_RANK = {"M": 1, "RC": 2, "SNAPSHOT": 3, "BUILD-SNAPSHOT": 3, "RELEASE": 4}
_INCLUSIVE_START, _EXCLUSIVE_START = "[", "("
_INCLUSIVE_END, _EXCLUSIVE_END = "]", ")"
_BOUND_SEPARATOR = ","


def parse_version(text: str) -> tuple[int, ...]:
    """Return a tuple that sorts the same way Initializr orders versions."""
    match = _VERSION.match(text.strip())
    if not match:
        raise ValidationError(messages.ERR_BAD_VERSION.format(version=text))
    major, minor, patch, qualifier, number = match.groups()
    rank = _QUALIFIER_RANK.get((qualifier or "RELEASE").upper())
    if rank is None:
        raise ValidationError(messages.ERR_BAD_VERSION.format(version=text))
    return int(major), int(minor), int(patch), rank, int(number or 0)


@dataclass(frozen=True)
class VersionRange:
    lower: tuple[int, ...]
    lower_inclusive: bool
    upper: tuple[int, ...] | None
    upper_inclusive: bool

    def contains(self, version: str) -> bool:
        value = parse_version(version)
        above = value >= self.lower if self.lower_inclusive else value > self.lower
        if self.upper is None:
            return above
        below = value <= self.upper if self.upper_inclusive else value < self.upper
        return above and below


def parse_range(text: str) -> VersionRange:
    raw = text.strip()
    if not raw.startswith((_INCLUSIVE_START, _EXCLUSIVE_START)):
        return VersionRange(parse_version(raw), True, None, False)
    if not raw.endswith((_INCLUSIVE_END, _EXCLUSIVE_END)) or _BOUND_SEPARATOR not in raw:
        raise ValidationError(messages.ERR_BAD_RANGE.format(range=text))
    lower, upper = raw[1:-1].split(_BOUND_SEPARATOR, 1)
    return VersionRange(
        lower=parse_version(lower),
        lower_inclusive=raw[0] == _INCLUSIVE_START,
        upper=parse_version(upper),
        upper_inclusive=raw[-1] == _INCLUSIVE_END,
    )


def is_compatible(version_range: str | None, version: str) -> bool:
    if not version_range:
        return True
    return parse_range(version_range).contains(version)
