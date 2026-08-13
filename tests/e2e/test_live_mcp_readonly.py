import os

import anyio
import pytest

from alphaxiv.clients.mcp import McpClient
from alphaxiv.contracts.mcp import check_mcp_tools
from alphaxiv.models.mcp import ListLibraryArguments

pytestmark = pytest.mark.skipif(
    os.getenv("ALPHAXIV_LIVE") != "1" or not os.getenv("ALPHAXIV_API_KEY"),
    reason="set ALPHAXIV_LIVE=1 and ALPHAXIV_API_KEY to run read-only MCP smoke tests",
)


def test_live_mcp_initialize_tools_and_library_are_structurally_valid() -> None:
    async def scenario() -> None:
        async with McpClient() as client:
            initialized = await client.initialize()
            tools = await client.list_tools()
            library = await client.list_library(ListLibraryArguments())
            detailed_library = await client.list_library(ListLibraryArguments(include_papers=True))
            membership = await client.list_library(ListLibraryArguments(paper_ids_or_urls=("1706.03762",)))

        assert initialized.server_name
        assert check_mcp_tools(tools).compatible is True
        assert isinstance(library.folders, tuple)
        assert all(paper.paper_id for folder in detailed_library.folders for paper in folder.papers)
        assert all(item.paper_id and isinstance(item.folder_ids, tuple) for item in membership.memberships)

    anyio.run(scenario)
