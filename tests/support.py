"""Shared test helpers."""

import json
from pathlib import Path

from spring_init.metadata import Metadata, parse_metadata

FIXTURE = Path(__file__).with_name("fixture_metadata.json")


def load_metadata() -> Metadata:
    return parse_metadata(json.loads(FIXTURE.read_text()), str(FIXTURE))
