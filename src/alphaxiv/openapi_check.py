import argparse
import json
import sys
from importlib.resources import files
from pathlib import Path
from typing import Protocol

import httpx
from pydantic import ValidationError

from alphaxiv.contracts.openapi import OpenAPIDocument
from alphaxiv.contracts.openapi import check_openapi_document

OPENAPI_URL = "https://api-dev.alphaxiv.org/api.json"
MAX_SCHEMA_BYTES = 5 * 1024 * 1024


class TextResource(Protocol):
    def read_text(self, encoding: str = "utf-8") -> str: ...


def _parse_document(text: str, *, label: str) -> OpenAPIDocument:
    try:
        payload = json.loads(text)
    except ValueError as error:
        msg = f"invalid JSON in OpenAPI document: {label}"
        raise RuntimeError(msg) from error
    try:
        return OpenAPIDocument.model_validate(payload)
    except ValidationError as error:
        msg = f"invalid OpenAPI document: {label}"
        raise RuntimeError(msg) from error


def _load_resource(resource: TextResource, *, label: str) -> OpenAPIDocument:
    try:
        text = resource.read_text(encoding="utf-8")
    except OSError as error:
        msg = f"could not read OpenAPI document: {label}"
        raise RuntimeError(msg) from error
    return _parse_document(text, label=label)


def load_packaged_baseline() -> OpenAPIDocument:
    resource = files("alphaxiv").joinpath("resources/openapi-rest-subset.json")
    return _load_resource(resource, label="packaged REST subset")


def load_remote_document() -> OpenAPIDocument:
    try:
        with (
            httpx.Client(
                timeout=15.0,
                follow_redirects=False,
                headers={"Accept": "application/json", "Accept-Encoding": "identity"},
            ) as client,
            client.stream("GET", OPENAPI_URL) as response,
        ):
            response.raise_for_status()
            body = bytearray()
            for chunk in response.iter_bytes():
                body.extend(chunk)
                if len(body) > MAX_SCHEMA_BYTES:
                    msg = "remote OpenAPI document was too large"
                    raise RuntimeError(msg)
    except httpx.HTTPError as error:
        raise RuntimeError("could not download the remote OpenAPI document") from error
    try:
        text = bytes(body).decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError("remote OpenAPI document was not UTF-8") from error
    return _parse_document(text, label=OPENAPI_URL)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check alphaXiv's reviewed REST contracts for OpenAPI drift.")
    parser.add_argument(
        "--baseline",
        type=Path,
        help="Optional minimal baseline fixture; defaults to the packaged REST subset.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        baseline = (
            _load_resource(args.baseline, label=str(args.baseline))
            if args.baseline is not None
            else load_packaged_baseline()
        )
        candidate = load_remote_document()
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 2

    report = check_openapi_document(candidate, baseline=baseline)
    print(report.model_dump_json(indent=2))
    return 0 if report.compatible else 1


if __name__ == "__main__":
    raise SystemExit(main())
