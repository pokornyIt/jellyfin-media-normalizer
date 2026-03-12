# GitHub Copilot Instructions

You are assisting with the `jellyfin-media-normalizer` project.

## Project Purpose

This project is used to scan, classify, validate, normalize, and safely rename a large movie and TV series library for Jellyfin.

The project must:

- normalize movie and TV series names into a consistent naming scheme
- validate parsed results before applying changes
- look up a single provider ID for movies and TV series
- generate rename plans before executing any filesystem changes
- support safe batch-based rename execution
- avoid `.nfo` files
- keep the filesystem readable and clean

## Key Constraints

These rules are non-negotiable and must be preserved in all generated code:

- no `.nfo` files
- one provider ID per movie or TV series only; no episode-level IDs
- no rename without a validated plan
- no bulk rename without a generated manifest
- dry-run must be the default execution mode

## Technical Stack

- Python 3.14.2
- dependency management: `uv`
- linting and formatting: `ruff`
- type checking: `pyright`
- tests: `pytest`

## Commit Messages

Use **Conventional Commits** with one of these prefixes (choose the best match):

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation only
- `refactor:` refactoring without behavior change
- `perf:` performance improvements
- `test:` tests only
- `chore:` tooling, dependencies, CI, and non-production tasks
- `ci:` CI pipeline changes
- `build:` packaging and build changes

Guidelines:

- Subject line must be imperative and concise, ideally up to 72 characters.
- Use English in commit messages.
- If relevant, include a scope in parentheses, for example: `feat(parser): add movie filename parser`

## Python Style Conventions

- Follow **PEP 8** and keep code readable and explicit.
- Use English for all code, identifiers, filenames, comments, and markdown files.
- Naming conventions:
  - variables and functions: `snake_case`
  - classes: `CamelCase`
  - constants: `UPPER_SNAKE_CASE`
- Prefer small, testable functions.
- Avoid hidden side effects and global mutable state.
- Prefer the standard library when reasonable.
- Prefer clear and explicit data flow over clever or compact code.
- Use `pathlib.Path` for filesystem paths.
- Use type hints for all public functions and important internal functions.
- Prefer dataclasses or Pydantic models for structured data.
- Separate parsing, validation, lookup, planning, and execution logic.

## Docstring Rules

Docstrings are required for all classes and all functions.

Use reStructuredText docstring format.

Use this style:

```python
def example(name: str) -> str:
    """Return normalized value.

    :param name: Input value to normalize.
    :return: Normalized value.
    """
```

Rules:

* Use `:param var: description`
* Use `:return: description` where applicable
* Do not use `:type:`
* Do not use `:rtype:`
* Keep docstrings concise and useful
* Every public and internal class/function must have a docstring

## Testing Rules

Tests must use `pytest`.

Testing conventions:

* Test files should reflect the source structure.
* Test classes should correspond to the tested classes.
* Test class names should start with `Test`.
* Test functions should start with `test_`.
* Prefer parametrized tests using `pytest.mark.parametrize` where it improves clarity and coverage.
* Avoid unnecessary mocks when simple input/output testing is enough.
* Focus tests on parser behavior, validation rules, provider ID lookup decisions, and rename planning.
* Cover valid, invalid, edge, and ambiguous cases.

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

## Architecture Guidance

Code is organized into clear layers. Each layer maps to one or more project phases.

```text
models/       — shared data structures (MediaItem, RenameEntry, ProviderMatch, etc.)
scanners/     — Phase 1: filesystem scan and inventory
parsers/      — Phase 2–3: classification and name normalization
validators/   — Phase 4: validation and confidence scoring
providers/    — Phase 5: provider ID lookup (TMDb, TVDB, IMDb)
planners/     — Phase 6: rename manifest generation
executors/    — Phase 7: batch rename execution and rollback logging
reporters/    — Phase 8: review report generation (CSV, JSON, HTML)
cli/          — entry points and command dispatch
```

Notes on specific layers:

* `providers/` handles all external API communication for provider ID lookup. This is the only layer that makes network requests. It should be replaceable without affecting other layers.
* `reporters/` produces review output for ambiguous matches, unresolved filenames, and items requiring manual approval. It has no side effects on the filesystem.
* `executors/` must support dry-run mode. Dry-run should be the default. Actual rename execution requires an explicit opt-in flag.

Suggested principles:

* never rename files directly from raw parsing or raw provider lookup
* always generate a validated plan first
* keep side effects isolated to `executors/`
* make dry-run behavior easy to support
* design for batch execution and rollback logging
* keep provider integration replaceable

## What Copilot Should Optimize For

When generating code, optimize for:

1. correctness
2. readability
3. maintainability
4. testability
5. safe filesystem operations

Do not optimize for cleverness.

Avoid hidden behavior, magic defaults, and tightly coupled code.

## Output Expectations

When proposing code:

* include complete functions or classes
* preserve project conventions
* include docstrings
* include type hints
* include tests when relevant
* avoid placeholder logic unless explicitly requested

When modifying code:

* keep the existing structure unless there is a clear reason to improve it
* prefer minimal safe changes
* preserve compatibility with the current project design
