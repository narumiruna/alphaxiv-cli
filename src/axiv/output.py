import unicodedata
from collections.abc import Sequence

from pydantic import BaseModel
from rich.console import Console
from rich.table import Table
from rich.text import Text

from axiv.errors import AlphaXivError
from axiv.models.common import ErrorDetail
from axiv.models.common import ErrorEnvelope


def render_json(model: BaseModel, *, console: Console | None = None) -> None:
    target = console or Console()
    target.print(
        model.model_dump_json(indent=2),
        markup=False,
        highlight=False,
        soft_wrap=True,
    )


def render_error(error: AlphaXivError, *, console: Console | None = None) -> None:
    target = console or Console(stderr=True)
    envelope = ErrorEnvelope(error=ErrorDetail(code=error.code, message=str(error)))
    target.print(
        envelope.model_dump_json(indent=2),
        markup=False,
        highlight=False,
        soft_wrap=True,
    )


def _safe_human_text(value: object, *, maximum: int | None = None) -> str:
    text = str(value) if value is not None else ""
    sanitized = "".join(
        character if character in {"\n", "\t"} or unicodedata.category(character) != "Cc" else " " for character in text
    )
    return sanitized if maximum is None else sanitized[:maximum]


def render_table(
    *,
    title: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[object]],
    console: Console | None = None,
) -> None:
    target = console or Console()
    table = Table(title=Text(_safe_human_text(title, maximum=500)))
    for column in columns:
        table.add_column(_safe_human_text(column, maximum=100))
    for row in rows:
        table.add_row(*(Text(_safe_human_text(value, maximum=1_000)) for value in row))
    target.print(table)


def render_text(text: str, *, console: Console | None = None) -> None:
    target = console or Console()
    target.print(Text(_safe_human_text(text)))
