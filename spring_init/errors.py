"""Domain errors. Every failure the user can hit maps to one of these."""


class SiError(Exception):
    """Base class for errors reported to the user without a traceback."""


class AbortedError(SiError):
    """The user cancelled an interactive prompt."""


class HttpError(SiError):
    """Network or protocol failure talking to the service."""


class ValidationError(SiError):
    """A requested option is not offered by the service."""


class UnsafeArchiveError(SiError):
    """The downloaded archive would write outside the target directory."""
