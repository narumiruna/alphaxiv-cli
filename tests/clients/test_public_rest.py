import gzip
import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from pydantic import BaseModel

from axiv.clients.public_rest import PublicRestClient
from axiv.errors import InvalidResponseError
from axiv.errors import NetworkError
from axiv.errors import NotFoundError
from axiv.models.feed import FeedInterval
from axiv.models.feed import FeedSort

FIXTURE = Path(__file__).parents[1] / "fixtures" / "api" / "responses.json"
RESPONSES = json.loads(FIXTURE.read_text())


def make_client(handler: Callable[[httpx.Request], httpx.Response]) -> PublicRestClient:
    http_client = httpx.Client(
        base_url="https://api.alphaxiv.org",
        transport=httpx.MockTransport(handler),
    )
    return PublicRestClient(http_client=http_client)


def test_public_client_never_sends_auth_or_persisted_cookies() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=RESPONSES["events"], headers={"set-cookie": "session=secret"})

    client = make_client(handler)
    client.list_events()
    client.list_events()

    assert len(requests) == 2
    for request in requests:
        assert "authorization" not in request.headers
        assert "cookie" not in request.headers


def test_public_client_rejects_injected_client_with_sensitive_headers() -> None:
    http_client = httpx.Client(
        base_url="https://api.alphaxiv.org",
        headers={"Authorization": "Bearer secret"},
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=[])),
    )

    with pytest.raises(ValueError, match="sensitive headers"):
        PublicRestClient(http_client=http_client)


def test_public_client_rejects_injected_client_that_follows_redirects() -> None:
    http_client = httpx.Client(
        base_url="https://api.alphaxiv.org",
        follow_redirects=True,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=[])),
    )

    with pytest.raises(ValueError, match="redirects"):
        PublicRestClient(http_client=http_client)


def test_search_papers_uses_fixed_route_and_query() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/search/v2/paper/fast"
        assert dict(request.url.params) == {"q": "transformer", "includePrivate": "false"}
        return httpx.Response(200, json=RESPONSES["search_fast"])

    result = make_client(handler).search_papers("transformer")

    assert result.count == 1
    assert result.items[0].paper_id == "1706.03762"


def test_feed_encodes_topics_as_json_and_enforces_fixed_parameters() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/papers/v3/feed"
        assert request.url.params["pageNum"] == "0"
        assert request.url.params["pageSize"] == "5"
        assert request.url.params["sort"] == "Recent"
        assert request.url.params["interval"] == "7 Days"
        assert json.loads(request.url.params["topics"]) == ["agents"]
        return httpx.Response(200, json=RESPONSES["feed"])

    result = make_client(handler).feed(
        page_num=0,
        page_size=5,
        sort=FeedSort.RECENT,
        interval=FeedInterval.SEVEN_DAYS,
        topics=("agents",),
    )

    assert result.papers[0].universal_paper_id == "1706.03762"


def test_paper_identifier_is_encoded_as_one_path_segment() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert b"hep-th%2F9901001" in request.url.raw_path
        return httpx.Response(200, json=RESPONSES["paper"])

    make_client(handler).paper("hep-th/9901001")


@pytest.mark.parametrize(
    ("call", "expected_path", "response_key"),
    [
        (lambda c: c.search_full_text("query", limit=3), "/search/v2/paper/full-text", "search_full_text"),
        (lambda c: c.search_rich_papers("query"), "/v1/search/paper", "search_rich"),
        (lambda c: c.closest_topics("query"), "/v1/search/closest-topic", "closest_topic"),
        (lambda c: c.search_organizations("query"), "/organizations/v2/search", "organizations"),
        (lambda c: c.top_organizations(), "/organizations/v2/top", "organizations"),
        (lambda c: c.list_researchers(offset=24), "/researchers/v1", "researchers"),
        (lambda c: c.search_researchers("query"), "/researchers/v1/search", "researchers"),
        (lambda c: c.list_events(), "/events/v1", "events"),
        (lambda c: c.icml_topics(), "/papers/v3/icml-topics", "topic_groups"),
        (lambda c: c.legacy_paper("1706.03762"), "/papers/v3/legacy/1706.03762", "legacy_paper"),
        (lambda c: c.paper_preview("1706.03762"), "/papers/v3/1706.03762/preview", "preview"),
        (lambda c: c.paper_full_text("version-id"), "/papers/v3/version-id/full-text", "full_text"),
        (lambda c: c.paper_overview("version-id", "en"), "/papers/v3/version-id/overview/en", "overview"),
        (
            lambda c: c.paper_overview_status("version-id"),
            "/papers/v3/version-id/overview/status",
            "overview_status",
        ),
        (lambda c: c.paper_comments("group-id"), "/papers/v3/legacy/group-id/comments", "comments"),
        (lambda c: c.similar_papers("1706.03762", limit=1), "/papers/v3/1706.03762/similar-papers", "similar"),
        (lambda c: c.paper_metrics("1706.03762"), "/papers/v3/1706.03762/metrics", "metrics"),
        (lambda c: c.paper_figures("group-id"), "/papers/v3/group-id/figures", "figures"),
        (lambda c: c.paper_extras("group-id"), "/papers/v3/group-id/extras", "extras"),
        (
            lambda c: c.paper_implementations("group-id"),
            "/papers/v3/group-id/implementations",
            "implementations",
        ),
        (
            lambda c: c.autoresearch_implementations("group-id"),
            "/papers/v3/group-id/autoresearch-implementations",
            "autoresearch",
        ),
        (lambda c: c.ai_detection("version-id"), "/papers/v3/version-id/ai-detection", "ai_detection"),
        (lambda c: c.model_links("version-id"), "/papers/v3/version-id/model-links", "model_links"),
    ],
)
def test_fixed_client_methods_use_only_reviewed_routes(
    call: Callable[[PublicRestClient], BaseModel],
    expected_path: str,
    response_key: str,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == expected_path
        return httpx.Response(200, json=RESPONSES[response_key])

    assert isinstance(call(make_client(handler)), BaseModel)


def test_compressed_response_is_not_decoded_twice() -> None:
    compressed = gzip.compress(json.dumps(RESPONSES["events"]).encode())
    client = make_client(
        lambda _: httpx.Response(
            200,
            content=compressed,
            headers={"content-type": "application/json", "content-encoding": "gzip"},
        )
    )

    result = client.list_events()

    assert result.count == 1


def test_invalid_success_response_is_rejected_without_payload_details() -> None:
    client = make_client(lambda _: httpx.Response(200, json={"unexpected": "secret"}))

    with pytest.raises(InvalidResponseError, match="invalid response"):
        client.search_papers("query")


def test_http_error_is_mapped_to_domain_error() -> None:
    client = make_client(lambda _: httpx.Response(404, json={"error": {"message": "not found"}}))

    with pytest.raises(NotFoundError, match="not found"):
        client.paper("missing")


def test_timeout_is_mapped_to_network_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with pytest.raises(NetworkError, match="network request failed"):
        make_client(handler).list_events()


def test_oversized_response_is_rejected() -> None:
    client = make_client(
        lambda _: httpx.Response(
            200,
            content=b"[" + b" " * (PublicRestClient.MAX_RESPONSE_BYTES + 1) + b"]",
        )
    )

    with pytest.raises(InvalidResponseError, match="too large"):
        client.list_events()
