"""Human-readable recap shown before generating."""

from . import messages
from .defaults import SELECT_ATTRIBUTES
from .metadata import Metadata
from .request import ProjectRequest
from .wizard import STEPS

LINE = "  {label:<{width}}  {value}"
DEPENDENCY_JOINER = ", "


def render(request: ProjectRequest, metadata: Metadata) -> str:
    rows = [(step.label, _display(step.attribute, request, metadata)) for step in STEPS]
    rows.append((messages.LABEL_DEPENDENCIES, _dependencies(request, metadata)))
    width = max(len(label) for label, _ in rows)
    body = [LINE.format(label=label, width=width, value=value) for label, value in rows]
    return "\n".join([messages.SUMMARY_TITLE, *body])


def _display(attribute: str, request: ProjectRequest, metadata: Metadata) -> str:
    value = getattr(request, attribute)
    if attribute not in SELECT_ATTRIBUTES:
        return value
    choice = metadata.selects[SELECT_ATTRIBUTES[attribute]].find(value)
    return choice.name if choice else value


def _dependencies(request: ProjectRequest, metadata: Metadata) -> str:
    names = {dep.id: dep.name for dep in metadata.dependencies}
    chosen = [names.get(dep_id, dep_id) for dep_id in request.dependencies]
    return DEPENDENCY_JOINER.join(chosen) or messages.DEPS_NONE
