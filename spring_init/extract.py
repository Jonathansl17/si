"""Safe zip extraction that keeps executable bits (mvnw, gradlew)."""

import io
import zipfile
from pathlib import Path

from . import config, messages
from .errors import UnsafeArchiveError, ValidationError


def extract_zip(data: bytes, target: Path) -> list[Path]:
    """Extract into target, refusing path traversal and existing files."""
    root = target.resolve()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = [(info, _destination(root, info.filename)) for info in archive.infolist()]
        _refuse_existing(entries)
        for info, destination in entries:
            _write_entry(archive, info, destination)
    return [destination for info, destination in entries if not info.is_dir()]


def _destination(root: Path, name: str) -> Path:
    destination = (root / name).resolve()
    if destination != root and root not in destination.parents:
        raise UnsafeArchiveError(messages.ERR_UNSAFE_ENTRY.format(entry=name))
    return destination


def _refuse_existing(entries: list[tuple[zipfile.ZipInfo, Path]]) -> None:
    for info, destination in entries:
        if not info.is_dir() and destination.exists():
            raise ValidationError(messages.ERR_TARGET_EXISTS.format(path=destination))


def _write_entry(archive: zipfile.ZipFile, info: zipfile.ZipInfo, destination: Path) -> None:
    if info.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(archive.read(info))
    mode = info.external_attr >> config.UNIX_MODE_SHIFT
    if mode & config.EXECUTABLE_MASK:
        destination.chmod(destination.stat().st_mode | (mode & config.EXECUTABLE_MASK))
