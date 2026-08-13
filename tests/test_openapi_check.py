import copy
import json
from pathlib import Path

from axiv.contracts.openapi import OpenAPIDocument
from axiv.contracts.openapi import check_openapi_document
from axiv.openapi_check import load_packaged_baseline

FIXTURE = Path(__file__).parent / "fixtures" / "openapi" / "alphaxiv-rest-subset.json"


def load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE.read_text())


def test_packaged_openapi_baseline_matches_test_fixture() -> None:
    fixture = OpenAPIDocument.model_validate(load_fixture())

    assert load_packaged_baseline() == fixture


def test_openapi_fixture_is_compatible_with_static_contracts() -> None:
    payload = load_fixture()
    document = OpenAPIDocument.model_validate(payload)

    report = check_openapi_document(document, baseline=document)

    assert report.compatible is True
    assert report.checked_endpoints == 26
    assert report.issues == []


def test_openapi_check_reports_missing_route() -> None:
    baseline_payload = load_fixture()
    candidate_payload = copy.deepcopy(baseline_payload)
    paths = candidate_payload["paths"]
    assert isinstance(paths, dict)
    del paths["/events/v1"]

    report = check_openapi_document(
        OpenAPIDocument.model_validate(candidate_payload),
        baseline=OpenAPIDocument.model_validate(baseline_payload),
    )

    assert report.compatible is False
    assert any(issue.kind == "missing_path" and issue.path == "/events/v1" for issue in report.issues)


def test_openapi_check_reports_new_required_parameter() -> None:
    baseline_payload = load_fixture()
    candidate_payload = copy.deepcopy(baseline_payload)
    paths = candidate_payload["paths"]
    assert isinstance(paths, dict)
    operation = paths["/events/v1"]["get"]
    operation["parameters"].append({"name": "required", "in": "query", "required": True, "schema": {"type": "string"}})

    report = check_openapi_document(
        OpenAPIDocument.model_validate(candidate_payload),
        baseline=OpenAPIDocument.model_validate(baseline_payload),
    )

    assert report.compatible is False
    assert any(issue.kind == "required_parameters" for issue in report.issues)


def test_openapi_check_reports_response_schema_drift() -> None:
    baseline_payload = load_fixture()
    candidate_payload = copy.deepcopy(baseline_payload)
    paths = candidate_payload["paths"]
    assert isinstance(paths, dict)
    schema = paths["/papers/v3/{unresolved}/metrics"]["get"]["responses"]["200"]["schema"]
    schema["required"] = ["commentsCount"]

    report = check_openapi_document(
        OpenAPIDocument.model_validate(candidate_payload),
        baseline=OpenAPIDocument.model_validate(baseline_payload),
    )

    assert report.compatible is False
    assert any(issue.kind == "response_schema" for issue in report.issues)
