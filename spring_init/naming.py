"""Derived defaults that the web UI computes as you type."""

import re

from . import config

_INVALID_PACKAGE_CHARS = re.compile(r"[^a-z0-9_.]")
_REPEATED_DOTS = re.compile(r"\.{2,}")
_DIGIT_START = re.compile(r"(^|\.)(\d)")
_DIGIT_PREFIX = "_"


def package_name(group_id: str, artifact_id: str) -> str:
    """Mirror start.spring.io: '<group>.<artifact>', lowercased, invalid chars dropped."""
    raw = f"{group_id}{config.PACKAGE_SEPARATOR}{artifact_id}".lower()
    cleaned = _INVALID_PACKAGE_CHARS.sub("", raw)
    cleaned = _REPEATED_DOTS.sub(config.PACKAGE_SEPARATOR, cleaned).strip(config.PACKAGE_SEPARATOR)
    return _DIGIT_START.sub(lambda m: f"{m.group(1)}{_DIGIT_PREFIX}{m.group(2)}", cleaned)


def project_name(artifact_id: str) -> str:
    """The web UI defaults Name to the artifact id."""
    return artifact_id
