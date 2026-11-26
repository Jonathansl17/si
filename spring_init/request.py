"""The user's choices and their translation into Initializr query parameters."""

from dataclasses import dataclass, field

from . import config, messages
from .errors import ValidationError
from .metadata import Metadata

DEPENDENCY_SEPARATOR = ","


@dataclass
class ProjectRequest:
    type: str
    language: str
    boot_version: str
    group_id: str
    artifact_id: str
    name: str
    description: str
    package_name: str
    packaging: str
    configuration_file_format: str
    java_version: str
    version: str
    dependencies: list[str] = field(default_factory=list)

    def selects(self) -> dict[str, str]:
        return {
            "type": self.type,
            "language": self.language,
            "bootVersion": self.boot_version,
            "packaging": self.packaging,
            "configurationFileFormat": self.configuration_file_format,
            "javaVersion": self.java_version,
        }

    def to_params(self, base_dir: str) -> dict[str, str]:
        texts = {
            "groupId": self.group_id,
            "artifactId": self.artifact_id,
            "name": self.name,
            "description": self.description,
            "packageName": self.package_name,
            "version": self.version,
            "dependencies": DEPENDENCY_SEPARATOR.join(self.dependencies),
        }
        params = {**self.selects(), **{k: v for k, v in texts.items() if v}}
        params[config.BASE_DIR_PARAM] = base_dir
        return params


def validate(request: ProjectRequest, metadata: Metadata) -> None:
    """Fail before the network round-trip when a choice cannot be generated."""
    for field_name, value in request.selects().items():
        select = metadata.selects[field_name]
        if value not in select.ids():
            raise ValidationError(messages.ERR_UNKNOWN_CHOICE.format(
                field=field_name, value=value, valid=", ".join(select.ids())))
    _validate_dependencies(request, metadata)


def _validate_dependencies(request: ProjectRequest, metadata: Metadata) -> None:
    known = {dep.id: dep for dep in metadata.dependencies}
    unknown = [dep_id for dep_id in request.dependencies if dep_id not in known]
    if unknown:
        raise ValidationError(messages.ERR_UNKNOWN_DEPS.format(ids=", ".join(unknown)))
    incompatible = [dep_id for dep_id in request.dependencies
                    if not known[dep_id].supports(request.boot_version)]
    if incompatible:
        raise ValidationError(messages.ERR_INCOMPATIBLE_DEPS.format(
            boot=request.boot_version, ids=", ".join(incompatible)))


def is_project_archive(request: ProjectRequest, metadata: Metadata) -> bool:
    """Build-only types (Maven POM, Gradle Config) return a single file, not a zip."""
    choice = metadata.selects["type"].find(request.type)
    return choice is not None and choice.tags.get(config.FORMAT_TAG) == config.FORMAT_PROJECT


def action_path(request: ProjectRequest, metadata: Metadata) -> str:
    """Endpoint for the chosen type, e.g. /starter.zip or /pom.xml."""
    return metadata.selects["type"].find(request.type).action
