"""Walks the user through every Initializr option, in the web UI's order."""

from dataclasses import dataclass

from . import config, messages
from .defaults import SELECT_ATTRIBUTES, refresh_derived
from .metadata import Metadata
from .request import ProjectRequest


@dataclass(frozen=True)
class Step:
    attribute: str
    label: str
    is_select: bool


STEPS = (
    Step("type", messages.LABEL_TYPE, True),
    Step("language", messages.LABEL_LANGUAGE, True),
    Step("boot_version", messages.LABEL_BOOT, True),
    Step("group_id", messages.LABEL_GROUP, False),
    Step("artifact_id", messages.LABEL_ARTIFACT, False),
    Step("name", messages.LABEL_NAME, False),
    Step("description", messages.LABEL_DESCRIPTION, False),
    Step("package_name", messages.LABEL_PACKAGE, False),
    Step("packaging", messages.LABEL_PACKAGING, True),
    Step("configuration_file_format", messages.LABEL_CONFIG, True),
    Step("java_version", messages.LABEL_JAVA, True),
)
DERIVED_SOURCES = ("group_id", "artifact_id")
TYPE_ATTRIBUTE = "type"


class Wizard:
    def __init__(self, prompter, metadata: Metadata):
        self._prompter = prompter
        self._metadata = metadata

    def run(self, request: ProjectRequest, fixed: set[str]) -> ProjectRequest:
        """Ask for every option not fixed by a flag; mutates and returns request."""
        for step in STEPS:
            if step.attribute not in fixed:
                setattr(request, step.attribute, self._ask(step, request))
            if step.attribute in DERIVED_SOURCES:
                refresh_derived(request, fixed)
        if "dependencies" not in fixed:
            self._ask_dependencies(request)
        return request

    def _ask(self, step: Step, request: ProjectRequest) -> str:
        current = getattr(request, step.attribute)
        if step.is_select:
            return self._prompter.choose(step.label, self._field(step), current)
        return self._prompter.text(step.label, current)

    def _field(self, step: Step):
        field = self._metadata.selects[SELECT_ATTRIBUTES[step.attribute]]
        if step.attribute == TYPE_ATTRIBUTE:
            # Like the web form, offer only full projects, not bare build files.
            return field.with_tag(config.FORMAT_TAG, config.FORMAT_PROJECT)
        return field

    def _ask_dependencies(self, request: ProjectRequest) -> None:
        available = self._metadata.dependencies_for(request.boot_version)
        request.dependencies = self._prompter.dependencies(available, request.dependencies)

