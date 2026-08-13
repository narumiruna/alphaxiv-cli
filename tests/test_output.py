import json

import httpx
import pytest
from pydantic import ValidationError
from rich.console import Console

from alphaxiv.errors import ExitCode
from alphaxiv.errors import InvalidResponseError
from alphaxiv.errors import NotFoundError
from alphaxiv.errors import PermissionDeniedError
from alphaxiv.errors import RateLimitError
from alphaxiv.errors import RemoteAPIError
from alphaxiv.errors import map_http_error
from alphaxiv.models.search import PaperSearchResult
from alphaxiv.models.search import PaperSearchResults
from alphaxiv.output import render_error
from alphaxiv.output import render_json
from alphaxiv.output import render_table
from alphaxiv.output import render_text


def make_response(status_code: int, payload: object) -> httpx.Response:
    request = httpx.Request("GET", "https://api.alphaxiv.org/test")
    return httpx.Response(status_code, request=request, json=payload)


@pytest.mark.parametrize(
    ("status", "error_type", "exit_code"),
    [
        (401, PermissionDeniedError, ExitCode.PERMISSION),
        (403, PermissionDeniedError, ExitCode.PERMISSION),
        (404, NotFoundError, ExitCode.NOT_FOUND),
        (429, RateLimitError, ExitCode.RATE_LIMIT),
        (500, RemoteAPIError, ExitCode.REMOTE),
    ],
)
def test_http_errors_map_to_stable_types_and_exit_codes(
    status: int,
    error_type: type[RemoteAPIError],
    exit_code: ExitCode,
) -> None:
    error = map_http_error(make_response(status, {"error": {"message": "safe message"}}))

    assert isinstance(error, error_type)
    assert error.exit_code == exit_code
    assert str(error) == "safe message"


def test_http_error_message_is_bounded_and_control_characters_are_removed() -> None:
    error = map_http_error(make_response(500, {"error": {"message": "secret\n" + "x" * 1000}}))

    assert "\n" not in str(error)
    assert len(str(error)) <= 500


def test_invalid_success_payload_has_stable_remote_error() -> None:
    error = InvalidResponseError.from_validation_error(
        ValidationError.from_exception_data("test", []),
    )

    assert "invalid response" in str(error).lower()
    assert error.exit_code == ExitCode.REMOTE
    assert "Traceback" not in str(error)


def test_json_output_uses_stable_snake_case_fields() -> None:
    result = PaperSearchResults(
        items=[PaperSearchResult(paperId="1706.03762", title="Attention")],
        count=1,
    )
    console = Console(record=True, width=120)

    render_json(result, console=console)
    payload = json.loads(console.export_text())

    assert payload["items"][0]["paper_id"] == "1706.03762"
    assert payload["count"] == 1


def test_json_output_does_not_wrap_long_strings() -> None:
    result = PaperSearchResults(
        items=[PaperSearchResult(paperId="1706.03762", title="x" * 500)],
        count=1,
    )
    console = Console(record=True, width=20)

    render_json(result, console=console)

    assert json.loads(console.export_text())["items"][0]["title"] == "x" * 500


def test_human_output_removes_terminal_control_characters_and_does_not_parse_markup() -> None:
    text_console = Console(record=True, width=120)
    table_console = Console(record=True, width=120)

    render_text("safe\x1b[31mevil", console=text_console)
    render_table(
        title="[bold]Results[/bold]\x1b[2J",
        columns=("Title",),
        rows=(("[bold]literal[/bold]\x1b[2J",),),
        console=table_console,
    )

    text_output = text_console.export_text()
    table_output = table_console.export_text()
    assert "\x1b" not in text_output
    assert "\x1b" not in table_output
    assert "[bold]Results[/bold]" in table_output
    assert "[bold]literal[/bold]" in table_output


def test_error_output_goes_to_stderr_without_traceback() -> None:
    console = Console(record=True, stderr=True, width=120)

    render_error(NotFoundError("paper not found"), console=console)
    output = console.export_text()

    assert "paper not found" in output
    assert "Traceback" not in output
