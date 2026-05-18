---
applyTo: "**/*.yaml,**/*.yml"
---

# YAML Conventions - jellyfin-media-normalizer

## Scope

- These rules apply to YAML files in this repository, primarily:
  - Tool and runtime configuration files
  - local automation and quality tooling configuration

- These rules complement workspace-level rules in `AGENTS.md`.

## General YAML Rules

- Keep indentation consistent (2 spaces).
- Prefer explicit booleans (`true`/`false`) and quoted strings when values may be ambiguous.
- Keep changes minimal and focused; do not reformat unrelated blocks.
- Allow both single-document and multi-document YAML where used by existing files.

## Configuration Rules

- Keep YAML configuration local to the project; avoid introducing cross-project coupling.
- Do not introduce plaintext credentials, API tokens, or private keys.
- Keep example configuration files usable as templates (for example, keep placeholders non-sensitive).

## Validation

- Validate YAML changes with `uv run pre-commit run check-yaml --all-files` (or narrower scope when practical).
- For changed files only, prefer `uv run pre-commit run check-yaml --files <changed-yaml-files>`.
- Use the project virtual environment for tooling execution, not global tools.
- If validation cannot be run in the current environment, state that clearly in the final report.
