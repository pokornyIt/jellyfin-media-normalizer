# Development Plan

[English](DEVELOPMENT_PLAN.md) | [Čeština](../cs/DEVELOPMENT_PLAN.md)

This document tracks verified implementation status and the practical backlog for jellyfin-media-normalizer. Product
rules come from [PROJECT-DESCRIPTION.md](PROJECT-DESCRIPTION.md), while accepted direction and rationale come from
[PRODUCT_DEVELOPMENT_BRIEF.md](PRODUCT_DEVELOPMENT_BRIEF.md).

## Current State Snapshot (2026-07-19)

Verified current capabilities:

- supported video-file scanning;
- flat per-file parsing and classification into movie, TV episode, or unknown;
- per-file structural validation and confidence scoring;
- basic embedded-ID, JSON-cache, and online-provider resolver chain;
- JSON and HTML review and unresolved reports;
- configured quality gates with Ruff, Pyright, pytest, and pre-commit.

Latest recorded verification:

- `uv run pytest -q`: 466 passed;
- `uv run ruff check src tests`: passed;
- `uv run pyright`: 0 errors.

These dated results are evidence for that snapshot, not a claim that the target product workflow is complete.

<!-- markdownlint-disable MD013 -->
| Capability                            | Status                                                |
| ------------------------------------- | ----------------------------------------------------- |
| Inventory and scan                    | Partial: supported video files only                   |
| Classification and entity grouping    | Partial: flat file classification only                |
| Name normalization                    | Partial: basic filename parsing only                  |
| Validation                            | Partial: per-file checks; grouped consistency missing |
| Provider lookup and selection         | Partial: resolver chain accepts the first result      |
| Rename planning                       | Not started                                           |
| Batch rename and rollback execution   | Not started                                           |
| Static review exports                 | Partial: JSON and HTML implemented; CSV missing       |
| Interactive review and approval UI    | Not started                                           |
<!-- markdownlint-enable MD013 -->

The current release is analysis-only. A dry-run configuration default exists, but no rename planner or executor
exists yet, so it must not be presented as implemented rename safety.

## Non-Negotiable Constraints

- Never read, parse, create, modify, delete, or target `.nfo` files with standalone operations. An `.nfo` file may
  move only as an ignored child of a renamed parent directory.
- Store at most one selected provider ID per movie or TV series and never store episode-level IDs.
- Treat every symbolic link as unsupported and incompatible. Never follow, model, plan, or rename it, and do not
  allow review to override the rejection.
- Every rename must originate from an approved, validated, persisted manifest.
- Dry-run remains the default; real execution requires explicit opt-in.

## Release Architecture

- CLI remains the source of truth for automation and real execution.
- A lightweight FastAPI application with server-rendered HTML provides high-volume review and approval.
- UI and CLI reuse the same application services, state transitions, planner, and executor boundaries.
- The first UI is unauthenticated, defaults to `0.0.0.0`, and is supported only on a trusted machine or private LAN.
  It may trigger planning and dry-run but has no real-execution endpoint.
- SQLite stores mutable workflow state. Immutable rename and rollback manifests remain JSON artifacts.
- Parsers and entity services remain media-server neutral. `NamingProfile` validates media-server compatibility;
  `OutputScheme` renders target names. P0 ships explicit Jellyfin implementations with one fixed output scheme and no
  dynamic third-party plugin discovery or configurable templates.
- Docker Compose is the primary operator path. The long-running app uses `/media:ro`; a separate one-shot executor
  in the `execution` profile uses `/media:rw`, no network, no web port, and a global workspace execution lock.
- Official images target only `linux/amd64`, covering WSL, Synology DS925+, and Synology DS723+.

## P0 - Operator-Ready Release

### P0.1 Correct The Analysis Model And Persist Workflow State

Goal:

- Establish trustworthy entities and durable human-in-the-loop state before provider selection or planning.

Deliverables:

- Inventory directories, supported videos, supported subtitles, ignored membership, depth-limit violations, and
  symbolic links without opening ignored files.
- Add typed movie, TV series, episode, and associated-file entities plus directory-role classification.
- Keep parsed and grouped entity fields independent of Jellyfin target-name formatting.
- Group files into entities and integrate grouped consistency validation into the production workflow.
- Enforce the accepted mixed-root, strict TV layout, multipart, version, subtitle, and incompatible-directory rules.
- Add SQLite persistence for runs, entities, candidates, corrections, approvals, notes, workflow transitions, and
  audit metadata with versioned migrations.
- Record a focused persistence ADR with the implementation schema and migration boundary.

Acceptance criteria:

- Every discovered path is managed, ignored with opaque membership, or reported incompatible.
- Failed, ambiguous, incompatible, and low-confidence entities cannot become implicitly approved.
- State survives restart and operators never need to edit generated JSON, YAML, or SQLite data directly.
- Tests cover grouping, mixed content, maximum depth, direct-root warnings, subtitles, and symbolic-link rejection.

### P0.2 Implement Baseline Reviewable Provider Selection

Goal:

- Replace first-result matching with the accepted deterministic first-release policy.

Deliverables:

- Multiple provider candidates with provenance and scoring explanations.
- Versioned constants for score, title similarity, candidate lead, sole-candidate, and year gates.
- Exact movie-year and reliable TV input-year handling, embedded and manual selection precedence, and TMDb/TVDB
  fallback behavior.
- Policy-aware cache reuse and persisted `ready_for_approval` state without implicit approval.
- Yearless series that fail title-only thresholds remain in review; episode corroboration is not part of P0.

Acceptance criteria:

- API ordering, popularity, artwork, and metadata completeness never decide identity.
- Boundary, year-conflict, close-candidate, sole-candidate, provider-fallback, and cache-provenance tests pass.
- Manual overrides are explicit and auditable, and no episode-level provider ID is created.

### P0.3 Implement The Minimum Human Review UI

Goal:

- Make persistent review practical before rename planning is introduced.

Deliverables:

- FastAPI pages for review-required, ready-for-approval, and unresolved queues.
- Search, filtering, sorting, and pagination for large libraries.
- Corrections, provider selection, approve, reject, defer, notes, and guarded bulk actions.
- Visible trusted-network warning and no endpoint for real filesystem execution.
- A focused UI/service-boundary ADR created with the implemented interfaces.

Acceptance criteria:

- Every state change uses shared services, is validated, persists across restart, and is auditable.
- Bulk actions reject mixed or ineligible selections instead of bypassing item-level rules.
- Route tests prove that the first UI exposes no real-execution operation.

### P0.4 Add The Shared Rename Manifest And Planner

Goal:

- Generate deterministic, reviewable plans only from approved entities.

Deliverables:

- Versioned `RenameManifest` and `RenameEntry` models supporting `rename` and `rollback` manifest kinds.
- Pluggable `NamingProfile` and `OutputScheme` contracts with explicit registries, `JellyfinNamingProfile`, and one
  fixed `JellyfinDefaultOutputScheme`. Parsers must not render output paths; configurable templates remain P3.
- Canonical JSON serialization and SHA-256 digest.
- Source file fingerprints and directory tree digests with opaque ignored membership.
- Deterministic targets for folders, videos, supported subtitles, multipart components, and versions.
- Immutable manifest persistence and a human-readable UI preview grouped by logical batch. The preview shows current
  and proposed paths, associated files, provider identity, warnings, validation failures, and the exact digest being
  approved; raw JSON is a downloadable artifact rather than the primary review view.

Acceptance criteria:

- Planner rejects unresolved, unapproved, invalid, incompatible, conflicting, or symbolic-link-containing input.
- Repeated planning over unchanged approved state produces equivalent entries and digest.
- Every target complies with the accepted Jellyfin naming and structure rules.
- The manifest stores identifiers and versions for both the naming profile and output scheme, and rendered output
  passes shared path, collision, provider-ID, `.nfo`, and safety validation.

### P0.5 Implement Safe Execution And Rollback

Goal:

- Execute only verified manifests with explicit control and recoverable partial-failure evidence.

Deliverables:

- Default dry-run and explicit real-execution mode.
- Manifest integrity, source fingerprint, collision, target-absence, and global-lock checks at documented boundaries.
- Durable per-operation states for successful, failed, pending, and uncertain work with stop on first failure.
- Immutable rollback manifest generated only from confirmed successful operations, using the shared schema, reverse
  list order, original-operation linkage, current source fingerprints, and its own digest.
- Separate rollback dry-run, confirmation, and audit; no automatic rollback and no shell-command manifest.
- A focused execution-safety ADR created with the concrete locking and audit design.

Acceptance criteria:

- No mutation path bypasses a validated manifest or writes during dry-run.
- Changed sources, existing targets, collisions, invalid digests, and concurrent execution fail before unsafe change.
- Execution never mutates its input manifest or overwrites an existing path.
- Failure tests prove audit classification and safe rollback-manifest generation.

### P0.6 Integrate CLI And UI Workflow Operations

Goal:

- Expose the shared planner and executor services through clear operator workflows.

Deliverables:

- CLI commands to plan, validate, dry-run, and explicitly execute rename and rollback manifests.
- UI manifest preview and exact-digest approval, planner trigger, dry-run results, and audit history.
- Clear summaries, artifact paths, failure codes, and links between original and rollback runs.

Acceptance criteria:

- Real execution remains CLI-only and requires an explicit flag.
- CLI and UI produce consistent state transitions and results through shared services.
- End-to-end fixture tests cover analysis through approval, planning, dry-run, execution failure, and rollback dry-run.

### P0.7 Package The Supported Compose Deployment

Goal:

- Provide the supported single-operator deployment without weakening filesystem safety.

Deliverables:

- Non-root production Dockerfile, `.dockerignore`, Compose file, healthcheck, and example environment.
- Long-running app with read-only media and persistent workspace.
- One-shot execution-profile service with explicit writable media, no network, no web port, and no restart.
- Reproducible `linux/amd64` build, smoke test, image metadata, and release workflow.
- Focused deployment ADR covering mounts, permissions, upgrade, backup, and recovery boundaries.

Acceptance criteria:

- Normal `docker compose up` cannot mutate the media library.
- Unsupported platforms fail normally without hidden emulation.
- Workspace database and artifacts survive upgrades, with tested migration and backup guidance.

### P0.8 Complete Operator Documentation And End-To-End Verification

Goal:

- Make the supported workflow usable without undocumented knowledge.

Deliverables:

- Compose-first quick start, setup, review, execution, rollback, backup, upgrade, and troubleshooting guidance.
- Separate read-only application and explicit writable executor examples.
- Representative large-library fixture and performance validation.
- Updated English and Czech README and documentation pairs reflecting actual behavior.

Acceptance criteria:

- A new operator can complete the safe workflow without editing generated state files or guessing commands.
- Documentation never presents planned behavior, unsupported architectures, or public exposure as supported.
- Repository quality gates and end-to-end workflow tests pass.

## P1 - Important Follow-Up

### P1.1 Add Episode-Title Corroboration

- Measure the yearless-series review queue first.
- If justified, implement the accepted deterministic two-or-three-episode sampling and 75/25 scoring policy.
- Cache episode evidence reproducibly and never create episode-level provider IDs.

### P1.2 Complete CSV And Execution Exports

- Add CSV review and unresolved exports from the same persisted dataset.
- Add a JSON execution summary; add CSV only if it provides concrete operator value.

### P1.3 Improve Long-Run Observability

- Add run correlation IDs, structured start and finish events, elapsed time, progress, and optional persistent logs.
- Keep secrets and credential-bearing URLs out of diagnostics.

### P1.4 Improve CLI Ergonomics

- Add consistent examples, documented exit codes, report switches, and actionable summaries.
- Keep safety-critical flags explicit and avoid convenience defaults that enable mutation.

## P2 - Maintenance And Optional Hardening

### P2.1 Align Test Structure Naming

- Align the existing `tests/parses` mismatch with `src/parsers` without collection regressions.

### P2.2 Tighten Type Checking Incrementally

- Strengthen new critical modules first and add targeted annotations where they remain useful and low-noise.

### P2.3 Add Authenticated Remote Access

- Treat authentication, sessions, CSRF, trusted-proxy handling, and HTTPS reverse-proxy guidance as an add-on.
- Keep Synology account integration optional and do not make it a dependency of trusted private-network operation.

## P3 - Future Wishlist (Not Release Blocking)

### P3.1 Add More Media-Server Naming Profiles

- Research and specify a Plex naming profile, including provider tags and episode naming, before implementation.
- Treat Emby as a Jellyfin-profile alias only if compatibility tests prove identical required output; otherwise add a
  separate implementation.
- Consider other profiles only when they fit the core model and preserve all safety rules.
- Exclude Kodi workflows that require application-managed `.nfo` files.

### P3.2 Generalize Language And Localization Logic

- Separate metadata locale, display-title fallback, audio markers, and subtitle markers.
- Keep Czech and `CZ` as first-release defaults while designing validated language tags and filename mappings.
- Feed these choices into `OutputScheme` rather than branching parsers or server profiles by language.

### P3.3 Add Constrained Naming Templates

- Extend `OutputScheme` with named presets and typed tokens, for example
  `{{year}} - {{movie_title}} - {{provider_tag}} - {{language}}`, with preview and validation.
- Reject arbitrary code, invalid paths, collisions, ambiguous output, and templates that bypass profile or safety rules.

## Recommended Implementation Order

1. Correct entity grouping and add SQLite workflow persistence.
2. Implement baseline reviewable provider selection.
3. Implement the minimum persistent review UI.
4. Add the shared manifest schema, planner, and UI preview.
5. Add safe dry-run, execution, audit, and rollback.
6. Integrate CLI and UI operations through shared services.
7. Package and verify the supported Compose deployment.
8. Complete operator documentation and end-to-end verification.
9. Measure production friction before selecting P1, P2, or wishlist work.

## Cross-Cutting Test Strategy

- Domain grouping, directory roles, depth limits, subtitles, multipart media, versions, mixed content, and symlinks.
- SQLite migrations, restart persistence, valid state transitions, audit history, and concurrent update handling.
- Provider threshold boundaries, year conflicts, fallback, ambiguity, cache provenance, and explicit override behavior.
- UI filtering, pagination, corrections, approvals, guarded bulk actions, and absence of real execution routes.
- Manifest and tree-digest determinism, changed-source detection, collision checks, and symbolic-link rejection.
- Dry-run with zero mutations, explicit real-execution opt-in, global locking, stop-on-failure, and durable audit
  states.
- Shared-schema rollback ordering, integrity, changed-source rejection, target-exists rejection, and separate audit.
- End-to-end CLI and UI flows over representative fixtures without live APIs or destructive external filesystems.

## Operator-Ready Definition Of Done

- The supported Compose application starts without host Python setup and mounts media read-only by default.
- Entities, provider candidates, corrections, approvals, notes, and audit state persist across restart.
- The minimum UI makes review practical and exposes no real-execution endpoint.
- An approved, validated, immutable manifest and successful dry-run are mandatory before execution.
- Real execution is explicit, CLI-only, locked, audited, stops on failure, and has a documented rollback path.
- English and Czech operator documentation covers setup through recovery and matches tested behavior.

## Operational Update Routine

When work starts, mark the related backlog item in progress in the issue tracker and link its implementation PR and
tests. When it completes, record verification and create separate follow-up issues for remaining debt. Keep dated
verification evidence separate from product-completeness claims.
