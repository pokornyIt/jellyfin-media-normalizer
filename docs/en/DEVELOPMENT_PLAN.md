# Development Plan

[English](DEVELOPMENT_PLAN.md) | [Čeština](../cs/DEVELOPMENT_PLAN.md)

This document tracks implementation status and next steps for jellyfin-media-normalizer.

It should be updated continuously and used as the practical execution checklist for upcoming phases.

## Current State Snapshot (2026-07-19)

Verified as implemented and stable:

- Scan pipeline (filesystem inventory).
- Parse and classification pipeline (movies, TV episodes, unknown).
- Validation pipeline (structure, consistency, confidence scoring).
- Basic provider lookup transport (embedded ID -> cache -> online resolver chain).
- Reporting: JSON review report, unresolved JSON report, review HTML report, unresolved HTML report.
- Runtime safety defaults, including dry-run default setting.
- Local quality gates: ruff, pyright, pytest, pre-commit hooks.

Verified quality status:

- `uv run pytest -q`: 466 passed.
- `uv run ruff check src tests`: passed.
- `uv run pyright`: 0 errors.

Main missing product capabilities:

- Provider lookup still accepts the first online result with fixed confidence. Reviewable candidates, explainable
  scoring, ambiguity thresholds, episode-title corroboration, and trusted cache provenance are not implemented.
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
| 5     | Provider ID lookup                    | Partial                          |
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
- UI actions must write to persisted review or manifest state and reuse the same application services as the CLI.
- The first UI may trigger dry-run but has no endpoint for real rename execution; real execution remains CLI-only.
- UI must preserve one-provider-ID-per-movie-or-series rule and no `.nfo` rule.
- The first UI is unauthenticated, binds to a configurable address with a `0.0.0.0` default, and is supported only on
  a trusted machine or private LAN. Public Internet exposure is unsupported.

Container release contract:

- Build, smoke-test, and publish only `linux/amd64` images for the WSL environment and target Synology DS925+ and
  DS723+ devices.
- Do not publish ARM, 32-bit, or multi-platform image manifests in the first release.
- Keep `platform` out of Compose so unsupported hosts fail instead of silently using emulation.
- Keep the Dockerfile reasonably portable and add advanced native and cross-build examples, clearly marked as
  best-effort and unsupported.
- Keep the long-running `app` media mount explicitly read-only. Provide a separate one-shot `executor` under the
  `execution` profile with an explicit writable mount, no network, no web port, and no restart.
- Forbid variable media-mount modes. Require an explicit execution CLI flag and a global workspace execution lock in
  addition to profile activation.

## Execution Backlog

## P0 - Critical Path (Release Blocking)

### 1. Implement reviewable provider candidate selection

Goal:

- Replace first-result matching with the accepted deterministic provider-selection policy.

Deliverables:

- Multiple-candidate provider responses with selection provenance and scoring explanations.
- Versioned policy constants for normal score, title similarity, candidate lead, and sole-candidate thresholds.
- Exact movie-year and reliable TV input-year gates.
- Deterministic first, middle, and last episode-title corroboration for eligible yearless TV series.
- Policy-aware cache reuse that distinguishes approved selections from unproven cached candidates.
- Persisted `ready_for_approval` state without implicit rename approval.

Acceptance criteria:

- API result order never determines provider selection by itself.
- Tests cover threshold boundaries, year disagreement, close candidates, sole candidates, provider fallback, episode
  corroboration, and missing episode coordinates.
- Episode lookups never create episode-level provider IDs.
- Manual overrides remain explicit and auditable; legacy or unproven cache entries require rescoring or review.

### 2. Add rename models (foundation)

Goal:

- Introduce shared data contracts for planning and execution.

Deliverables:

- `RenameEntry` model.
- `RenameManifest` model.
- Stable schema fields: source path, target path, source fingerprint, reason, confidence, provider linkage, and batch
  metadata.
- Canonical manifest serialization with a SHA-256 digest.

Acceptance criteria:

- Models are fully typed and validated.
- Models are reused by planners, executors, and reporting/summary outputs.
- Symbolic links cannot be represented as executable rename sources.

### 3. Implement planners layer

Goal:

- Create planners package for validated rename manifest generation.

Deliverables:

- planners module with manifest builder service.
- Manifest schema serialization to `data/workspace/manifests`.
- Validation gate before a manifest can be marked executable.
- File fingerprints from relative path, entry type, size, and modification time.
- Directory tree digests that include opaque membership for ignored children without opening or modeling them.

Acceptance criteria:

- Planner accepts parsed and validated media items as input.
- Planner output is deterministic and fully serializable.
- Planner rejects invalid, ambiguous, or unresolved entries.
- Planner rejects every symbolic link and any planned directory containing one.

### 4. Implement executors layer

Goal:

- Create executors package for safe batch rename execution from manifest only.

Deliverables:

- Dry-run executor (default behavior).
- Explicit opt-in mode for real filesystem changes.
- Durable per-operation audit with confirmed successful, failed, pending, and uncertain states.
- Immutable JSON rollback-manifest generation from confirmed successful operations in reverse execution order.
- Collision and destination-exists checks.
- Source-fingerprint checks during dry-run, before each batch, and before each operation.
- Stable changed-source failure codes and linkage of successful dry-run to the exact manifest digest.
- Rollback entries linked to their original operations with reverse paths, fingerprints, expected absent targets,
  sequence, and recovery reasons.
- A global workspace execution lock shared by rename and rollback execution.

Acceptance criteria:

- No rename path bypasses manifest input.
- Dry-run performs no filesystem mutations.
- Errors are logged with enough context for replay or manual rollback.
- Any source mismatch stops the complete execution run and requires a newly approved workflow from scan through
  dry-run; the executor never refreshes fingerprints in place.
- Destination safety is rechecked independently at planning, dry-run, and immediately before execution.
- The first operation failure stops the complete run without automatic rollback.
- Rollback uses the normal executor, mandatory dry-run, explicit confirmation, no-overwrite checks, and a separate
  audit; execution never mutates the rollback manifest.
- Concurrent real rename or rollback execution fails before the first filesystem mutation.

### 5. Add CLI commands for rename workflow

Goal:

- Make parse -> plan -> execute flow explicit in CLI.

Deliverables:

- `plan-rename` command.
- `execute-rename` command.
- Optional `validate-manifest` command.
- CLI flow to inspect, dry-run, and explicitly execute generated rollback manifests through the same executor.

Acceptance criteria:

- `execute-rename` fails fast when manifest is missing or invalid.
- Real execution requires explicit flag and cannot happen by default.
- Commands produce clear user-facing summaries and output paths.
- Failure output identifies the rollback manifest and distinguishes completed, failed, pending, and uncertain work.

### 6. Define CLI + UI architecture contract (ADR)

Goal:

- Lock down integration boundaries before implementing the web layer.

Deliverables:

- Architecture decision record describing CLI responsibilities vs UI responsibilities.
- Clear service-level interfaces reusable by both CLI and web app.
- Initial deployment contract covering configurable binding, the trusted private-network assumption, warning outside
  loopback, and the absence of a real-execution UI endpoint.
- Boundary for a later authentication and remote-access hardening add-on.

Acceptance criteria:

- No duplicated business logic between CLI and UI entrypoints.
- Planner/executor remain single source of truth for mutations.
- The initial trusted-network assumptions and unsupported public exposure are explicitly documented.

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
- Every action is persisted and auditable with its time, change, and single local-operator actor.
- UI exposes planner and dry-run actions but no endpoint for real rename execution.
- The configurable bind address defaults to `0.0.0.0` and non-loopback startup produces a visible warning.

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
- Document the supported AMD64 image in the operator quick start and place unsupported native and `buildx` source
  build examples in advanced documentation.
- Document normal read-only Compose startup separately from the explicit one-shot execution-profile command.

Acceptance criteria:

- New operator can run full safe workflow from docs without guessing.
- Documentation is consistent with current CLI and report outputs.
- Documentation never presents an untested architecture as supported.
- The normal quick start cannot be mistaken for a writable-media deployment.

### 12. Add authenticated remote-access deployment

Goal:

- Harden access after the functional single-operator UI is complete.

Possible scope:

- Single-operator authentication, sessions, and CSRF protection.
- HTTPS reverse-proxy guidance and trusted-proxy handling.
- Optional broader account or role support if a concrete need appears.
- Optional Synology account integration as a non-required enhancement.

Acceptance criteria:

- The add-on does not become a dependency of the trusted private-network UI.
- Any newly supported remote-access mode has explicit security and deployment documentation.

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
11. Optional authenticated remote-access hardening.

## Test Strategy for Remaining Phases

Required tests for planner and executor features:

- Valid manifest generation from clean parsed inputs.
- Manifest rejection for unresolved or conflicting entries.
- Manifest and directory-digest determinism across repeated scans of unchanged fixtures.
- Rejection of symbolic links without following their targets.
- Detection of changed paths, entry types, sizes, modification times, and directory membership.
- Rejection of a dry-run result created for a different manifest digest.
- Rejection of concurrent execution while the global workspace execution lock is held.
- `execute-rename` dry-run confirms zero filesystem mutations.
- `execute-rename` hard-fails without explicit execution flag.
- Stop-on-failure behavior, durable audit states, rollback-manifest ordering, and rollback-manifest integrity.
- Rollback refusal when its source fingerprint changes or its target exists.
- End-to-end CLI flow on fixture library data.
- UI integration tests for approval actions and manifest state transitions.
- UI-to-executor dry-run flow tests (no filesystem mutations).
- UI route tests proving that no real rename endpoint exists in the initial release.

## Definition of Done for Rename Workflow

Rename workflow is considered complete only when all items below are true:

- Manifest generation exists and is mandatory before execution.
- Rename execution supports dry-run by default.
- Real execution requires explicit opt-in.
- The first failure stops the run and produces a durable audit plus an immutable rollback manifest for confirmed
  successful operations.
- Rollback requires its own successful dry-run and explicit opt-in through the normal executor.
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
