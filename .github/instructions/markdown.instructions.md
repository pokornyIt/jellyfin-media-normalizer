---
applyTo: "**/*.md"
---

# Markdown Conventions - jellyfin-media-normalizer

## Source Of Truth

- Follow repository Markdown linting rules from `.markdownlint.yml`.
- Treat all Markdown rules as required, except rules explicitly disabled in `.markdownlint.yml`.
- These rules complement workspace-level rules in `AGENTS.md`.

## Allowed Exceptions From `.markdownlint.yml`

- `MD024: false` - duplicate headings are allowed.
- `MD025: false` - multiple top-level headings are allowed.
- `MD036: false` - emphasis used instead of headings is allowed.
- `MD041: false` - first line does not need to be a top-level heading.

## Line Length

- Keep normal prose lines within the configured limit (`MD013`, 120 characters).
- Use local `MD013` disable/enable blocks only when needed for readability (for example long URLs, command output,
  or wide tables).

## Tables

- Do not aggressively reflow Markdown tables just to satisfy line length.
- Surround wide table blocks with local `MD013` disable/enable comments.

```md
<!-- markdownlint-disable MD013 -->
| Column A | Column B | Column C |
| --- | --- | --- |
| ... | ... | ... |
<!-- markdownlint-enable MD013 -->
```

- Keep the disabled section as small as possible (table-only where practical).

## Documentation Structure

- Keep docs operational and example-driven; avoid marketing language.
- Keep changes scoped to the requested document; avoid unrelated rewrites or bulk reformatting.
- Keep terminology consistent with this project domain (Jellyfin media normalization, provider lookup, manifests,
  dry-run safety).

## Validation

- Validate Markdown changes with `uv run pre-commit run --files <changed-md-files>`.
- For repo-wide verification, use `uv run pre-commit run --all-files`.
- Use project tooling from the virtual environment; do not require global installations.
