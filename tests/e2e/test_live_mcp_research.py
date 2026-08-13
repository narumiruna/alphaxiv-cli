import os

import anyio
import pytest

from alphaxiv.clients.mcp import McpClient
from alphaxiv.models.mcp import GetPaperContentArguments

pytestmark = pytest.mark.skipif(
    os.getenv("ALPHAXIV_LIVE_RESEARCH") != "1" or not os.getenv("ALPHAXIV_API_KEY"),
    reason="set ALPHAXIV_LIVE_RESEARCH=1 and ALPHAXIV_API_KEY to spend quota on one MCP research smoke test",
)


def test_live_mcp_research_reads_one_known_paper() -> None:
    print("WARNING: this live alphaXiv MCP research test consumes Assistant quota.")

    async def scenario() -> None:
        async with McpClient() as client:
            await client.initialize()
            result = await client.get_paper_content(GetPaperContentArguments(url="https://arxiv.org/abs/1706.03762"))
        assert result.text.strip()

    anyio.run(scenario)
