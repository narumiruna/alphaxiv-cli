from typing import Annotated

import typer

from alphaxiv.clients.public_rest import PublicRestClient
from alphaxiv.commands.common import emit
from alphaxiv.commands.common import run_operation
from alphaxiv.models.researchers import ResearchersResponse
from alphaxiv.output import render_table

app = typer.Typer(help="Browse alphaXiv researcher profiles.", no_args_is_help=True)


def _human(result: ResearchersResponse) -> None:
    render_table(
        title="Researchers",
        columns=("Name", "Slug", "Affiliation", "Citations"),
        rows=[(item.name, item.slug, item.affiliation, item.citations) for item in result.researchers],
    )


@app.command("list")
def list_researchers(
    offset: Annotated[int | None, typer.Option(min=0, max=1_000_000, help="Pagination offset.")] = None,
    limit: Annotated[int, typer.Option(min=1, max=50, help="Maximum results to print.")] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """List researcher profiles."""

    def operation() -> ResearchersResponse:
        with PublicRestClient() as client:
            result = client.list_researchers(offset=offset)
        return ResearchersResponse(
            researchers=result.researchers[:limit],
            nextOffset=result.next_offset,
        )

    result = run_operation(operation)
    emit(result, json_output=json_output, human=lambda: _human(result))


@app.command("search")
def search_researchers(
    query: Annotated[str, typer.Argument(help="Researcher query.")],
    limit: Annotated[int, typer.Option(min=1, max=50, help="Maximum results to print.")] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Search researcher profiles."""

    def operation() -> ResearchersResponse:
        with PublicRestClient() as client:
            result = client.search_researchers(query)
        return ResearchersResponse(researchers=result.researchers[:limit])

    result = run_operation(operation)
    emit(result, json_output=json_output, human=lambda: _human(result))
