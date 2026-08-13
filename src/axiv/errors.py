import unicodedata
from enum import IntEnum

import httpx
from pydantic import ValidationError


class ExitCode(IntEnum):
    OK = 0
    USAGE = 2
    PERMISSION = 3
    NOT_FOUND = 4
    RATE_LIMIT = 5
    REMOTE = 6
    NETWORK = 7


def _safe_message(value: object, *, fallback: str = "alphaXiv request failed") -> str:
    if not isinstance(value, str):
        return fallback
    sanitized = "".join(" " if unicodedata.category(character) == "Cc" else character for character in value)
    sanitized = " ".join(sanitized.split())
    return (sanitized or fallback)[:500]


class AlphaXivError(Exception):
    code = "alphaxiv_error"
    exit_code = ExitCode.REMOTE

    def __init__(self, message: str) -> None:
        self.message = _safe_message(message)
        super().__init__(self.message)


class InputError(AlphaXivError):
    code = "invalid_input"
    exit_code = ExitCode.USAGE


class RemoteAPIError(AlphaXivError):
    code = "remote_error"
    exit_code = ExitCode.REMOTE


class PermissionDeniedError(RemoteAPIError):
    code = "permission_denied"
    exit_code = ExitCode.PERMISSION


class NotFoundError(RemoteAPIError):
    code = "not_found"
    exit_code = ExitCode.NOT_FOUND


class RateLimitError(RemoteAPIError):
    code = "rate_limited"
    exit_code = ExitCode.RATE_LIMIT


class ToolDriftError(RemoteAPIError):
    code = "tool_drift"


class InvalidResponseError(RemoteAPIError):
    code = "invalid_response"

    @classmethod
    def from_validation_error(cls, _error: ValidationError) -> "InvalidResponseError":
        return cls("alphaXiv returned an invalid response")


class NetworkError(AlphaXivError):
    code = "network_error"
    exit_code = ExitCode.NETWORK


def _response_message(response: httpx.Response) -> str:
    fallback = f"alphaXiv request failed with HTTP {response.status_code}"
    try:
        payload = response.json()
    except ValueError:
        return fallback
    if not isinstance(payload, dict):
        return fallback
    error = payload.get("error")
    if isinstance(error, dict):
        return _safe_message(error.get("message"), fallback=fallback)
    if isinstance(error, str):
        return _safe_message(error, fallback=fallback)
    return _safe_message(payload.get("message"), fallback=fallback)


def map_http_error(response: httpx.Response) -> AlphaXivError:
    message = _response_message(response)
    if response.status_code in {401, 403}:
        return PermissionDeniedError(message)
    if response.status_code == 404:
        return NotFoundError(message)
    if response.status_code == 429:
        return RateLimitError(message)
    if response.status_code == 400:
        return InputError(message)
    return RemoteAPIError(message)
