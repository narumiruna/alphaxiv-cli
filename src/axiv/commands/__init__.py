from axiv.commands.auth import app as auth_app
from axiv.commands.events import app as events_app
from axiv.commands.feed import app as feed_app
from axiv.commands.library import app as library_app
from axiv.commands.paper import app as paper_app
from axiv.commands.research import app as research_app
from axiv.commands.researchers import app as researchers_app
from axiv.commands.search import app as search_app

__all__ = [
    "auth_app",
    "events_app",
    "feed_app",
    "library_app",
    "paper_app",
    "research_app",
    "researchers_app",
    "search_app",
]
