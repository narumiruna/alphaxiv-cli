import string
from enum import StrEnum
from typing import Literal

from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from alphaxiv.models.common import StrictModel

API_BASE_URL = "https://api.alphaxiv.org"


class EndpointName(StrEnum):
    SEARCH_FAST = "search_fast"
    SEARCH_FULL_TEXT = "search_full_text"
    SEARCH_RICH = "search_rich"
    CLOSEST_TOPIC = "closest_topic"
    SEARCH_ORGANIZATIONS = "search_organizations"
    TOP_ORGANIZATIONS = "top_organizations"
    LIST_RESEARCHERS = "list_researchers"
    SEARCH_RESEARCHERS = "search_researchers"
    LIST_EVENTS = "list_events"
    FEED = "feed"
    ICML_TOPICS = "icml_topics"
    LEGACY_PAPER = "legacy_paper"
    PAPER = "paper"
    PAPER_PREVIEW = "paper_preview"
    PAPER_FULL_TEXT = "paper_full_text"
    PAPER_OVERVIEW = "paper_overview"
    PAPER_OVERVIEW_STATUS = "paper_overview_status"
    PAPER_COMMENTS = "paper_comments"
    SIMILAR_PAPERS = "similar_papers"
    PAPER_METRICS = "paper_metrics"
    PAPER_FIGURES = "paper_figures"
    PAPER_EXTRAS = "paper_extras"
    PAPER_IMPLEMENTATIONS = "paper_implementations"
    AUTORESEARCH_IMPLEMENTATIONS = "autoresearch_implementations"
    AI_DETECTION = "ai_detection"
    MODEL_LINKS = "model_links"


class RestEndpoint(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: EndpointName
    method: Literal["GET"] = "GET"
    path: str
    auth_mode: Literal["anonymous"] = "anonymous"
    required_path_params: tuple[str, ...] = ()
    required_query_params: tuple[str, ...] = ()
    optional_query_params: tuple[str, ...] = ()
    purpose: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_contract(self) -> "RestEndpoint":
        placeholders = tuple(
            field_name for _, field_name, _, _ in string.Formatter().parse(self.path) if field_name is not None
        )
        if set(placeholders) != set(self.required_path_params):
            msg = f"path placeholders do not match required parameters for {self.name}"
            raise ValueError(msg)
        all_query = (*self.required_query_params, *self.optional_query_params)
        if len(all_query) != len(set(all_query)):
            msg = f"query parameters must be unique for {self.name}"
            raise ValueError(msg)
        return self


def _endpoint(
    name: EndpointName,
    path: str,
    purpose: str,
    *,
    path_params: tuple[str, ...] = (),
    query: tuple[str, ...] = (),
    optional_query: tuple[str, ...] = (),
) -> RestEndpoint:
    return RestEndpoint(
        name=name,
        path=path,
        purpose=purpose,
        required_path_params=path_params,
        required_query_params=query,
        optional_query_params=optional_query,
    )


ENDPOINTS: dict[EndpointName, RestEndpoint] = {
    endpoint.name: endpoint
    for endpoint in (
        _endpoint(
            EndpointName.SEARCH_FAST,
            "/search/v2/paper/fast",
            "Fast paper search",
            query=("q", "includePrivate"),
        ),
        _endpoint(
            EndpointName.SEARCH_FULL_TEXT,
            "/search/v2/paper/full-text",
            "Full-text paper search",
            query=("q",),
            optional_query=("limit",),
        ),
        _endpoint(EndpointName.SEARCH_RICH, "/v1/search/paper", "Rich paper search", query=("q",)),
        _endpoint(EndpointName.CLOSEST_TOPIC, "/v1/search/closest-topic", "Topic suggestions", query=("input",)),
        _endpoint(EndpointName.SEARCH_ORGANIZATIONS, "/organizations/v2/search", "Organization search", query=("q",)),
        _endpoint(EndpointName.TOP_ORGANIZATIONS, "/organizations/v2/top", "Top organizations"),
        _endpoint(
            EndpointName.LIST_RESEARCHERS,
            "/researchers/v1",
            "Researcher directory",
            optional_query=("offset",),
        ),
        _endpoint(EndpointName.SEARCH_RESEARCHERS, "/researchers/v1/search", "Researcher search", query=("q",)),
        _endpoint(EndpointName.LIST_EVENTS, "/events/v1", "Public events"),
        _endpoint(
            EndpointName.FEED,
            "/papers/v3/feed",
            "Paper feed",
            query=("pageNum", "pageSize", "sort", "interval"),
            optional_query=("source", "runnable", "topics", "universalId", "includeExternalBlogs"),
        ),
        _endpoint(EndpointName.ICML_TOPICS, "/papers/v3/icml-topics", "ICML topic groups"),
        _endpoint(
            EndpointName.LEGACY_PAPER,
            "/papers/v3/legacy/{unresolved}",
            "Legacy paper payload",
            path_params=("unresolved",),
        ),
        _endpoint(EndpointName.PAPER, "/papers/v3/{unresolved}", "Paper metadata", path_params=("unresolved",)),
        _endpoint(EndpointName.PAPER_PREVIEW, "/papers/v3/{id}/preview", "Paper preview", path_params=("id",)),
        _endpoint(
            EndpointName.PAPER_FULL_TEXT,
            "/papers/v3/{paperVersion}/full-text",
            "Extracted full text",
            path_params=("paperVersion",),
        ),
        _endpoint(
            EndpointName.PAPER_OVERVIEW,
            "/papers/v3/{paperVersion}/overview/{language}",
            "Existing paper overview",
            path_params=("paperVersion", "language"),
        ),
        _endpoint(
            EndpointName.PAPER_OVERVIEW_STATUS,
            "/papers/v3/{paperVersion}/overview/status",
            "Overview status",
            path_params=("paperVersion",),
        ),
        _endpoint(
            EndpointName.PAPER_COMMENTS,
            "/papers/v3/legacy/{group}/comments",
            "Paper comments",
            path_params=("group",),
        ),
        _endpoint(
            EndpointName.SIMILAR_PAPERS,
            "/papers/v3/{id}/similar-papers",
            "Similar papers",
            path_params=("id",),
            optional_query=("limit", "exclude", "excludeLikes", "interval"),
        ),
        _endpoint(
            EndpointName.PAPER_METRICS,
            "/papers/v3/{unresolved}/metrics",
            "Paper metrics",
            path_params=("unresolved",),
        ),
        _endpoint(
            EndpointName.PAPER_FIGURES,
            "/papers/v3/{paperGroupId}/figures",
            "Paper figures",
            path_params=("paperGroupId",),
        ),
        _endpoint(
            EndpointName.PAPER_EXTRAS,
            "/papers/v3/{paperGroupId}/extras",
            "Paper extras",
            path_params=("paperGroupId",),
        ),
        _endpoint(
            EndpointName.PAPER_IMPLEMENTATIONS,
            "/papers/v3/{paperGroupId}/implementations",
            "Paper implementations",
            path_params=("paperGroupId",),
        ),
        _endpoint(
            EndpointName.AUTORESEARCH_IMPLEMENTATIONS,
            "/papers/v3/{paperGroupId}/autoresearch-implementations",
            "Autoresearch implementations",
            path_params=("paperGroupId",),
        ),
        _endpoint(
            EndpointName.AI_DETECTION,
            "/papers/v3/{paperVersion}/ai-detection",
            "AI detection",
            path_params=("paperVersion",),
        ),
        _endpoint(
            EndpointName.MODEL_LINKS,
            "/papers/v3/{paperVersion}/model-links",
            "Model links",
            path_params=("paperVersion",),
        ),
    )
}
