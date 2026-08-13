from alphaxiv.commands.auth import app as auth_app
from alphaxiv.commands.events import app as events_app
from alphaxiv.commands.feed import app as feed_app
from alphaxiv.commands.library import app as library_app
from alphaxiv.commands.paper import app as paper_app
from alphaxiv.commands.research import app as research_app
from alphaxiv.commands.researchers import app as researchers_app
from alphaxiv.commands.search import app as search_app

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
