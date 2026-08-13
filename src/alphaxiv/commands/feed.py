from typing import Annotated

import typer

from alphaxiv.clients.public_rest import PublicRestClient
from alphaxiv.commands.common import emit
from alphaxiv.commands.common import run_operation
from alphaxiv.models.feed import FeedInterval
from alphaxiv.models.feed import FeedResponse
from alphaxiv.models.feed import FeedSort
from alphaxiv.models.feed import TopicGroupsResponse
from alphaxiv.output import render_table

app = typer.Typer(help="Browse public alphaXiv paper feeds.", no_args_is_help=True)


@app.command("list")
def list_feed(
    page: Annotated[int, typer.Option(min=0, max=10_000, help="Zero-based feed page.")] = 0,
    limit: Annotated[int, typer.Option(min=1, max=50, help="Papers per page.")] = 10,
    sort: Annotated[FeedSort, typer.Option(case_sensitive=False, help="Feed ordering.")] = FeedSort.HOT,
    interval: Annotated[
        FeedInterval,
        typer.Option(case_sensitive=False, help="Ranking time window."),
    ] = FeedInterval.THIRTY_DAYS,
    topic: Annotated[list[str] | None, typer.Option("--topic", help="Repeat to filter by topic.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """List papers from the public feed."""

    def operation() -> FeedResponse:
        with PublicRestClient() as client:
            return client.feed(
                page_num=page,
                page_size=limit,
                sort=sort,
                interval=interval,
                topics=tuple(topic or ()),
            )

    result = run_operation(operation)
    emit(
        result,
        json_output=json_output,
        human=lambda: render_table(
            title=f"Paper feed — page {result.page}",
            columns=("Paper ID", "Title", "Published"),
            rows=[(item.universal_paper_id, item.title, item.publication_date) for item in result.papers],
        ),
    )


@app.command("topics")
def list_topics(
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """List ICML topic groups."""

    def operation() -> TopicGroupsResponse:
        with PublicRestClient() as client:
            return client.icml_topics()

    result = run_operation(operation)
    emit(
        result,
        json_output=json_output,
        human=lambda: render_table(
            title="ICML topics",
            columns=("Group", "Count"),
            rows=[(item.group, item.count) for item in result.topic_groups],
        ),
    )
