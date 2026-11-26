"""Static configuration: endpoints, protocol details, and UI tuning."""

import os

APP_NAME = "si"
VERSION = "0.1.0"

SERVICE_URL_ENV = "SI_SERVICE_URL"
DEFAULT_SERVICE_URL = "https://start.spring.io"
SERVICE_URL = os.environ.get(SERVICE_URL_ENV, DEFAULT_SERVICE_URL).rstrip("/")

METADATA_ACCEPT = "application/vnd.initializr.v2.3+json"
USER_AGENT = f"{APP_NAME}/{VERSION}"
HTTP_TIMEOUT_SECONDS = 30

FZF_BINARY = "fzf"
FZF_EXIT_NO_MATCH = 1
FZF_EXIT_ABORTED = 130
FZF_HEIGHT = "60%"
FZF_FIELD_SEPARATOR = "\t"
FZF_TABSTOP = "2"
FZF_SHELL = "sh -c"

BACK_KEY = "q"
BACK_SENTINEL = "<si:back>"

FORMAT_TAG = "format"
FORMAT_PROJECT = "project"
BASE_DIR_PARAM = "baseDir"
EXECUTABLE_MASK = 0o111
UNIX_MODE_SHIFT = 16
# The service ships build wrappers without the executable bit.
WRAPPER_SCRIPTS = ("mvnw", "gradlew")

PACKAGE_SEPARATOR = "."
