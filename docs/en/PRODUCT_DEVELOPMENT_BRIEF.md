# Product Development Brief

[English](PRODUCT_DEVELOPMENT_BRIEF.md) | [Čeština](../cs/PRODUCT_DEVELOPMENT_BRIEF.md)

## Purpose Of This Document

This document defines a coherent product direction for `jellyfin-media-normalizer` before rename planning,
execution, and an interactive user interface are implemented.

It is intended to be used as the input for a later documentation realignment. After the decisions in this
document are accepted, the relevant parts should be reflected in:

- [Project Description](PROJECT-DESCRIPTION.md) for stable product scope and domain rules;
- [Development Plan](DEVELOPMENT_PLAN.md) for the implementation backlog and current status;
- [README](../../README.md) for installation and operator workflows;
- architecture decision records for persistence, UI deployment, and rename safety.

This brief describes the desired product. It does not claim that all described capabilities are already
implemented.

## Product Summary

`jellyfin-media-normalizer` should be a human-in-the-loop application for analyzing, reviewing, planning, and
safely normalizing a movie and TV library for Jellyfin.

The application should help an operator move from an inconsistent library to a clean and predictable structure
without requiring manual editing of JSON, YAML, cache files, or generated manifests.

The product is successful when an operator can:

1. select a media library;
2. scan it without changing any media files;
3. review detected movies, series, episodes, and related files;
4. correct parsing and provider matches in a user interface;
5. approve proposed changes;
6. generate and inspect an immutable rename manifest;
7. verify the manifest in dry-run mode;
8. explicitly execute approved changes;
9. inspect an audit log and recover from a partially failed batch.

## Primary User

The primary user is the owner or administrator of a large personal Jellyfin library stored on a NAS. The user is
comfortable running a local application but should not need to understand the internal data schema or edit
machine-generated files.

The application should remain scriptable for advanced users, but CLI knowledge must not be required for routine
review and approval work. The primary installation path should not require a host Python installation or manual
dependency management.

## Product Boundaries

### In Scope

- inventory of supported media and related files;
- classification into movies, TV series, episodes, extras, and unresolved items;
- parsing and normalization of file and folder names;
- validation at item, folder, movie, series, and episode-group level;
- provider candidate lookup and selection;
- persistent manual corrections and approvals;
- deterministic rename manifest generation;
- dry-run verification;
- controlled batch execution, audit logging, and rollback assistance;
- CLI automation and a local web interface for human review;
- reproducible container images and a Docker Compose configuration for normal operation.

### Out Of Scope

- `.nfo` generation or management;
- modification of media streams or embedded metadata;
- downloading artwork, subtitles, or other metadata;
- episode-level provider IDs in filenames;
- unattended acceptance of ambiguous provider matches;
- renaming directly from raw parser or provider output;
- acting as a general-purpose media server or Jellyfin replacement.

## Non-Negotiable Safety Rules

- Never read, parse, create, modify, delete, or target `.nfo` files with standalone operations. An `.nfo` file may
  move only as an ignored child of a renamed parent directory and never receives its own manifest entry.
- Store at most one selected provider ID on a movie or TV series entity.
- Never store provider IDs on episode entities or in episode filenames.
- Never rename from scan, parse, validation, or provider lookup output directly.
- Every filesystem change must originate from a validated, approved, and persisted manifest.
- Dry-run must be the default for both CLI and web workflows.
- Real execution must require an explicit confirmation separate from approval of the manifest.
- Destination collisions, missing sources, changed sources, and cross-filesystem moves must be checked before
  execution.
- Every attempted operation must be recorded in an audit log suitable for manual recovery.
- Low-confidence, conflicting, or ambiguous results must require human review.

## Required Domain Model

The current file-centered model is sufficient for scanning, but rename planning requires explicit media entities.
The implementation should introduce the following concepts before building the planner.

### Library Item

A discovered filesystem entry with its original path, type, size, timestamps, and optional content fingerprint.
Library items include supported video files and associated files that may need to move with a video.

### Movie

A movie entity groups its main video, optional alternate versions or extras, associated files, containing folder,
parsed titles, year, and one selected provider ID.

### TV Series

A TV series entity owns series-level identity, display title, source folder, seasons, episodes, and one selected
provider ID. Provider lookup must use the series identity, not the episode title.

### Episode

An episode entity contains season and episode numbers, episode title, language information, main video, and
associated files. It never owns a provider ID.

### Associated File

Supported subtitle files must be linked to their owning video so they are not orphaned by a rename. The first
release supports `.srt`, `.ass`, `.ssa`, `.vtt`, and `.sub` files. Ownership requires either the same filename stem
as the video or that stem followed only by recognized language and subtitle qualifiers such as `cs`, `en`, `forced`,
`sdh`, `cc`, or `default`. Qualifiers are preserved when the video and subtitle are renamed. An orphaned subtitle
or a target-name collision requires review.

Other file types are ignored and receive no individual parse, validation, plan, or execution operation. They remain
inside a directory when that parent directory is renamed. `.nfo` files follow this ignored-child behavior but are
never read, modeled, or included as standalone manifest entries.

### Title Fields

The model must not use one string for every title purpose. At minimum it should distinguish:

- source title: text extracted from the existing filesystem;
- display title: human-readable title proposed for the final filename, preserving diacritics;
- lookup title: normalized text used only for search and comparison;
- series title and episode title: separate fields with separate ownership.

Normalization for lookup must never silently become the final filename.

### Provider Candidate And Selection

Online search should return provider candidates rather than immediately creating a final match. A candidate should
contain enough information for scoring and human review, including provider, ID, title, original title, year or
first-air date, media type, overview, and poster URL when available.

A selected provider match must record:

- the chosen candidate;
- confidence and scoring explanation;
- whether it was embedded, cached, automatically accepted, or manually selected;
- who or what selected it and when;
- the entity to which the selection belongs.

## Provider Matching Policy

Provider results must not be accepted solely because they are the first API result.

Automatic acceptance should require configurable but documented criteria, such as:

- compatible media type;
- normalized title similarity above a defined threshold;
- exact or acceptable year agreement for movies;
- a sufficient score difference between the best and second-best candidates;
- no conflict with an embedded or previously approved provider ID.

If the criteria are not met, the entity must enter review instead of receiving a final provider selection.

Embedded provider IDs may be trusted by default but must still be validated for syntax, provider compatibility,
and the one-ID-per-entity rule. The UI should allow the operator to replace an incorrect embedded selection before
planning.

## Validation Policy

Validation must operate at more than the individual-file level.

The production pipeline should include:

- field and syntax validation;
- folder and entity grouping validation;
- series-title consistency;
- duplicate season and episode detection;
- duplicate movie and alternate-version detection;
- provider-selection validation;
- target-path and collision validation;
- associated-file completeness checks.

Provider lookup may collect candidates for review, but an invalid entity must never become automatically approved
or executable.

Validation results should use stable machine-readable codes in addition to human-readable messages. This enables
reliable filtering, documentation, and UI actions without parsing English text.

## Target Operator Workflow

### 1. Initial Setup

The operator selects a library path and workspace path, configures provider credentials, and verifies read and write
permissions. Secrets must not be displayed after saving.

The application should provide a setup screen and equivalent CLI options. Manual shell export commands may remain
available for automation but must not be the only supported setup method.

For the normal installation path, the operator should only need Docker with Compose support, a checked-out release
or release bundle, a small environment file for deployment settings, and access to the media library. Installing
Python, `uv`, or project dependencies on the host must not be required.

### 2. Scan

A scan creates a persistent run with an identifier, timestamps, settings snapshot, summary, and discovered items.
The UI displays progress and allows the operator to leave and return without losing the run.

Scanning is read-only.

### 3. Analyze

The application parses, groups, validates, and searches provider candidates. Results are persisted so that review
does not depend on editing generated reports.

### 4. Review And Correct

The operator can search, filter, sort, and paginate results. For each entity, the operator can:

- edit parsed title, year, season, episode, and language fields;
- choose a provider candidate or enter a provider ID explicitly;
- approve, reject, or defer the proposed interpretation;
- add a note;
- apply safe bulk actions to equivalent items.

Every correction triggers relevant validation again.

### 5. Plan

Only approved and valid entities can enter a rename manifest. The planner generates deterministic source and target
paths, grouped into logical batches.

The operator reviews a before-and-after preview. Generated manifest files are machine artifacts and are not the
primary editing interface.

### 6. Dry-Run

Dry-run verifies current source state, target paths, permissions, collisions, batch ordering, and rollback data. It
must not modify the library.

A manifest can be executed only after a successful dry-run against the same relevant source state. If the library
changes, the manifest must be revalidated.

### 7. Execute And Audit

Real execution requires explicit confirmation and operates only on one approved manifest. The application records
each attempted operation and its result.

On partial failure, execution stops at a safe boundary and reports completed, pending, failed, and recoverable
operations. Rollback should use the audit log and must itself be logged.

## User Interface Direction

The recommended interface is a lightweight local web application using server-rendered HTML. The CLI and web UI
must be adapters over the same application services; neither may duplicate planner or executor logic.

The first useful UI should provide:

- setup and connection verification;
- run creation and progress;
- a dashboard with actionable counts;
- review queues for parse errors, provider ambiguity, duplicates, and unresolved items;
- inline editing and provider selection;
- bulk approve, reject, and defer actions;
- manifest preview;
- dry-run initiation and results;
- execution confirmation and audit history.

Static HTML and CSV reports remain useful as exports, but they are not the primary review workflow.

The default deployment should bind to localhost and assume a single local operator. Any documented LAN deployment
must define authentication, CSRF protection, secret handling, and trusted-network assumptions before it is treated
as supported.

## Container Deployment

Docker Compose should be the primary documented deployment method for operators. Native `uv` installation should
remain available for development, debugging, and advanced CLI automation.

The repository should provide:

- a production `Dockerfile` using the project's pinned Python runtime;
- a `.dockerignore` that excludes development caches, credentials, workspace data, and media files;
- a `compose.yaml` with safe defaults and documented environment variables;
- an example environment file containing placeholders only;
- a container healthcheck;
- versioned image metadata and release tags;
- startup, upgrade, backup, and troubleshooting instructions.

The production image should:

- contain runtime dependencies only;
- run as a non-root user;
- support configurable UID and GID behavior when required for NAS permissions;
- expose only the web application port;
- write mutable application data only to declared workspace or temporary paths;
- avoid privileged mode, host networking, and Docker socket access;
- use a clear entrypoint that can start the web application or run supported CLI commands.

The Compose configuration should separate media from application state:

- the media library is mounted at a stable container path such as `/media`;
- the workspace is mounted at a stable path such as `/workspace` and persists SQLite data, manifests, reports,
  audit records, and logs;
- the default analysis and review deployment mounts the media library read-only;
- enabling a read-write media mount requires an explicit execution-oriented configuration or profile;
- a read-write mount alone never bypasses application-level manifest, dry-run, validation, and confirmation gates;
- provider credentials are injected through environment variables or supported secret files and are never baked
  into the image.

The exact read-write activation mechanism should be documented in an architecture decision. The safe default must
be visible in both the Compose configuration and the operator documentation, not only enforced by application code.

Published images should target the architectures selected for supported development machines and NAS devices.
At minimum, the project must make an explicit decision about `linux/amd64` and `linux/arm64` support before the
first operator-ready release.

Container upgrades must preserve the workspace database and artifacts. Database schema migrations must run through
a versioned and recoverable process, with backup guidance provided before potentially incompatible upgrades.

## Persistence Strategy

Human decisions and workflow state should be stored in a small application database, with SQLite as the preferred
initial implementation. This avoids requiring a separate database service while supporting filtering, state
transitions, resumable review, and audit history.

Recommended storage responsibilities:

- SQLite: scan runs, entities, candidates, corrections, approvals, notes, workflow state, and audit metadata;
- JSON: versioned immutable rename manifests and portable machine-readable exports;
- CSV and HTML: optional human-readable exports;
- environment or protected settings storage: provider secrets;
- filesystem logs: operational diagnostics where configured.

JSON, YAML, and SQLite files must not be presented as normal operator editing interfaces.

## Workflow States

The application should use explicit states rather than inferring approval from missing errors. A minimal entity and
manifest lifecycle is:

```text
discovered
  -> analyzed
  -> review_required | ready_for_approval
  -> approved | rejected | deferred
  -> planned
  -> dry_run_verified
  -> executed | execution_failed
  -> rolled_back
```

Not every state applies to every object, but allowed transitions must be defined and validated. A user action,
automatic rule, or execution event causing a transition must be auditable.

## Delivery Plan

### Stage 0: Align Product Documentation

- Accept or amend the decisions in this brief.
- Resolve the open product decisions listed below.
- Update `PROJECT-DESCRIPTION.md`, `DEVELOPMENT_PLAN.md`, `README.md`, and `README.cs.md` so their terminology and
  phase status agree.
- Add architecture decisions for persistence, UI deployment, container safety, and manifest execution safety.

### Stage 1: Correct The Analysis Model

- Introduce movie, TV series, episode, and associated-file entities.
- Separate source, display, lookup, series, and episode titles.
- Group scanned files into entities.
- Integrate consistency validation into the production pipeline.
- Prevent failed or low-confidence entities from automatic approval.

### Stage 2: Make Provider Matching Reviewable

- Return multiple provider candidates.
- Add explainable scoring and ambiguity thresholds.
- Persist selected matches and manual corrections.
- Provide CLI commands for inspecting and selecting candidates until the UI is available.

### Stage 3: Implement Rename Planning

- Add versioned `RenameEntry` and `RenameManifest` models.
- Generate deterministic target paths for folders, videos, and supported associated files.
- Reject unresolved, unapproved, invalid, or conflicting entries.
- Persist immutable manifests and readable previews.

### Stage 4: Implement Safe Execution

- Add default dry-run execution.
- Verify source state and destination safety.
- Require explicit real-execution confirmation.
- Add batch boundaries, audit records, partial-failure handling, and rollback assistance.

### Stage 5: Implement The Human Review UI

- Add setup, dashboard, review, provider selection, and bulk actions.
- Add manifest preview, dry-run results, execution confirmation, and audit history.
- Keep all state changes behind the same services and validation gates used by the CLI.

### Stage 6: Package For Container Deployment

- Add the production Dockerfile, `.dockerignore`, Compose configuration, and example environment file.
- Run the production process as a non-root user with persistent workspace storage.
- Make the default media mount read-only and provide an explicit execution configuration for read-write access.
- Add healthchecks, image metadata, architecture targets, and reproducible release builds.
- Document startup, CLI usage in the container, upgrades, backups, permissions, and recovery.

### Stage 7: Operational Hardening

- Add resumable long-running jobs and clear progress reporting.
- Add run correlation IDs and persistent operational logs.
- Add end-to-end documentation, troubleshooting, backup guidance, and recovery exercises.
- Validate performance on a representative large library.

## Operator-Ready Milestone

The project should not be described as operator-ready until all of the following are true:

- an operator can start the supported application with Docker Compose without installing Python dependencies;
- the default container deployment mounts the media library read-only;
- an operator can complete setup without editing generated data files;
- movies, series, episodes, and supported associated files are represented correctly;
- ambiguous provider matches require review;
- corrections and approvals persist across restarts;
- a validated rename manifest is mandatory;
- dry-run proves that no filesystem changes occur;
- real execution requires explicit confirmation;
- collision and changed-source checks are enforced;
- every operation is audited;
- partial failures have a documented recovery path;
- the complete workflow is documented and tested on representative library fixtures.

## Documentation Realignment Checklist

When this brief is accepted, update the existing documents as follows.

### `PROJECT-DESCRIPTION.md`

- Make media entities and associated files part of the stable domain description.
- Clarify series title versus episode title.
- Clarify display-title preservation versus lookup normalization.
- Replace immediate provider matching with candidates, scoring, selection, and approval.
- Describe the persistent human-in-the-loop workflow.
- Update the architecture tree and phase descriptions.

### `DEVELOPMENT_PLAN.md`

- Correct the validation status: structural validation exists, but grouped consistency validation is not integrated.
- Mark provider lookup as implemented but provider selection quality as incomplete.
- Replace the current flat backlog with the delivery stages in this brief.
- Define the operator-ready milestone as the release target.
- Keep verification results dated and separate from product-completeness claims.

### `README.md` and `README.cs.md`

- Clearly label the current release as analysis-only until planning and execution exist.
- Replace manual `.env` export as the primary user setup once setup support exists.
- Make the Docker Compose workflow the primary operator quick start.
- Document safe read-only analysis and explicit read-write execution configurations separately.
- Add one end-to-end operator workflow when the corresponding commands are implemented.
- Explain which files are scanned, ignored, moved together, and never touched.
- Add troubleshooting for paths, provider credentials, unresolved candidates, and dry-run failures.

## Accepted Product Decisions

### Library Layout And Classification

- The application scans one configured library root containing both movies and TV series. The root is a neutral
  container; directories below it are classified from their content and structure.
- Directory roles are movie collection, series collection, TV series, season, and incompatible. Once classified,
  movie and series collection subtrees must remain homogeneous.
- Scanning descends through at most five directory levels below the root. Content beyond the limit is reported as
  incompatible instead of being silently omitted.
- A movie is a video file and does not require a dedicated folder. Its single provider ID belongs in the movie
  filename. Genre and collection folders remain organizational and do not receive provider IDs.
- A TV series owns a series folder with one provider ID and no year. The normalized structure below it is strictly
  `Season XX` followed by episode files and their supported associated files, without another directory level.
- Direct episode files in an input series folder are repairable. An explicit `SxxExx` determines the season. An
  episode number without a season proposes `Season 01` and requires review. Ambiguous numbering requires review
  without an automatic plan.
- Nested season directories and mixed movie/series content are incompatible and receive corrective guidance.
- A movie file or TV series folder directly in the library root remains processable and may become ready for
  planning, but receives a non-blocking warning because the mixed root is not a suitable final Jellyfin layout.
- An item with safe structural ownership but uncertain metadata enters review. An item whose ownership or directory
  role cannot be determined is incompatible and cannot enter provider selection, approval, or a rename manifest.
- `.nfo` files are always ignored and never enter the domain model or a standalone filesystem operation. They may
  move only as children of a renamed parent directory.
- Exactly one syntactically valid, media-compatible provider ID already present in a movie filename or TV series
  folder name resolves that entity without cache or online lookup. IDs elsewhere, multiple IDs, and episode-level
  IDs do not resolve an entity and require validation. A later explicit operator correction remains auditable.

### Associated Files

- The first release supports subtitle extensions `.srt`, `.ass`, `.ssa`, `.vtt`, and `.sub`.
- A subtitle belongs to a video when it has the same filename stem or adds only recognized language and subtitle
  qualifiers. These qualifiers are preserved during renaming.
- Orphaned subtitles and subtitle target-name collisions require review and cannot enter an executable manifest.
- Unsupported file types are ignored as individual items and remain inside a renamed parent directory.
- An `.nfo` file is never read, modeled, modified, deleted, or included as a standalone manifest operation. It may
  move only as an ignored child of a renamed parent directory.

## Open Product Decisions

The following decisions remain open and should be made before Stage 1 implementation begins:

1. How are alternate movie versions, multipart movies, specials, and extras represented?
2. What is the authoritative source of the final Czech display title when the filename and provider differ?
3. Should series folders omit the year unconditionally, or may the operator enable it for ambiguous remakes?
4. What scoring thresholds permit automatic provider acceptance?
5. Is the first supported UI deployment localhost-only, or must authenticated NAS/LAN access be included?
6. What source-state fingerprint is required between planning, dry-run, and execution?
7. Is automatic rollback required, or is deterministic rollback assistance sufficient for the first release?
8. Which container architectures must be published, especially for the target Synology NAS?
9. Which explicit Compose mechanism enables read-write execution while keeping normal operation read-only?

Until these decisions are resolved, implementation should favor data preservation, explicit review, and reversible
operations over automation.
