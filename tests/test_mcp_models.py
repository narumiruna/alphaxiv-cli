import json
from datetime import date

import pytest
from pydantic import ValidationError

from alphaxiv.models.library import ExternalLibraryResponse
from alphaxiv.models.library import LibraryFolder
from alphaxiv.models.library import LibraryListResult
from alphaxiv.models.library import LibraryMutationResult
from alphaxiv.models.mcp import AnswerPdfQueriesArguments
from alphaxiv.models.mcp import AuthStatusResult
from alphaxiv.models.mcp import CreateFolderArguments
from alphaxiv.models.mcp import DiscoverPapersArguments
from alphaxiv.models.mcp import GithubRepositoryArguments
from alphaxiv.models.mcp import McpTextResult
from alphaxiv.models.mcp import SavePapersArguments


def test_discover_arguments_validate_bounds_dates_and_alias_serialization() -> None:
    arguments = DiscoverPapersArguments(
        keywords=("attention",),
        question="How does attention work?",
        difficulty=5,
        published_after=date(2017, 1, 1),
        prioritize="historical",
    )

    assert arguments.model_dump(by_alias=True, exclude_none=True, mode="json") == {
        "keywords": ["attention"],
        "question": "How does attention work?",
        "difficulty": 5,
        "published_after": "2017-01-01",
        "prioritize": "historical",
    }
    with pytest.raises(ValidationError):
        DiscoverPapersArguments(keywords=("attention",), question="Question", difficulty=11)


def test_research_arguments_reject_empty_or_unsafe_values() -> None:
    with pytest.raises(ValidationError):
        AnswerPdfQueriesArguments(paper="1706.03762", queries=())
    with pytest.raises(ValidationError):
        GithubRepositoryArguments(github_url="https://example.com/repo", path="/")
    with pytest.raises(ValidationError):
        GithubRepositoryArguments(github_url="https://github.com/owner/repo/issues/1", path="/")
    with pytest.raises(ValidationError):
        GithubRepositoryArguments(github_url="https://github.com/owner/repo?tab=readme", path="/")
    with pytest.raises(ValidationError):
        GithubRepositoryArguments(github_url="https://github.com/owner/repo", path="bad\x1bpath")


def test_library_arguments_enforce_remote_limits_and_folder_names() -> None:
    arguments = SavePapersArguments(folder_id="folder-1", paper_ids_or_urls=("1706.03762",))

    assert arguments.model_dump(by_alias=True, exclude_none=True, mode="json") == {
        "paper_ids_or_urls": ["1706.03762"],
        "folder_id": "folder-1",
    }
    with pytest.raises(ValidationError):
        SavePapersArguments(folder_id="folder-1", paper_ids_or_urls=tuple(str(index) for index in range(51)))
    with pytest.raises(ValidationError):
        CreateFolderArguments(name="  ")
    with pytest.raises(ValidationError):
        SavePapersArguments(folder_id="folder-1\x00", paper_ids_or_urls=("1706.03762",))
    with pytest.raises(ValidationError):
        SavePapersArguments(folder_id="folder-1", paper_ids_or_urls=("1706.03762\x1b",))


def test_external_library_models_tolerate_additive_fields_but_stable_output_is_strict() -> None:
    external = ExternalLibraryResponse.model_validate(
        {
            "folders": [
                {
                    "folder_id": "folder-1",
                    "name": "Reading",
                    "type": "custom",
                    "paper_count": 1,
                    "future_remote_field": True,
                }
            ],
            "future_top_level_field": "ignored",
        }
    )
    stable = LibraryListResult(
        folders=tuple(LibraryFolder.from_external(folder) for folder in external.folders),
        memberships=(),
    )

    assert json.loads(stable.model_dump_json())["folders"][0]["folder_id"] == "folder-1"
    with pytest.raises(ValidationError):
        LibraryListResult.model_validate({"folders": [], "memberships": [], "unknown": True})


def test_mcp_outputs_never_have_an_api_key_field() -> None:
    status = AuthStatusResult(
        api_key_present=True,
        initialized=True,
        tools_compatible=True,
        protocol_version="2025-03-26",
        server_name="alphaXiv",
    )
    result = McpTextResult(tool="discover_papers", text="answer", metadata={"requestId": "request-1"})

    serialized = status.model_dump_json() + result.model_dump_json()
    assert "axv-" not in serialized
    assert 'api_key"' not in serialized
    with pytest.raises(ValidationError):
        McpTextResult(
            tool="discover_papers",
            text="answer",
            metadata={"requestId": {"apiKey": "axv-private"}},
        )
    with pytest.raises(ValidationError):
        LibraryMutationResult(
            action="create_folder",
            success=True,
            target="Reading",
            details={"data": {"access_token": "axv-private"}},
        )
