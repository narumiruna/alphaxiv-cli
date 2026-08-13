# axiv rename completion plan

## Goal

Complete the package, executable, container, documentation, and agent Skill rename from `alphaxiv` to `axiv` while preserving the alphaXiv service name, API hosts, payload fields, and `ALPHAXIV_*` environment variables.

## Non-Goals

- Do not rename alphaXiv service terminology, domains, API payload aliases, OpenAPI fixtures, or `ALPHAXIV_*` environment variables.
- Do not rewrite archived implementation plans.
- Preserve every `alphaXiv` proper noun in `README.md`.

## Plan

- [x] Add focused rename assertions for the `axiv` CLI and Skill, then confirm the old identity fails those checks; the initial focused run failed on the old command name, message, resource package, and Skill path.
- [x] Update package metadata, runtime resource lookup, CLI identity, Docker entrypoint, User-Agent, and lockfile to `axiv`.
- [x] Rename the Skill to `using-axiv-cli` and update its commands, references, tests, discovery symlink, and current documentation links.
- [x] Update `README.md` project, executable, and Skill references without changing alphaXiv proper nouns or `ALPHAXIV_*` variables.
- [x] Run focused tests, lint, formatting, type checking, the full test suite, build checks, and an installed-wheel CLI/resource smoke test; Docker execution was unavailable because Docker is not installed in this WSL environment.

## Completion Checklist

- [x] `axiv --help` works from source and an isolated built wheel.
- [x] Packaged OpenAPI resources load from the `axiv` package; the isolated wheel smoke test loaded all 26 paths.
- [x] No active project or CLI identity reference still uses lowercase `alphaxiv` outside preserved service paths, payload fields, fixtures, and historical plans.
- [x] All available configured local quality gates pass: Ruff lint/format, ty, lock check, and 174 tests with 4 opt-in live tests skipped.
