"""Command-line flags: one per Initializr option, plus behaviour switches."""

import argparse

from . import config, messages
from .request import DEPENDENCY_SEPARATOR

# (flags, request attribute, help text key)
OPTION_FLAGS = (
    (("-t", "--type"), "type", messages.HELP_TYPE),
    (("-l", "--language"), "language", messages.HELP_LANGUAGE),
    (("-b", "--boot"), "boot_version", messages.HELP_BOOT_VERSION),
    (("-g", "--group"), "group_id", messages.HELP_GROUP_ID),
    (("-a", "--artifact"), "artifact_id", messages.HELP_ARTIFACT_ID),
    (("-n", "--name"), "name", messages.HELP_NAME),
    (("--description",), "description", messages.HELP_DESCRIPTION),
    (("-p", "--package"), "package_name", messages.HELP_PACKAGE_NAME),
    (("--packaging",), "packaging", messages.HELP_PACKAGING),
    (("-c", "--config"), "configuration_file_format", messages.HELP_CONFIGURATION_FILE_FORMAT),
    (("-j", "--java"), "java_version", messages.HELP_JAVA_VERSION),
    (("--project-version",), "version", messages.HELP_VERSION),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=config.APP_NAME, description=messages.HELP_APP)
    for flags, attribute, help_text in OPTION_FLAGS:
        parser.add_argument(*flags, dest=attribute, help=help_text)
    parser.add_argument("-d", "--deps", dest="dependencies", help=messages.HELP_DEPS)
    parser.add_argument("-y", "--yes", action="store_true", help=messages.HELP_YES)
    parser.add_argument("--here", action="store_true", help=messages.HELP_HERE)
    parser.add_argument("--list-deps", action="store_true", help=messages.HELP_LIST)
    parser.add_argument("-V", "--version", action="version",
                        version=f"{config.APP_NAME} {config.VERSION}")
    return parser


def overrides(namespace: argparse.Namespace) -> dict:
    """Request attributes the user set explicitly on the command line."""
    values = {attr: getattr(namespace, attr) for _, attr, _ in OPTION_FLAGS
              if getattr(namespace, attr) is not None}
    if namespace.dependencies is not None:
        values["dependencies"] = [dep.strip() for dep in
                                  namespace.dependencies.split(DEPENDENCY_SEPARATOR) if dep.strip()]
    return values
