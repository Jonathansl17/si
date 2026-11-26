"""Walks the user through the start.spring.io form, field by field, in its order.

Name and Description are not on the form either; they stay flag-only.

Each prompt may raise GoBack; the wizard then re-asks the previous prompt.
"""

from dataclasses import dataclass

from . import config, messages
from .defaults import SELECT_ATTRIBUTES, refresh_derived
from .errors import AbortedError, GoBack
from .metadata import Metadata
from .request import ProjectRequest

SELECT, TEXT, DEPENDENCIES, CONFIRM = "select", "text", "dependencies", "confirm"


@dataclass(frozen=True)
class Step:
    attribute: str
    label: str
    kind: str


STEPS = (
    Step("type", messages.LABEL_TYPE, SELECT),
    Step("language", messages.LABEL_LANGUAGE, SELECT),
    Step("boot_version", messages.LABEL_BOOT, SELECT),
    Step("group_id", messages.LABEL_GROUP, TEXT),
    Step("artifact_id", messages.LABEL_ARTIFACT, TEXT),
    Step("package_name", messages.LABEL_PACKAGE, TEXT),
    Step("packaging", messages.LABEL_PACKAGING, SELECT),
    Step("configuration_file_format", messages.LABEL_CONFIG, SELECT),
    Step("java_version", messages.LABEL_JAVA, SELECT),
)
DEPENDENCIES_STEP = Step("dependencies", messages.LABEL_DEPENDENCIES, DEPENDENCIES)
CONFIRM_STEP = Step("confirm", messages.SUMMARY_TITLE, CONFIRM)
DERIVED_SOURCES = ("group_id", "artifact_id")
TYPE_ATTRIBUTE = "type"


class Wizard:
    def __init__(self, prompter, metadata: Metadata, render_summary):
        self._prompter = prompter
        self._metadata = metadata
        self._render_summary = render_summary

    def run(self, request: ProjectRequest, fixed: set[str]) -> ProjectRequest:
        """Ask every option not fixed by a flag, then confirm; mutates request."""
        steps = [s for s in (*STEPS, DEPENDENCIES_STEP) if s.attribute not in fixed]
        steps.append(CONFIRM_STEP)
        index = 0
        while index < len(steps):
            try:
                self._apply(steps[index], request, fixed)
                index += 1
            except GoBack as back:
                if back.kept is not None:
                    setattr(request, steps[index].attribute, back.kept)
                index = max(index - 1, 0)
        return request

    def _apply(self, step: Step, request: ProjectRequest, fixed: set[str]) -> None:
        if step.kind == CONFIRM:
            if not self._prompter.confirm(self._render_summary(request)):
                raise AbortedError(messages.ABORTED)
            return
        setattr(request, step.attribute, self._ask(step, request))
        if step.attribute in DERIVED_SOURCES:
            refresh_derived(request, fixed)

    def _ask(self, step: Step, request: ProjectRequest):
        current = getattr(request, step.attribute)
        if step.kind == SELECT:
            return self._prompter.choose(step.label, self._field(step), current)
        if step.kind == DEPENDENCIES:
            available = self._metadata.dependencies_for(request.boot_version)
            return self._prompter.dependencies(available, current)
        return self._prompter.text(step.label, current)

    def _field(self, step: Step):
        field = self._metadata.selects[SELECT_ATTRIBUTES[step.attribute]]
        if step.attribute == TYPE_ATTRIBUTE:
            # Like the web form, offer only full projects, not bare build files.
            return field.with_tag(config.FORMAT_TAG, config.FORMAT_PROJECT)
        return field
