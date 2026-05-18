---
applyTo: "**/*.py"
---

# Python Conventions - jellyfin-media-normalizer

## Scope

- These rules apply to Python source files in this repository.
- They complement workspace-level rules in `AGENTS.md`.

## Runtime Baseline

- Target Python `3.14.2` for new and updated code.
- Keep code and tests compatible with the version pinned in `pyproject.toml`.

## Environment And Tooling

- Use project virtual environments only (`.venv`), not OS-level/global tools.
- Use `uv` for dependency and execution workflows.
- Use `ruff` for linting/formatting and `pytest` for tests.
- Use `pyright` for static type checking.
- Do not introduce separate static type-checker configuration in this repository unless explicitly requested.

## Logging Rules

- Use `logging` for runtime diagnostics and operational events.
- Use `print` only for intentional CLI/user-facing output in script entrypoints.
- Prefer module loggers (`logger = get_logger(__name__)`) instead of root logger usage in libraries.
- Keep severity semantics aligned with Python logging levels: `ERROR`, `WARNING`, `INFO`, `DEBUG`.
- Keep log messages concise and actionable; avoid noisy repeated logs in hot loops unless guarded by level.
- Reuse existing logging helpers from `jellyfin_media_normalizer.utils.logging` (`setup_logging`, `get_logger`) in
  touched code.

## Domain Safety Rules

- Preserve core behavior constraints: no `.nfo` handling, one provider ID per movie/series, and safe dry-run defaults.
- Keep parsing, validation, provider lookup, planning, and execution concerns separated.
- Avoid introducing direct rename side effects outside explicit execution/planning flows.

## Code Quality

- Keep changes scoped to the affected module.
- Prefer explicit exceptions over broad `except Exception` blocks.
- Keep imports organized and avoid wildcard imports.
- Favor `pathlib` for filesystem paths in new or touched code.

## Validation

- Run `uv run ruff check` for changed Python scope.
- Run `uv run pyright` for static type checks.
- Run `uv run pytest` for impacted tests.
- If checks cannot run, state that clearly in the final report.
