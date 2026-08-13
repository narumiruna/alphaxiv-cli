# alphaxiv-cli

`alphaxiv` is a typed Python CLI for reading alphaXiv through a static, reviewed REST surface.

The CLI uses Typer, HTTPX, and `pydantic.BaseModel`.

It does not generate requests from OpenAPI at runtime and does not expose arbitrary HTTP methods, URLs, or paths.

## Install

Install the project and its locked dependencies with uv.

```bash
uv sync --python 3.12
```

Run the CLI from the checkout.

```bash
uv run --python 3.12 alphaxiv --help
```

## Commands

Search public papers, extracted text, topics, and organizations.

```bash
uv run --python 3.12 alphaxiv search papers "transformer" --limit 5
uv run --python 3.12 alphaxiv search full-text "scaled dot-product attention" --limit 3
uv run --python 3.12 alphaxiv search topics "transformer"
uv run --python 3.12 alphaxiv search organizations "MIT"
```

Browse researchers, events, feeds, and topic groups.

```bash
uv run --python 3.12 alphaxiv researchers list --limit 5
uv run --python 3.12 alphaxiv researchers search "Yann LeCun" --limit 5
uv run --python 3.12 alphaxiv events list --limit 5
uv run --python 3.12 alphaxiv feed list --sort Recent --interval "7 Days" --limit 5
uv run --python 3.12 alphaxiv feed topics
```

Read paper metadata and existing derived data without starting remote generation jobs.

```bash
uv run --python 3.12 alphaxiv paper show 1706.03762
uv run --python 3.12 alphaxiv paper preview 1706.03762
uv run --python 3.12 alphaxiv paper text 1706.03762 --page 1
uv run --python 3.12 alphaxiv paper overview 1706.03762 --language en
uv run --python 3.12 alphaxiv paper related 1706.03762 --kind metrics
```

Add `--json` to any read command for stable machine-readable output.

```bash
uv run --python 3.12 alphaxiv search papers "transformer" --limit 1 --json
```

Search and list commands enforce conservative result limits.

The public REST client never sends `Authorization` or Cookie headers because several anonymous alphaXiv endpoints reject requests carrying an API Key.

## OpenAPI contract check

The development OpenAPI document is a development-time reference only.

Run the explicit drift check to compare the remote document with the 26 reviewed static contracts.

```bash
uv run --python 3.12 scripts/check_openapi_contract.py
```

The checker only downloads `https://api-dev.alphaxiv.org/api.json` and reports drift.

It does not generate source code or call any API operation described by the document.

## Development

Run the same checks as CI on Python 3.12.

```bash
uv run --python 3.12 ruff check .
uv run --python 3.12 ty check .
uv run --python 3.12 pytest -v -s --cov=src --cov-report=xml tests
```

Live REST smoke tests are opt-in and read only.

```bash
ALPHAXIV_LIVE=1 uv run --python 3.12 pytest tests/e2e/test_live_rest_readonly.py -q
```

See [`docs/research/alphaxiv-api.md`](docs/research/alphaxiv-api.md) for the API research and safety boundaries.
