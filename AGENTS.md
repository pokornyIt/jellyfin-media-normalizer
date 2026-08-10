# Repository Instructions

You are assisting with the `jellyfin-media-normalizer` project.

## Scope And Sources Of Truth

These instructions apply to the entire repository unless a more specific nested `AGENTS.md` file applies.

Use the project documents according to their roles:

- `docs/en/PROJECT-DESCRIPTION.md` defines the current stable product scope, domain rules, and safety constraints.
- `docs/en/PRODUCT_DEVELOPMENT_BRIEF.md` defines the target product direction and records unresolved product decisions.
- `docs/en/DEVELOPMENT_PLAN.md` tracks implementation status, priorities, and verification snapshots.
- `README.md` and `README.cs.md` document behavior and workflows currently available to operators.

Keep implementation, examples, tests, and documentation consistent with these sources. If a requested change
conflicts with them, call out the conflict and update the appropriate source document as part of the same change
when authorized.

For current behavior, verify the implementation and both README language versions. For new product behavior, follow
accepted decisions in `docs/en/PRODUCT_DEVELOPMENT_BRIEF.md`; do not implement choices that the brief still marks as
open. Keep `docs/en/PROJECT-DESCRIPTION.md` and `docs/en/DEVELOPMENT_PLAN.md` aligned when an accepted decision changes
scope or priorities.

Do not treat roadmap items or target-state requirements as already implemented behavior.

## Communication And Language

- Communicate with the user in Czech.
- Use English for identifiers, comments, docstrings, tests, logs, errors, configuration comments, canonical English
  documentation, commit messages, and pull request text.
- Write Czech documentation only in the paired Czech documentation tree described below.

## Project Purpose

This project is intended to scan, classify, validate, normalize, and safely rename a large movie
and TV series library for Jellyfin.

The project must:

- normalize movie and TV series names into a consistent naming scheme;
- validate parsed results and provider selections;
- identify each movie or TV series with at most one provider ID;
- generate reviewable rename manifests;
- execute approved changes safely in logical batches;
- keep the filesystem readable and clean.

## Key Constraints

These rules are non-negotiable and must be preserved in all generated code:

- Never read, parse, create, modify, delete, or target `.nfo` files with standalone operations. An `.nfo` file may
  move only as an ignored child of a renamed parent directory and must never receive its own manifest entry.
- Store at most one selected provider ID per movie or TV series; never store episode-level IDs.
- Every rename must originate from a validated, approved, and persisted manifest.
- Never rename directly from raw parsing or provider lookup output.
- Dry-run must be the default; real execution requires explicit opt-in.

## Technical Stack

- Python 3.14 (`>=3.14,<3.15`)
- dependency management: `uv`
- linting and formatting: `ruff`
- type checking: `pyright`
- tests: `pytest`

Use `uv` for dependency management, virtual environments, locking, and Python command execution. Use the
project-local `.venv`, declare dependencies in `pyproject.toml`, and keep `uv.lock` synchronized.

- Do not rely on OS-level or globally installed Python development tools.
- Do not use `pip install` for normal project dependency management.
- Do not introduce `requirements.txt` as the primary dependency definition.
- Do not add a production dependency without a concrete need and an explanation in the change summary.
- Use only commands supported by configuration files currently present in the repository.

## Documentation Guidance

- English documentation lives under `docs/en/`; paired Czech documentation lives under `docs/cs/`.
- Keep matching file names and directory structures between `docs/en/` and `docs/cs/` for every maintained document.
- Treat English documentation as canonical and update its Czech counterpart in the same change whenever content or
  links change. This includes the root `README.md` and `README.cs.md` pair.
- Do not merge a documentation change while the language versions are semantically inconsistent unless the user
  explicitly requests a temporary single-language change; report that mismatch clearly.
- Keep documentation operational and example-driven; avoid marketing language.
- Keep changes scoped to the requested documents and avoid unrelated rewrites or bulk reformatting.
- Keep stable product requirements separate from implementation status and dated verification results.
- Update examples and operator documentation when behavior, configuration, or workflows change.
- Keep terminology consistent with the Jellyfin media normalization domain, including provider lookup, manifests,
  dry-run safety, and human approval.

## Markdown Conventions

These rules apply to every `*.md` file in the repository.

- Follow `.markdownlint.yml` and treat every enabled rule as required.
- Do not add inline or file-level lint exceptions when the content can be written clearly without them.
- The configured exceptions `MD024`, `MD025`, `MD036`, and `MD041` are permitted; do not disable additional rules
  without a concrete repository need.
- Keep normal prose within the configured `MD013` limit of 120 characters.
- Use local `MD013` disable and enable comments only when necessary for long URLs, command output, or wide tables.
- Do not aggressively reflow tables only to satisfy line length.
- Keep any disabled region as small as possible, preferably around one table only.

Use this form for a wide table when an exception is necessary:

```md
<!-- markdownlint-disable MD013 -->
| Column A | Column B | Column C |
| -------- | -------- | -------- |
| ...      | ...      | ...      |
<!-- markdownlint-enable MD013 -->
```

## Commit Messages

Follow the allowed types, format, and examples in:

- `docs/en/COMMIT_CONVENTIONS.md` (canonical, English)
- `docs/cs/COMMIT_CONVENTIONS.md` (Czech reference)

- Subject line must be imperative and concise, ideally up to 72 characters.
- Use English in commit messages.
- If relevant, include a scope in parentheses, for example: `feat(parser): add movie filename parser`

## Branch Names

- Use the format `<issue-number>-<short-description>` for branches associated with an issue.
- Write the description in lowercase English kebab-case, for example: `5-align-product-documentation`.
- Do not use category or Conventional Commit prefixes such as `docs/`, `feat/`, `fix/`, or `chore/`.
- Keep branch names concise while preserving enough context to identify the related work.

## Pull Requests And Issue Traceability

- Every change merged into `main` must go through a pull request.
- Every pull request targeting `main` must link at least one existing open issue in this repository.
- When merging the pull request will complete an issue, add `Closes #<issue-number>` to the pull request description.
- For partial work that must not close the issue, link the pull request manually through GitHub's Development section
  and use `Related to #<issue-number>` in the description for reader context.
- Use a plain GitHub issue reference such as `#123`; do not wrap it in a manually constructed Markdown link.
- Verify that every referenced issue exists and matches the change. Never invent or guess an issue number.
- Pull request titles must follow the same English Conventional Commit subject rules as commit messages.
- Individual branch commits do not need an issue reference. Do not append an issue number to a generated commit subject
  unless the user explicitly requests it and the correct issue is known.
- For squash merges, allow GitHub to append the pull request number to the final commit subject. Keep the issue-closing
  reference in the pull request description.

## Python Style Conventions

- Follow **PEP 8** and keep code readable and explicit.
- Use a maximum Python line length of 120 characters, as configured for Ruff.
- Use English for Python code, identifiers, filenames, comments, and docstrings.
- Naming conventions:
  - variables and functions: `snake_case`
  - classes: `CamelCase`
  - constants: `UPPER_SNAKE_CASE`
- Use `snake_case.py` for Python filenames; never use hyphens.
- Prefer small, testable functions.
- Avoid hidden side effects and global mutable state.
- Prefer the standard library when reasonable.
- Prefer clear and explicit data flow over clever or compact code.
- Use `pathlib.Path` for filesystem paths.
- Add type annotations to every function and method signature, including return types.
- Add explicit type annotations to module-level and local variables introduced by assignment, even when inference is
  possible.
- Inline annotations are not required for `for` loop targets, comprehensions, context managers, exception targets,
  assignment expressions, or unpacking assignments.
- Prefer precise types and avoid `Any` when a narrower type or model is practical.
- Prefer `str | None` to `Optional[str]` and built-in generic collections such as `list[str]`.
- Use `TypeAlias` or `TypedDict` for complex data shapes when a dedicated model would not be clearer.
- Annotate constants with `Final` and an explicit type when practical.
- Do not introduce a separate static type-checker configuration unless explicitly requested.
- Prefer dataclasses or Pydantic models for structured data.
- Separate parsing, validation, lookup, planning, and execution logic.
- Keep modules focused and avoid speculative abstractions or unused extension frameworks.
- Keep imports organized and never use wildcard imports.
- Prefer specific exception handling over broad `except Exception` blocks.
- Give standalone executable Python scripts a `#!/usr/bin/env python3` shebang and a module docstring. Package modules
  do not need a shebang.

## Docstring Rules

Use English reStructuredText docstrings.

Use this style:

```python
def example(name: str) -> str:
    """Return normalized value.

    :param name: Input value to normalize.
    :return: Normalized value.
    """
```

Rules:

- Use `:param var: description`
- Use `:return: description` where applicable
- Use `:raises ExceptionType:` for relevant documented failure modes.
- Do not use `:type:`
- Do not use `:rtype:`
- Keep docstrings concise and focused on contracts, behavior, and non-obvious failure modes.
- Every public and internal class, function, and method must have a docstring, including private helpers,
  constructors, special methods, and nested functions.
- Constructor docstrings must describe every parameter other than `self`.
- Test methods must state the behavior they verify. They do not need `:param:` fields for pytest fixtures or
  parametrized values.
- Do not place a bare string after a constant assignment as a pseudo-docstring. Add a comment only when the purpose,
  unit, or derivation is not clear from context.

## Errors, Logging, And Security

- Raise specific exceptions in reusable and library code; do not call `sys.exit` there.
- Exit the process only from `main()` or an equivalent top-level CLI layer.
- Use logging for operational and diagnostic output. Use `click.echo` or `print` only for intentional CLI output.
- Reuse `setup_logging`, `get_logger`, and `LoggingMixin` from `jellyfin_media_normalizer.utils.logging`; do not use
  the root logger directly in library modules.
- Keep severity semantics aligned with `ERROR`, `WARNING`, `INFO`, and `DEBUG`.
- Keep log messages concise and actionable; avoid noisy logging in hot loops unless guarded by log level.
- Make error messages actionable and include relevant non-secret context such as a path, provider, or expected field.
- Read provider credentials and other secrets only from documented environment variables or supported secret files.
- Never commit credentials, private media metadata, or generated workspace data.
- Never log API keys, environment contents, authorization headers, or complete URLs containing credentials.
- Sanitize secrets from exception messages and HTTP diagnostics.
- Never weaken TLS certificate verification.
- Preserve structured logging conventions and keep logs useful for long-running operations.

## Configuration Changes

- Validate configuration values strictly and fail with actionable messages.
- Reject unknown configuration keys when a structured configuration format is introduced.
- Keep documented defaults, examples, and runtime behavior aligned.
- Update example configuration whenever schema, defaults, units, or accepted formats change.
- Keep credentials out of committed YAML, JSON, environment examples, and source code.

## Testing Rules

Tests must use `pytest`.

Testing conventions:

- Test files should reflect the source structure.
- Test classes should correspond to the tested classes.
- Test class names should start with `Test`.
- Test functions should start with `test_`.
- Prefer parametrized tests using `pytest.mark.parametrize` where it improves clarity and coverage.
- Avoid unnecessary mocks when simple input/output testing is enough.
- Focus tests on parser behavior, validation rules, provider ID lookup decisions, and rename planning.
- Cover valid, invalid, edge, and ambiguous cases.
- Add or update tests for every behavior change, including the affected happy path and relevant boundary or failure
  cases.
- Tests must not require live provider credentials, Internet access, destructive filesystem changes, or wall-clock
  waiting.
- Use test doubles for HTTP and other external boundaries and controllable clocks for time-dependent behavior.
- Do not add tests for trivial I/O-only flows unless the user requests them.

Example:

```python
import pytest


class TestMovieNameParser:
    @pytest.mark.parametrize(
        ("filename", "expected_title", "expected_year"),
        [
            ("Avatar (2009) - EN.mkv", "Avatar", 2009),
            ("Matrix (1999) - CZ.mkv", "Matrix", 1999),
        ],
    )
    def test_parse_movie_name(
        self,
        filename: str,
        expected_title: str,
        expected_year: int,
    ) -> None:
        """Test parsing of normalized movie filenames.

        :param filename: Input filename to parse.
        :param expected_title: Expected parsed movie title.
        :param expected_year: Expected parsed movie year.
        """
        ...
```

## YAML Conventions

These rules apply to all `*.yaml` and `*.yml` files in the repository.

- Use consistent two-space indentation.
- Prefer explicit booleans such as `true` and `false`.
- Quote strings when an unquoted value could be interpreted ambiguously.
- Preserve single-document or multi-document structure already used by the file.
- Keep changes focused and do not reformat unrelated blocks.
- Keep configuration local to this project and avoid cross-project coupling.
- Never add plaintext credentials, API tokens, or private keys.
- Keep example configuration usable with non-sensitive placeholders.

## Architecture Guidance

Code is organized into clear layers with explicit responsibilities.

```text
models/       — shared typed data structures
scanners/     — filesystem scan and inventory
parsers/      — classification and name normalization
validators/   — validation and confidence scoring
providers/    — embedded ID, cache, and TMDb/TVDB lookup
services/     — application workflow orchestration
reporters/    — JSON and HTML reports; CSV is planned
cli/          — command entry points and dispatch
utils/        — shared infrastructure such as logging and paths
settings.py   — runtime configuration and path defaults
constants.py  — shared constants and defaults

# reserved/planned layers
planners/     — validated rename manifest generation
executors/    — batch execution, audit, and rollback support
```

Notes on specific layers:

- `providers/` handles all external API communication for provider ID lookup. This is the only layer that makes network
  requests. It should be replaceable without affecting other layers.
- `reporters/` may write requested report files, but it must never modify the media library.
- `services/` coordinates workflows and may use explicit persistence abstractions, but it must never mutate the media
  library directly.
- `executors/` owns all media-library mutations and must enforce manifest input, dry-run defaults, explicit opt-in,
  audit logging, batch safety, and rollback support.

## Docker And Compose

- Treat Docker Compose as the primary operator deployment path once container support is implemented.
- Run production containers as a non-root user.
- Do not bake credentials, workspace data, media files, or installation-specific configuration into images.
- Keep the default media-library mount read-only.
- Require an explicit execution configuration for read-write media access.
- Keep workspace persistence separate from the media-library mount.
- Do not use privileged mode, host networking, or Docker socket access without an approved and documented need.
- Container access does not bypass manifest, validation, dry-run, confirmation, audit, or rollback requirements.

## Engineering Priorities

When generating code, optimize for:

1. correctness
2. readability
3. maintainability
4. testability
5. safe filesystem operations

Do not optimize for cleverness.

Avoid hidden behavior, magic defaults, and tightly coupled code.

## Simplicity And Validation Boundaries

- Prefer the simplest direct implementation that clearly satisfies the requirement.
- Structure code into small cohesive components with explicit responsibilities, dependencies, inputs, and outputs.
- Do not introduce pass-through wrappers, unnecessary indirection, premature extension points, or configuration flags
  without a current concrete use case.
- Validate untrusted data once at the boundary where it enters the application, such as CLI or web input, environment
  configuration, filesystem data, persisted state, deserialization, or provider responses.
- After successful validation, represent data with a typed validated model or explicit workflow state. Downstream
  functions should trust that contract instead of repeating identical validation.
- Revalidate only when data may have changed, crosses a new trust boundary, or enters a state transition with stronger
  invariants.
- Planning, dry-run, and real execution are separate safety boundaries. Executors must revalidate relevant source and
  destination filesystem state because it can change between those stages.
- Make function preconditions clear through types, names, and concise docstrings rather than defensive checks in every
  call layer.

## Implementation Expectations

- Provide complete implementations and avoid placeholder logic unless explicitly requested.
- Keep the existing structure unless there is a clear reason to improve it.
- Prefer minimal safe changes and preserve compatibility with the current project design.

## Validation Requirements

Use narrower validation scopes during iteration when practical, then run checks proportional to the final change.

- Markdown changes: `uv run pre-commit run markdownlint --files <changed-md-files>`.
- Documentation-wide changes: `uv run pre-commit run markdownlint --all-files`.
- YAML changes: `uv run pre-commit run check-yaml --files <changed-yaml-files>`.
- Python behavior changes: `uv run ruff format --check .`, `uv run ruff check .`, `uv run pyright`, and
  `uv run pytest`.
- Container changes, when the files exist: `docker build .` and `docker compose config`.
- Repository-wide final validation when appropriate: `uv run pre-commit run --all-files`.

If a required check cannot run, state that clearly in the final report.

## Change Discipline

- Inspect the working tree before editing and preserve unrelated user changes.
- Do not edit generated files manually when an appropriate generator exists.
- Do not mix product requirements, implementation status, and historical verification results in one source of truth.
- Report which checks ran, which checks did not run, and why.
