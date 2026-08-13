from typing import Annotated

import typer

from alphaxiv.clients.public_rest import PublicRestClient
from alphaxiv.commands.common import emit
from alphaxiv.commands.common import run_operation
from alphaxiv.models.events import EventsResponse
from alphaxiv.output import render_table

app = typer.Typer(help="Browse public alphaXiv events.", no_args_is_help=True)


@app.command("list")
def list_events(
    limit: Annotated[int, typer.Option(min=1, max=50, help="Maximum events to print.")] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """List public events."""

    def operation() -> EventsResponse:
        with PublicRestClient() as client:
            result = client.list_events()
        items = result.items[:limit]
        return EventsResponse(items=items, count=len(items))

    result = run_operation(operation)
    emit(
        result,
        json_output=json_output,
        human=lambda: render_table(
            title="Events",
            columns=("Date", "Title", "Speaker", "Organization", "Link"),
            rows=[(item.date, item.title, item.speaker, item.organization, item.link) for item in result.items],
        ),
    )
