# Development Plan

This document tracks the next implementation steps for jellyfin-media-normalizer.

It is intended to be updated during normal development and used as the execution
checklist for upcoming phases.

## Current State Snapshot

Implemented and stable:

- Scan pipeline (filesystem inventory).
- Parse and classify pipeline (movies and TV patterns).
- Validation pipeline and confidence scoring.
- Provider lookup and cache integration.
- JSON and review-focused reporting.
- Dry-run default in runtime settings.

Main gap:

- Rename planning and execution phases are not yet fully implemented
  as first-class layers.

## Non-Negotiable Constraints

All development tasks must preserve these rules:

- Never process or generate .nfo files.
- Exactly one provider ID per movie or TV series entity.
- Never rename without a validated plan.
- Never bulk rename without a generated manifest.
- Dry-run must remain the default execution mode.

## Execution Backlog

## P0 - Critical Path (Release Blocking)

### 1. Implement planners layer

Goal:

- Create planners package for validated rename manifest generation.

Deliverables:

- planners module with manifest builder service.
- Manifest schema and serialization to workspace/manifests.
- Validation gate before any manifest is marked executable.

Acceptance criteria:

- Planner takes parsed and validated media items as input.
- Planner output is deterministic and fully serializable.
- Planner rejects invalid, ambiguous, or unresolved entries.

### 2. Implement executors layer

Goal:

- Create executors package for safe batch rename execution from manifest only.

Deliverables:

- Dry-run executor (default behavior).
- Explicit opt-in mode for real filesystem changes.
- Batch rollback log for each attempted operation.

Acceptance criteria:

- No rename path bypasses manifest input.
- Dry-run performs no filesystem mutations.
- Errors are logged with enough context for replay or manual rollback.

### 3. Add CLI commands for rename workflow

Goal:

- Make parse -> plan -> execute flow explicit in CLI.

Deliverables:

- plan-rename command.
- execute-rename command.
- Optional validate-manifest command.

Acceptance criteria:

- execute-rename fails fast when manifest is missing or invalid.
- Real execution requires explicit flag and cannot happen by default.
- Commands produce clear user-facing summaries and output paths.

## P1 - Important Follow-Up

### 4. Add rename models

Goal:

- Introduce shared data contracts for planning and execution.

Deliverables:

- RenameEntry model.
- RenameManifest model.
- Stable schema fields for source path, target path, reason, confidence,
  and provider linkage.

Acceptance criteria:

- Models are fully typed and validated.
- Models are reused across planners, executors, and reporters.

### 5. Complete report exports

Goal:

- Extend reporting outputs for operations and review.

Deliverables:

- CSV reporter.
- HTML reporter.

Acceptance criteria:

- Export commands produce valid files for the same source dataset.
- Output clearly marks unresolved and manual-review entries.

### 6. Strengthen local quality gates

Goal:

- Enforce consistent quality checks before commits.

Deliverables:

- .pre-commit-config.yaml with ruff, pyright, and pytest hooks.
- Coverage policy in pytest configuration.

Acceptance criteria:

- Pre-commit checks pass on staged files.
- CI and local checks use the same baseline quality rules.

## P2 - Maintenance and Consistency

### 7. Align test structure naming

Goal:

- Remove directory naming mismatch in tests.

Deliverables:

- Align tests/parses with src/parsers naming.
- Keep imports and test discovery stable.

Acceptance criteria:

- Test paths and source paths map cleanly.
- No test collection regressions.

### 8. Tighten type-checking policy

Goal:

- Improve pyright strictness where safe for incremental adoption.

Deliverables:

- Review and adjust pyright unknown-type reporting settings.
- Add targeted type annotations in weak areas.

Acceptance criteria:

- New critical modules ship with strong type coverage.
- Type errors are actionable and not noisy.

## Recommended Implementation Order

1. Planner models and schema.
2. Planner service and manifest generation.
3. Executor service with default dry-run.
4. CLI integration for plan and execute commands.
5. Planner and executor test suite.
6. Reporting extensions (CSV and HTML).
7. Quality-gate hardening and cleanup tasks.

## Test Strategy for New Phases

Required tests for planner and executor features:

- Valid manifest generation from clean parsed inputs.
- Manifest rejection for unresolved or conflicting entries.
- execute-rename dry-run confirms zero filesystem mutations.
- execute-rename hard-fails without explicit execution flag.
- Batch failure logging and rollback log integrity.
- End-to-end CLI flow on fixture library data.

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
