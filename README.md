# alphaxiv-cli

`alphaxiv` is a typed Python CLI for alphaXiv's reviewed public REST reads and official MCP research and library tools.

The CLI uses Typer, HTTPX, the official MCP Python SDK, and `pydantic.BaseModel`.

It does not dynamically expose OpenAPI operations, arbitrary HTTP requests, or arbitrary MCP tools and arguments.

## Install

Install the `alphaxiv` command from a source checkout with uv.

```bash
uv tool install .
alphaxiv --help
```

For development, install the locked environment and run the CLI from the checkout.

```bash
uv sync --python 3.12
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

## Authenticated MCP commands

Create an API key in alphaXiv's MCP/API settings and provide it only through the environment.

```bash
export ALPHAXIV_API_KEY="your-key"
uv run --python 3.12 alphaxiv auth status --json
```

The CLI does not accept `--api-key`, browser cookies, or arbitrary MCP endpoints.

Research commands call alphaXiv Assistant models and consume Assistant quota.

```bash
uv run --python 3.12 alphaxiv research discover "How do transformers use attention?" --keyword transformer --keyword attention --json
uv run --python 3.12 alphaxiv paper content 1706.03762 --json
uv run --python 3.12 alphaxiv paper query 1706.03762 --query "What datasets were used?" --json
uv run --python 3.12 alphaxiv paper code https://github.com/owner/repository / --json
```

Batch every question for one paper as repeated `--query` options to avoid unnecessary quota use.

Library listing is read only and does not load papers unless `--include-papers` is supplied.

```bash
uv run --python 3.12 alphaxiv library list --json
```

Every remote library write requires `--yes` and an exact folder and paper target.

```bash
uv run --python 3.12 alphaxiv library save FOLDER_ID 1706.03762 --yes --json
uv run --python 3.12 alphaxiv library move SOURCE_FOLDER TARGET_FOLDER 1706.03762 --yes --json
uv run --python 3.12 alphaxiv library folder create "Reading list" --yes --json
```

For agents, `--yes` does not replace explicit user authorization for the exact remote change.

The source skill at [`skills/using-alphaxiv-cli/`](skills/using-alphaxiv-cli/SKILL.md) defines safe research and library workflows.

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

Live MCP authentication and library listing require both the read-only opt-in and an API key.

```bash
ALPHAXIV_LIVE=1 ALPHAXIV_API_KEY="your-key" uv run --python 3.12 pytest tests/e2e/test_live_mcp_readonly.py -q
```

The one-case MCP research smoke test is separate because it consumes Assistant quota.

```bash
ALPHAXIV_LIVE_RESEARCH=1 ALPHAXIV_API_KEY="your-key" uv run --python 3.12 pytest tests/e2e/test_live_mcp_research.py -q -s
```

See [`docs/research/alphaxiv-api.md`](docs/research/alphaxiv-api.md) for the API research and safety boundaries.
