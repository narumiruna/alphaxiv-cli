from typing import Annotated

import typer

from axiv.commands import auth_app
from axiv.commands import events_app
from axiv.commands import feed_app
from axiv.commands import library_app
from axiv.commands import paper_app
from axiv.commands import research_app
from axiv.commands import researchers_app
from axiv.commands import search_app
from axiv.commands.common import set_debug

app = typer.Typer(
    name="alphaxiv",
    help="Read alphaXiv through a static, reviewed public REST surface.",
    no_args_is_help=True,
)


@app.callback()
def main(
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Show tracebacks for unexpected internal errors."),
    ] = False,
) -> None:
    """Configure the alphaXiv CLI."""
    set_debug(debug)


app.add_typer(auth_app, name="auth")
app.add_typer(search_app, name="search")
app.add_typer(research_app, name="research")
app.add_typer(library_app, name="library")
app.add_typer(researchers_app, name="researchers")
app.add_typer(events_app, name="events")
app.add_typer(feed_app, name="feed")
app.add_typer(paper_app, name="paper")
