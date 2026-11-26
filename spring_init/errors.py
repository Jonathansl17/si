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


class GoBack(SiError):
    """The user asked to return to the previous prompt.

    `kept` carries a partial answer worth keeping (marked dependencies), or None.
    """

    def __init__(self, kept=None):
        super().__init__()
        self.kept = kept
