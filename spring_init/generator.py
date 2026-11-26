"""Downloads the generated project and writes it under the working directory."""

import re
from pathlib import Path

from . import config, messages
from .errors import ValidationError
from .extract import extract_zip
from .metadata import Metadata
from .request import ProjectRequest, action_path, is_project_archive

_FILENAME = re.compile(r'filename="?([^";]+)"?')


class Generator:
    def __init__(self, client, metadata: Metadata):
        self._client = client
        self._metadata = metadata

    def generate(self, request: ProjectRequest, cwd: Path, here: bool) -> Path:
        """Return the created project directory (or build file)."""
        if is_project_archive(request, self._metadata):
            return self._write_project(request, cwd, here)
        return self._write_build_file(request, cwd)

    def _write_project(self, request: ProjectRequest, cwd: Path, here: bool) -> Path:
        target = cwd if here else cwd / request.artifact_id
        if not here and target.exists():
            raise ValidationError(messages.ERR_TARGET_EXISTS.format(path=target))
        response = self._client.get(action_path(request, self._metadata),
                                    request.to_params(base_dir=""))
        target.mkdir(parents=True, exist_ok=True)
        extract_zip(response.body, target)
        _mark_wrappers_executable(target)
        return target

    def _write_build_file(self, request: ProjectRequest, cwd: Path) -> Path:
        path = action_path(request, self._metadata)
        response = self._client.get(path, request.to_params(base_dir=""))
        destination = cwd / _filename(response.content_disposition, path)
        if destination.exists():
            raise ValidationError(messages.ERR_TARGET_EXISTS.format(path=destination))
        destination.write_bytes(response.body)
        return destination


def _mark_wrappers_executable(target: Path) -> None:
    for name in config.WRAPPER_SCRIPTS:
        wrapper = target / name
        if wrapper.is_file():
            wrapper.chmod(wrapper.stat().st_mode | config.EXECUTABLE_MASK)


def _filename(content_disposition: str, path: str) -> str:
    match = _FILENAME.search(content_disposition)
    name = match.group(1) if match else path.rsplit("/", 1)[-1]
    return Path(name).name
