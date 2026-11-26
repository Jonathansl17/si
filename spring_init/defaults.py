"""Builds the starting request from service defaults plus explicit overrides."""

from . import naming
from .metadata import Metadata
from .request import ProjectRequest

SELECT_ATTRIBUTES = {
    "type": "type",
    "language": "language",
    "boot_version": "bootVersion",
    "packaging": "packaging",
    "configuration_file_format": "configurationFileFormat",
    "java_version": "javaVersion",
}
TEXT_ATTRIBUTES = {
    "group_id": "groupId",
    "artifact_id": "artifactId",
    "description": "description",
    "version": "version",
}
DERIVED_ATTRIBUTES = ("name", "package_name")


def initial_request(metadata: Metadata, overrides: dict) -> ProjectRequest:
    values = {attr: metadata.selects[key].default for attr, key in SELECT_ATTRIBUTES.items()}
    values.update({attr: metadata.text_defaults[key] for attr, key in TEXT_ATTRIBUTES.items()})
    values.update({k: v for k, v in overrides.items() if k not in DERIVED_ATTRIBUTES})
    request = ProjectRequest(name="", package_name="", **values)
    refresh_derived(request, fixed=set(overrides))
    for attr in DERIVED_ATTRIBUTES:
        if attr in overrides:
            setattr(request, attr, overrides[attr])
    return request


def refresh_derived(request: ProjectRequest, fixed: set[str]) -> None:
    """Recompute Name and Package from Group/Artifact unless set explicitly."""
    if "name" not in fixed:
        request.name = naming.project_name(request.artifact_id)
    if "package_name" not in fixed:
        request.package_name = naming.package_name(request.group_id, request.artifact_id)
