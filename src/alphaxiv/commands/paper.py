from collections.abc import Callable
from functools import partial
from typing import Annotated

import typer
from pydantic import BaseModel

from alphaxiv.clients.public_rest import PublicRestClient
from alphaxiv.commands.common import emit
from alphaxiv.commands.common import run_operation
from alphaxiv.errors import InputError
from alphaxiv.models.paper import AIDetectionResponse
from alphaxiv.models.paper import AutoresearchImplementationsResponse
from alphaxiv.models.paper import ExtrasResponse
from alphaxiv.models.paper import FiguresResponse
from alphaxiv.models.paper import FullTextResponse
from alphaxiv.models.paper import ImplementationsResponse
from alphaxiv.models.paper import ModelLinksResponse
from alphaxiv.models.paper import OverviewResponse
from alphaxiv.models.paper import OverviewStatus
from alphaxiv.models.paper import PaperComments
from alphaxiv.models.paper import PaperMetrics
from alphaxiv.models.paper import PaperPreview
from alphaxiv.models.paper import PaperRecord
from alphaxiv.models.paper import RelatedKind
from alphaxiv.models.paper import ResolvedPaperIdentifiers
from alphaxiv.models.paper import SimilarPapers
from alphaxiv.output import render_table
from alphaxiv.output import render_text

app = typer.Typer(help="Read public alphaXiv paper data.", no_args_is_help=True)


def _identifiers(client: PublicRestClient, identifier: str) -> ResolvedPaperIdentifiers:
    return ResolvedPaperIdentifiers.from_record(client.paper(identifier))


def _json_human(model: BaseModel) -> Callable[[], None]:
    return lambda: render_text(model.model_dump_json(indent=2))


def _related_human(kind: RelatedKind, model: BaseModel) -> None:
    if isinstance(model, PaperComments | SimilarPapers):
        summary = f"{model.count} items"
    elif isinstance(model, PaperMetrics):
        summary = f"{model.visits_all} visits, {model.comments_count} comments"
    elif isinstance(model, FiguresResponse):
        summary = f"{len(model.figures)} figures"
    elif isinstance(model, ExtrasResponse):
        summary = model.repo_url or "No repository"
    elif isinstance(model, ImplementationsResponse):
        summary = f"{len(model.alphaxiv_implementations) + len(model.paper_resources)} implementations"
    elif isinstance(model, AutoresearchImplementationsResponse):
        summary = f"{len(model.implementations)} implementations"
    elif isinstance(model, AIDetectionResponse):
        summary = f"{model.state}: {model.headline or 'No headline'}"
    elif isinstance(model, ModelLinksResponse):
        summary = f"{model.state}: {len(model.matches)} matches"
    else:
        summary = "Available"
    render_table(title="Related paper data", columns=("Kind", "Summary"), rows=[(kind.value, summary)])


@app.command("show")
def show(
    identifier: Annotated[str, typer.Argument(help="arXiv ID or alphaXiv paper identifier.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Show paper metadata."""

    def operation() -> PaperRecord:
        with PublicRestClient() as client:
            return client.paper(identifier)

    result = run_operation(operation)
    emit(
        result,
        json_output=json_output,
        human=lambda: render_table(
            title=result.title,
            columns=("Universal ID", "Version", "Group ID", "Published"),
            rows=[
                (
                    result.universal_id,
                    result.version_label,
                    result.group_id,
                    result.publication_date,
                )
            ],
        ),
    )


@app.command("preview")
def preview(
    identifier: Annotated[str, typer.Argument(help="arXiv ID or alphaXiv paper identifier.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Show a compact paper preview."""

    def operation() -> PaperPreview:
        with PublicRestClient() as client:
            return client.paper_preview(identifier)

    result = run_operation(operation)
    emit(
        result,
        json_output=json_output,
        human=lambda: render_table(
            title="Paper preview",
            columns=("Paper ID", "Title", "Authors", "Topics"),
            rows=[
                (
                    result.universal_paper_id,
                    result.title,
                    ", ".join(result.authors),
                    ", ".join(result.topics),
                )
            ],
        ),
    )


@app.command("text")
def text(
    identifier: Annotated[str, typer.Argument(help="arXiv ID or alphaXiv paper identifier.")],
    page: Annotated[int, typer.Option(min=1, max=100_000, help="Page to print in human mode.")] = 1,
    json_output: Annotated[bool, typer.Option("--json", help="Emit all pages as stable JSON.")] = False,
) -> None:
    """Read extracted paper text."""

    def operation() -> FullTextResponse:
        with PublicRestClient() as client:
            ids = _identifiers(client, identifier)
            result = client.paper_full_text(ids.version_id)
        if not any(item.page_number == page for item in result.pages):
            raise InputError(f"paper text does not contain page {page}")
        return result

    result = run_operation(operation)
    emit(
        result,
        json_output=json_output,
        human=lambda: render_text(next(item.text for item in result.pages if item.page_number == page)),
    )


@app.command("overview")
def overview(
    identifier: Annotated[str, typer.Argument(help="arXiv ID or alphaXiv paper identifier.")],
    language: Annotated[str, typer.Option(help="Two-letter lowercase language code.")] = "en",
    status: Annotated[bool, typer.Option("--status", help="Show generation and translation status.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Read an existing paper overview without starting generation."""

    def operation() -> OverviewResponse | OverviewStatus:
        with PublicRestClient() as client:
            ids = _identifiers(client, identifier)
            if status:
                return client.paper_overview_status(ids.version_id)
            return client.paper_overview(ids.version_id, language)

    result = run_operation(operation)
    human = partial(render_text, result.overview) if isinstance(result, OverviewResponse) else _json_human(result)
    emit(result, json_output=json_output, human=human)


@app.command("related")
def related(
    identifier: Annotated[str, typer.Argument(help="arXiv ID or alphaXiv paper identifier.")],
    kind: Annotated[RelatedKind, typer.Option(help="Reviewed related-data resource.")],
    limit: Annotated[int, typer.Option(min=1, max=20, help="Maximum similar papers.")] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Read one reviewed related-data resource."""

    def operation() -> BaseModel:
        with PublicRestClient() as client:
            if kind is RelatedKind.SIMILAR:
                return client.similar_papers(identifier, limit=limit)
            if kind is RelatedKind.METRICS:
                return client.paper_metrics(identifier)
            ids = _identifiers(client, identifier)
            if kind is RelatedKind.COMMENTS:
                return client.paper_comments(ids.group_id)
            if kind is RelatedKind.FIGURES:
                return client.paper_figures(ids.group_id)
            if kind is RelatedKind.EXTRAS:
                return client.paper_extras(ids.group_id)
            if kind is RelatedKind.IMPLEMENTATIONS:
                return client.paper_implementations(ids.group_id)
            if kind is RelatedKind.AUTORESEARCH:
                return client.autoresearch_implementations(ids.group_id)
            if kind is RelatedKind.AI_DETECTION:
                return client.ai_detection(ids.version_id)
            return client.model_links(ids.version_id)

    result = run_operation(operation)
    emit(result, json_output=json_output, human=lambda: _related_human(kind, result))
