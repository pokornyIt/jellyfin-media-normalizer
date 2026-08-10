# Development Plan

[English](DEVELOPMENT_PLAN.md) | [Čeština](../cs/DEVELOPMENT_PLAN.md)

This document tracks implementation status and next steps for jellyfin-media-normalizer.

It should be updated continuously and used as the practical execution checklist for upcoming phases.

## Current State Snapshot (2026-07-19)

Verified as implemented and stable:

- Scan pipeline (filesystem inventory).
- Parse and classification pipeline (movies, TV episodes, unknown).
- Validation pipeline (structure, consistency, confidence scoring).
- Provider lookup (embedded ID -> cache -> online resolver chain).
- Reporting: JSON review report, unresolved JSON report, review HTML report, unresolved HTML report.
- Runtime safety defaults, including dry-run default setting.
- Local quality gates: ruff, pyright, pytest, pre-commit hooks.

Verified quality status:

- `uv run pytest -q`: 466 passed.
- `uv run ruff check src tests`: passed.
- `uv run pyright`: 0 errors.

Main missing product capability:

- Rename planning and rename execution are not implemented as first-class layers yet.

Scale and usability risk to address next:

- Pure CLI + manual file edits will not scale well for large batches (hundreds to thousands of affected files).

## Non-Negotiable Constraints

All development tasks must preserve these rules:

- Never read, parse, create, modify, delete, or target `.nfo` files with standalone operations. An `.nfo` file may
  move only as an ignored child of a renamed parent directory.
- Exactly one provider ID per movie or TV series entity.
- Never rename without a validated plan.
- Never bulk rename without a generated manifest.
- Dry-run must remain the default execution mode.

## Phase Status

| Phase | Area                                  | Status                           |
| ----- | ------------------------------------- | -------------------------------- |
| 1     | Inventory and scan                    | Done                             |
| 2     | Classification                        | Done                             |
| 3     | Name normalization                    | Done                             |
| 4     | Validation                            | Done                             |
| 5     | Provider ID lookup                    | Done                             |
| 6     | Rename planning (manifest generation) | Not started                      |
| 7     | Batch rename execution                | Not started                      |
| 8     | Review workflow exports               | Partial (HTML done, CSV missing) |

## UX/Product Direction for Large Libraries

Decision to implement:

- Keep CLI as the source of truth for automation and batch operations.
- Add a lightweight web application layer (FastAPI + server-rendered HTML) for high-volume review and approvals.

Rationale:

- The current approach is operationally strong but inefficient for triaging thousands of ambiguous entries.
- A web UI can provide filtering, bulk approve/reject actions, and safer human-in-the-loop workflow.

Architecture constraints for UI:

- UI must not bypass planner/executor safety gates.
- UI actions must write to manifest/review state, then trigger the same validated execution pipeline as CLI.
- Dry-run remains default for any execution action started from UI.
- UI must preserve one-provider-ID-per-movie-or-series rule and no `.nfo` rule.

## Execution Backlog

## P0 - Critical Path (Release Blocking)

### 1. Add rename models (foundation)

Goal:

- Introduce shared data contracts for planning and execution.

Deliverables:

- `RenameEntry` model.
- `RenameManifest` model.
- Stable schema fields: source path, target path, reason, confidence, provider linkage, batch metadata.

Acceptance criteria:

- Models are fully typed and validated.
- Models are reused by planners, executors, and reporting/summary outputs.

### 2. Implement planners layer

Goal:

- Create planners package for validated rename manifest generation.

Deliverables:

- planners module with manifest builder service.
- Manifest schema serialization to `data/workspace/manifests`.
- Validation gate before a manifest can be marked executable.

Acceptance criteria:

- Planner accepts parsed and validated media items as input.
- Planner output is deterministic and fully serializable.
- Planner rejects invalid, ambiguous, or unresolved entries.

### 3. Implement executors layer

Goal:

- Create executors package for safe batch rename execution from manifest only.

Deliverables:

- Dry-run executor (default behavior).
- Explicit opt-in mode for real filesystem changes.
- Batch rollback log for each attempted operation.
- Collision and destination-exists checks.

Acceptance criteria:

- No rename path bypasses manifest input.
- Dry-run performs no filesystem mutations.
- Errors are logged with enough context for replay or manual rollback.

### 4. Add CLI commands for rename workflow

Goal:

- Make parse -> plan -> execute flow explicit in CLI.

Deliverables:

- `plan-rename` command.
- `execute-rename` command.
- Optional `validate-manifest` command.

Acceptance criteria:

- `execute-rename` fails fast when manifest is missing or invalid.
- Real execution requires explicit flag and cannot happen by default.
- Commands produce clear user-facing summaries and output paths.

### 5. Define CLI + UI architecture contract (ADR)

Goal:

- Lock down integration boundaries before implementing the web layer.

Deliverables:

- Architecture decision record describing CLI responsibilities vs UI responsibilities.
- Clear service-level interfaces reusable by both CLI and web app.
- Security model for local deployment (auth mode, CSRF policy, trusted network assumptions).

Acceptance criteria:

- No duplicated business logic between CLI and UI entrypoints.
- Planner/executor remain single source of truth for mutations.
- Threat model and operational assumptions are explicitly documented.

## P1 - Important Follow-Up

### 5. Complete report exports

Goal:

- Extend reporting outputs for operations and review.

Deliverables:

- CSV reporter for review and unresolved datasets.
- Optional manifest execution summary report format (JSON first, CSV optional).

Acceptance criteria:

- Export commands produce valid files for the same source dataset.
- Output clearly marks unresolved and manual-review entries.

### 6. Improve operational logging for long runs

Goal:

- Strengthen observability for large-library execution.

Deliverables:

- Structured per-command start/finish log events with elapsed time.
- Per-run correlation ID added to log context.
- Optional file log sink in `data/workspace/logs` (alongside stdout).

Acceptance criteria:

- Long runs are traceable end-to-end from one run identifier.
- Operators can inspect logs after command completion without terminal history.

### 7. CLI user-friendliness improvements

Goal:

- Improve command ergonomics and feedback quality.

Deliverables:

- Consistent help text with practical examples for key commands.
- Exit-code policy documentation (success, validation warning mode, fatal failure).
- Optional `--no-html`/`--no-json` report switches for parse workflow.

Acceptance criteria:

- Typical operator flow is understandable from `--help` output only.
- Report generation behavior is explicit and configurable.

### 8. Implement review and approval web UI (FastAPI + HTML)

Goal:

- Enable scalable manual triage and approval for high-volume rename decisions.

Deliverables:

- FastAPI app with pages for review-needed and unresolved items.
- Search, filtering, sorting, and pagination for large datasets.
- Bulk actions: approve, reject, defer, add note/reason.
- Manifest preview view (before/after paths, provider ID, confidence, risk flags).
- Trigger endpoints for planner run and executor dry-run.

Acceptance criteria:

- Operator can process large review sets significantly faster than file-by-file edits.
- Every action is auditable and persisted (who/when/what changed).
- UI never executes real rename without explicit confirmation and safety checks.

## P2 - Maintenance and Consistency

### 9. Align test structure naming

Goal:

- Remove directory naming mismatch in tests.

Deliverables:

- Align `tests/parses` with `src/parsers` naming.
- Keep imports and test discovery stable.

Acceptance criteria:

- Test paths and source paths map cleanly.
- No test collection regressions.

### 10. Tighten type-checking policy incrementally

Goal:

- Improve pyright strictness where safe.

Deliverables:

- Revisit unknown-type reporting settings for new modules first (planners/executors).
- Add targeted annotations in weaker areas identified during implementation.

Acceptance criteria:

- New critical modules ship with stronger type coverage.
- Type errors remain actionable and low-noise.

### 11. Documentation completeness for operators

Goal:

- Ensure docs match real workflow and reduce onboarding friction.

Deliverables:

- Add rename workflow docs after phases 6 and 7 are implemented.
- Add troubleshooting section for provider keys, cache behavior, and unresolved matches.
- Add sample end-to-end command sequence (scan -> parse -> plan -> execute dry-run).
- Add web UI operator guide: run locally, review workflow, and safety model.

Acceptance criteria:

- New operator can run full safe workflow from docs without guessing.
- Documentation is consistent with current CLI and report outputs.

## Recommended Implementation Order

1. Rename models and schema.
2. Planner service and manifest generation.
3. Executor service with default dry-run.
4. CLI integration for plan and execute commands.
5. CLI + UI architecture ADR.
6. Planner and executor test suite.
7. CSV reporting extensions.
8. Logging and CLI UX improvements.
9. FastAPI + HTML review UI.
10. Final documentation pass for rename workflow and UI operations.

## Test Strategy for Remaining Phases

Required tests for planner and executor features:

- Valid manifest generation from clean parsed inputs.
- Manifest rejection for unresolved or conflicting entries.
- `execute-rename` dry-run confirms zero filesystem mutations.
- `execute-rename` hard-fails without explicit execution flag.
- Batch failure logging and rollback log integrity.
- End-to-end CLI flow on fixture library data.
- UI integration tests for approval actions and manifest state transitions.
- UI-to-executor dry-run flow tests (no filesystem mutations).

## Definition of Done for Rename Workflow

Rename workflow is considered complete only when all items below are true:

- Manifest generation exists and is mandatory before execution.
- Rename execution supports dry-run by default.
- Real execution requires explicit opt-in.
- Rollback logging is produced for each batch run.
- CLI commands for plan and execute are documented and tested.
- End-to-end tests verify safe behavior under failure conditions.

## Operational Update Routine

When a task starts:

- Move it to In Progress in this file or related issue tracking.
- Link implementation PRs and related tests.

When a task completes:

- Mark as Done and add short verification notes.
- Record follow-up debt as a new backlog item with priority.

Keep this file as the single practical roadmap for development execution.
