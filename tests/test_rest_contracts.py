import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from alphaxiv.contracts.rest import API_BASE_URL
from alphaxiv.contracts.rest import ENDPOINTS
from alphaxiv.contracts.rest import EndpointName
from alphaxiv.contracts.rest import RestEndpoint

FIXTURE = Path(__file__).parent / "fixtures" / "openapi" / "alphaxiv-rest-subset.json"


def test_static_contracts_are_get_only_anonymous_and_production_scoped() -> None:
    assert API_BASE_URL == "https://api.alphaxiv.org"
    assert len(ENDPOINTS) == 26
    assert set(ENDPOINTS) == set(EndpointName)
    assert {endpoint.method for endpoint in ENDPOINTS.values()} == {"GET"}
    assert {endpoint.auth_mode for endpoint in ENDPOINTS.values()} == {"anonymous"}


def test_static_contract_rejects_undeclared_path_placeholder() -> None:
    with pytest.raises(ValidationError):
        RestEndpoint(
            name=EndpointName.PAPER,
            path="/papers/{paperId}",
            purpose="paper",
        )


def test_minimal_openapi_fixture_matches_static_paths_and_parameters() -> None:
    document = json.loads(FIXTURE.read_text())

    assert set(document["paths"]) == {endpoint.path for endpoint in ENDPOINTS.values()}
    for endpoint in ENDPOINTS.values():
        operation = document["paths"][endpoint.path]["get"]
        required = {
            (parameter["in"], parameter["name"]) for parameter in operation["parameters"] if parameter["required"]
        }
        expected = {
            *(("path", name) for name in endpoint.required_path_params),
            *(("query", name) for name in endpoint.required_query_params),
        }
        assert required == expected


def test_minimal_openapi_fixture_excludes_internal_and_mutating_content() -> None:
    text = FIXTURE.read_text()

    for forbidden in (
        "Source file",
        "api-server/file:",
        '"post"',
        '"put"',
        '"patch"',
        '"delete"',
        "/admin",
        "kickoff",
        "ingest",
    ):
        assert forbidden not in text
