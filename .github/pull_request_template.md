<!-- Required title: <Conventional Commit subject> (#<primary-issue-number>) -->

## Summary

<!-- Describe what changed and why. -->

## Linked issue

<!--
Every pull request targeting main must link an existing open issue from this repository.
The primary issue must match the "(#<issue-number>)" suffix in the pull request title.
Use "Closes #123" when this pull request completes the issue.
For partial work, link the pull request through GitHub's Development section and use "Related to #123".
-->

Closes #

## Validation

<!-- List the checks that were run and their results. -->

- [ ] `uv lock --check`
- [ ] `uv run ruff format --check .`
- [ ] `uv run ruff check .`
- [ ] `uv run pyright`
- [ ] `uv run pytest`
- [ ] Relevant documentation checks

## Safety and documentation

- [ ] The change never reads, parses, creates, modifies, deletes, or targets `.nfo` files with standalone operations.
- [ ] Filesystem mutations, if any, require an approved manifest and preserve dry-run defaults.
- [ ] English and Czech documentation remain semantically aligned, or documentation is not affected.
