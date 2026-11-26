"""Thin urllib wrapper that turns transport failures into HttpError."""

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from . import config, messages
from .errors import HttpError

ERROR_MESSAGE_KEY = "message"


@dataclass(frozen=True)
class Response:
    body: bytes
    content_disposition: str


class HttpClient:
    def __init__(self, base_url: str, timeout: float = config.HTTP_TIMEOUT_SECONDS):
        self._base_url = base_url
        self._timeout = timeout

    def get_json(self, path: str, accept: str) -> dict:
        url = self._url(path, {})
        response = self._get(url, accept)
        try:
            return json.loads(response.body)
        except ValueError as exc:
            raise HttpError(messages.ERR_BAD_JSON.format(url=url, reason=exc)) from exc

    def get(self, path: str, params: dict[str, str]) -> Response:
        return self._get(self._url(path, params), "*/*")

    def _url(self, path: str, params: dict[str, str]) -> str:
        query = urllib.parse.urlencode(params)
        return f"{self._base_url}{path}" + (f"?{query}" if query else "")

    def _get(self, url: str, accept: str) -> Response:
        headers = {"Accept": accept, "User-Agent": config.USER_AGENT}
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as raw:
                disposition = raw.headers.get("Content-Disposition", "")
                return Response(raw.read(), disposition)
        except urllib.error.HTTPError as exc:
            raise HttpError(messages.ERR_SERVICE.format(reason=_service_reason(exc))) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise HttpError(messages.ERR_HTTP.format(url=url, reason=exc)) from exc


def _service_reason(exc: urllib.error.HTTPError) -> str:
    """Spring Initializr explains 4xx errors in a JSON 'message' field."""
    try:
        payload = json.loads(exc.read())
    except (ValueError, OSError):
        return str(exc)
    if isinstance(payload, dict) and payload.get(ERROR_MESSAGE_KEY):
        return str(payload[ERROR_MESSAGE_KEY])
    return str(exc)
