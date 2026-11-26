"""Typed view of the Initializr metadata document (v2.3)."""

from dataclasses import dataclass, field

from . import config, messages
from .errors import HttpError
from .version_range import is_compatible

SELECT_FIELDS = ("type", "language", "bootVersion", "packaging",
                 "configurationFileFormat", "javaVersion")
TEXT_FIELDS = ("groupId", "artifactId", "name", "description", "packageName", "version")


@dataclass(frozen=True)
class Choice:
    id: str
    name: str
    description: str = ""
    tags: dict = field(default_factory=dict)
    action: str = ""


@dataclass(frozen=True)
class SelectField:
    choices: tuple[Choice, ...]
    default: str | None

    def ids(self) -> list[str]:
        return [choice.id for choice in self.choices]

    def find(self, choice_id: str) -> Choice | None:
        return next((c for c in self.choices if c.id == choice_id), None)

    def with_tag(self, tag: str, value: str) -> "SelectField":
        return SelectField(tuple(c for c in self.choices if c.tags.get(tag) == value),
                           self.default)


@dataclass(frozen=True)
class Dependency:
    id: str
    name: str
    description: str
    group: str
    version_range: str | None

    def supports(self, boot_version: str) -> bool:
        return is_compatible(self.version_range, boot_version)


@dataclass(frozen=True)
class Metadata:
    selects: dict[str, SelectField]
    text_defaults: dict[str, str]
    dependencies: tuple[Dependency, ...]

    def dependencies_for(self, boot_version: str) -> list[Dependency]:
        return [dep for dep in self.dependencies if dep.supports(boot_version)]


def parse_metadata(document: dict, source: str) -> Metadata:
    try:
        return Metadata(
            selects={name: _parse_select(document[name]) for name in SELECT_FIELDS},
            text_defaults={name: document.get(name, {}).get("default") or ""
                           for name in TEXT_FIELDS},
            dependencies=tuple(_parse_dependencies(document["dependencies"])),
        )
    except (KeyError, TypeError, AttributeError) as exc:
        raise HttpError(messages.ERR_BAD_JSON.format(url=source, reason=exc)) from exc


def _parse_select(node: dict) -> SelectField:
    choices = tuple(
        Choice(v["id"], v.get("name") or v["id"], v.get("description", ""),
               v.get("tags", {}), v.get("action", ""))
        for v in node["values"]
    )
    return SelectField(choices, node.get("default"))


def _parse_dependencies(node: dict) -> list[Dependency]:
    return [
        Dependency(dep["id"], dep.get("name") or dep["id"], dep.get("description", ""),
                   group["name"], dep.get("versionRange"))
        for group in node["values"]
        for dep in group["values"]
    ]


class MetadataSource:
    """Loads metadata through an injected HTTP client."""

    def __init__(self, client):
        self._client = client

    def load(self) -> Metadata:
        document = self._client.get_json("", config.METADATA_ACCEPT)
        return parse_metadata(document, config.SERVICE_URL)
