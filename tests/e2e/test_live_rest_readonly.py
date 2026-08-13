import os

import pytest

from alphaxiv.clients.public_rest import PublicRestClient

pytestmark = pytest.mark.skipif(
    os.getenv("ALPHAXIV_LIVE") != "1",
    reason="set ALPHAXIV_LIVE=1 to run anonymous alphaXiv smoke tests",
)


def test_live_search_and_paper_reads_are_structurally_valid() -> None:
    with PublicRestClient() as client:
        search = client.search_papers("transformer")
        paper = client.paper("1706.03762")
        preview = client.paper_preview("1706.03762")

    assert search.count >= 1
    assert paper.universal_id == "1706.03762"
    assert preview.universal_paper_id == "1706.03762"


def test_live_feed_is_bounded_and_structurally_valid() -> None:
    with PublicRestClient() as client:
        feed = client.feed(page_size=1)

    assert feed.page == 0
    assert len(feed.papers) <= 1
