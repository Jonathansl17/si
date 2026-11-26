"""Entry point: wires concrete collaborators and maps errors to exit codes."""

import sys
from pathlib import Path

from . import arguments, config, messages, summary
from .defaults import initial_request
from .errors import AbortedError, SiError
from .fzf import Fzf
from .generator import Generator
from .http_client import HttpClient
from .line_input import read_line
from .metadata import Metadata, MetadataSource
from .prompter import Prompter
from .request import validate
from .wizard import Wizard

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_ABORTED = 130
LIST_LINE = "{id:<{width}}  {name}  [{group}]"


def main(argv: list[str] | None = None) -> int:
    namespace = arguments.build_parser().parse_args(argv)
    try:
        return _run(namespace)
    except AbortedError as exc:
        print(exc, file=sys.stderr)
        return EXIT_ABORTED
    except SiError as exc:
        print(f"{config.APP_NAME}: {exc}", file=sys.stderr)
        return EXIT_ERROR


def _run(namespace) -> int:
    client = HttpClient(config.SERVICE_URL)
    print(messages.FETCHING.format(url=config.SERVICE_URL), file=sys.stderr)
    metadata = MetadataSource(client).load()
    overrides = arguments.overrides(namespace)
    request = initial_request(metadata, overrides)
    if namespace.list_deps:
        _list_dependencies(metadata, request.boot_version)
        return EXIT_OK
    if not namespace.yes:
        prompter = Prompter(Fzf(), read_line)
        Wizard(prompter, metadata).run(request, fixed=set(overrides))
        validate(request, metadata)
        if not prompter.confirm(summary.render(request, metadata)):
            raise AbortedError(messages.ABORTED)
    validate(request, metadata)
    print(messages.DOWNLOADING, file=sys.stderr)
    created = Generator(client, metadata).generate(request, Path.cwd(), namespace.here)
    print(messages.CREATED.format(path=created))
    if created.is_dir() and not namespace.here:
        print(messages.DONE_HINT.format(path=created.name))
    return EXIT_OK


def _list_dependencies(metadata: Metadata, boot_version: str) -> None:
    deps = metadata.dependencies_for(boot_version)
    width = max((len(dep.id) for dep in deps), default=0)
    for dep in deps:
        print(LIST_LINE.format(id=dep.id, width=width, name=dep.name, group=dep.group))
