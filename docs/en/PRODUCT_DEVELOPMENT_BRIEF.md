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
- Symbolic links are always rejected. The application never follows, models, plans, or renames them. A symbolic link
  inside a directory that would otherwise be renamed blocks that directory from planning.

## Required Domain Model

The current file-centered model is sufficient for scanning, but rename planning requires explicit media entities.
The implementation should introduce the following concepts before building the planner.

### Library Item

A discovered regular file or directory with its original path, type, size where applicable, modification time, and
required source-state fingerprint. Library items include supported video files and associated files that may need to
move with a video. Symbolic links are invalid library entries and are never followed.

### Movie

A movie entity groups one or more physical parts of its main presentation, optional alternate versions, associated
files, containing folder, parsed titles, year, and one selected provider ID. A bonus or extra is not attached to the
movie automatically; it requires operator classification.

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

The authoritative display-title order is:

1. a title explicitly edited or approved by the operator;
2. the Czech localized title from the selected provider candidate;
3. the existing filesystem title when the selected provider has no Czech title;
4. the provider's original title only as a last resort and with required review.

Display titles preserve diacritics, articles, punctuation, and word order from the selected source. Lookup
normalization never rewrites them. A material difference between the existing and provider titles is visible during
review. Once approved manually, a display title remains authoritative across later scans. Changing the selected
provider invalidates that approval and reopens display-title review.

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

Candidate confidence is separate from parser and entity-group confidence. Automatic provider selection requires a
structurally valid, high-confidence entity, a compatible media type, a provider-valid ID, and no conflict with an
embedded or manually approved provider selection. A valid embedded ID and a manually approved selection take
precedence over candidate scoring.

Normalized title similarity is the best comparison against the candidate's localized or original title. When a
reliable source year is available, the normal candidate score is:

```text
candidate score = 0.80 * title similarity + 0.20 * year agreement
```

An exact year has agreement `1.0`, a one-year difference has `0.5`, and a larger difference or missing candidate
year has `0.0`. A movie requires an exact year for automatic selection. A TV series also requires an exact year when
the input supplied a reliably parsed terminal year. Without a comparable TV year, the normal candidate score equals
title similarity.

Normal automatic selection requires all of the following:

- candidate score of at least `0.92`;
- title similarity of at least `0.90`;
- a score lead of at least `0.08` over the second-best candidate from the same provider;
- all structural, media-type, year, ID, and conflict gates described above.

A sole returned candidate requires both candidate score and title similarity of at least `0.97`. TMDb is evaluated
for movies. For TV series, TMDb TV is evaluated first and TVDB is a fallback when TMDb has no candidate that passes
the policy. API result order, popularity, artwork, overview availability, and metadata completeness never increase
the identity score.

A yearless TV series that does not pass the normal title-only path may use episode-title evidence. The application
selects up to three deterministic samples: the first, middle, and last suitable episode, preferably from different
seasons. `Season 00`, specials, multipart files, multi-episode files, unparseable episodes, and filenames without a
usable episode title are excluded. At least two usable episode titles are required.

Each sampled season and episode coordinate must exist for the candidate, and every sampled title must reach `0.85`
similarity against the provider's localized or original episode title. A missing coordinate is conflicting evidence.
Coordinate existence can reject a candidate but is not positive identity evidence by itself. The episode evidence is
the average title similarity of the usable samples, and the corroborated score is:

```text
corroborated TV score = 0.75 * series title similarity + 0.25 * episode evidence
```

This path requires a series-title similarity of at least `0.85`, a final score of at least `0.92`, the normal `0.08`
lead, and no sampled conflict. The sole-candidate `0.97` rule still applies. Episode metadata is requested only for
the leading candidates that need corroboration, limiting provider requests and keeping the result reproducible.

An automatically selected ID resolves provider identity and moves the entity to `ready_for_approval`; it never
approves a rename. A manual selection may override a score failure but must be explicit and auditable. If any
automatic criterion is not met, the entity enters review.

The first release uses named, versioned policy constants for these thresholds. Operators cannot lower them through
configuration until real-library results justify a separately approved policy change. A cached candidate is not
trusted merely because it is cached. Automatic cache reuse requires a prior approved selection, unchanged identity
inputs, and the same policy version; legacy or unproven cache entries require rescoring or review.

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

Each regular source file records its relative path, entry type, size, and modification time at the maximum precision
reported by the filesystem. Full media-content hashing, inode numbers, creation time, ownership, and permissions are
not part of the first-release source fingerprint.

A directory rename records a SHA-256 tree digest over a canonically sorted inventory. Every child contributes its
relative path and entry type. Managed regular files additionally contribute size and modification time. Ignored
children, including `.nfo`, contribute only opaque directory membership and are never opened, parsed, modeled, or
given standalone manifest entries. Adding, removing, renaming, or changing a managed child invalidates the digest.

The immutable manifest also receives a SHA-256 digest over its canonical serialization. Dry-run results apply only
to that exact manifest digest.

### 6. Dry-Run

Dry-run verifies current source state, target paths, permissions, collisions, batch ordering, and rollback data. It
must not modify the library.

A manifest can be executed only after a successful dry-run against the same source fingerprints and exact manifest
digest. Dry-run recomputes source fingerprints independently. A mismatch is never accepted by updating the manifest
in place; the operator must repeat scan, analysis, approval, planning, and dry-run.

### 7. Execute And Audit

Real execution requires explicit confirmation and operates only on one approved manifest. It recomputes source
fingerprints immediately before each batch and again before each operation. A mismatch stops the complete execution
run before further operations and reports a stable reason such as `SOURCE_MISSING`, `SOURCE_SIZE_CHANGED`,
`SOURCE_MTIME_CHANGED`, or `DIRECTORY_CONTENT_CHANGED`. Destination existence and collision checks remain separate
and run during planning, dry-run, and immediately before each operation. The application records each attempted
operation and its result.

On the first operation failure, the complete execution run stops. The application does not attempt automatic
rollback. It reports completed, pending, failed, and recoverable operations and creates an immutable JSON rollback
manifest from only the operations that the durable audit confirms as successfully completed.

Rollback entries reverse successful operations in reverse execution order: the completed target becomes the
rollback source and the original source becomes the rollback target. Each entry records the original operation ID,
current source fingerprint, expected absent target, sequence, and recovery reason. The rollback manifest records its
schema version, manifest kind, original run ID, original manifest digest, creation time, and its own SHA-256 digest.
It contains structured paths and metadata, never shell commands.

Rollback execution uses the same safe manifest executor. It requires integrity and source-state validation, an
absent target, a successful dry-run, and separate explicit confirmation. It never overwrites an existing entry.
Execution results are written to a separate audit instead of mutating the rollback manifest. If rollback state has
changed, the operation is refused. The operator may execute the rollback manifest or leave completed work in place
and create a new scan-through-dry-run workflow for the remaining items.

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
- audit history.

Static HTML and CSV reports remain useful as exports, but they are not the primary review workflow.

The first UI assumes one operator on a trusted machine or private network. Its bind address is configurable and the
development and container default is `0.0.0.0`, allowing access from a Windows browser while the application runs in
WSL and optional access from the private LAN. No authentication, user accounts, roles, application-managed TLS, or
Synology account integration are required for this phase.

This deployment must not be exposed to the public Internet or an untrusted network. Host firewall rules and Compose
port publishing control reachability. The application warns when listening outside the loopback interface but does
not block startup. State-changing routes never use `GET`.

The first UI supports setup, analysis, review, correction, approval, manifest preview, and dry-run. Real rename
execution remains a CLI-only operation with the normal manifest, validation, dry-run, and explicit-confirmation
gates. Authentication, sessions, CSRF protection, HTTPS reverse-proxy guidance, and broader remote-access hardening
are a later add-on. Synology account integration is optional and not required for supported deployment.

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
- the default long-running `app` service mounts the media library explicitly as `:ro`;
- a separate one-shot `executor` service belongs to the `execution` profile and mounts the same library explicitly
  as `:rw`;
- a read-write mount alone never bypasses application-level manifest, dry-run, validation, and confirmation gates;
- provider credentials are injected through environment variables or supported secret files and are never baked
  into the image.

Normal `docker compose up` starts only `app`; it never activates the `execution` profile. The `executor` has no web
port, no long-running process, `restart: "no"`, and `network_mode: "none"`. It is invoked explicitly with
`docker compose --profile execution run --rm executor ...` and is removed after completion. The same service handles
real rename and rollback manifests.

The mount mode must be literal in Compose. A variable such as `${MEDIA_MODE}` must never switch the normal service
between `:ro` and `:rw`, and the web service must never receive a writable media mount. The executor additionally
requires an explicit real-execution CLI flag and a global execution lock in the persistent workspace. The lock
prevents concurrent rename or rollback executors but does not replace manifest, fingerprint, target, dry-run,
confirmation, or audit checks.

Official images are built, smoke-tested, and published only for `linux/amd64`. This covers the `x86_64` WSL
development environment and the target Synology DS925+ and DS723+ systems. The project does not publish
`linux/arm64`, `linux/arm/v7`, `linux/386`, or a multi-platform image manifest in the first release.

The Dockerfile should remain portable where doing so adds no architecture-specific complexity, but portability does
not create a support commitment. The advanced documentation should show a native local source build and an optional
single-platform `docker buildx build` example. Images built for other architectures are best-effort, are not release
tested or published by the project, and may fail when the pinned Python image or binary dependencies are unavailable.

Compose must not force a `platform` value. The official single-platform tag fails clearly on an unsupported host
instead of silently running the AMD64 image through emulation. The normal operator quick start documents only the
supported AMD64 image; unsupported source-build instructions belong in advanced or development documentation.

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
- Add batch boundaries, durable audit states, stop-on-failure handling, and immutable rollback manifests.

### Stage 5: Implement The Human Review UI

- Add setup, dashboard, review, provider selection, and bulk actions.
- Add manifest preview, dry-run results, and audit history. Keep real execution in the CLI for the first UI release.
- Keep all state changes behind the same services and validation gates used by the CLI.

### Stage 6: Package For Container Deployment

- Add the production Dockerfile, `.dockerignore`, Compose configuration, and example environment file.
- Run the production process as a non-root user with persistent workspace storage.
- Make the default media mount read-only and provide an explicit execution configuration for read-write access.
- Add healthchecks, image metadata, the `linux/amd64` release target, smoke tests, and reproducible release builds.
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

### Multipart Media, Versions, Specials, And Extras

- `Part 1`, `Part 2`, or an equivalent phrase in an official movie title denotes separate movie entities when the
  parts have distinct provider identities. The phrase remains in each display title to keep filesystem ordering
  readable.
- One movie physically split across files is one entity with ordered components. Supported terminal component
  markers are `CD1`, `CD2`, `Disc 1`, `Disc 2`, `Part 1`, and `Part 2`, extended to further positive integers when
  required. Component numbering must start at one, remain contiguous, and agree on title, year, provider, and
  language. The same selected provider ID is rendered in every component filename.
- A `Part` marker alone never proves multipart ownership. Provider identity or explicit operator confirmation must
  distinguish a split file from separately released movies. Missing, duplicate, or conflicting components require
  review.
- Alternate versions such as `Theatrical`, `Director's Cut`, `Extended`, `Unrated`, `Remastered`, and `Alternate`
  remain separate video files under one movie entity and one selected provider ID. Multiple files with the same
  title, year, and provider require review to classify them as versions, components, duplicates, or distinct movies.
- Multi-part TV stories with separate episode numbers remain separate episodes; `Part 1` and `Part 2` are display-title
  text. One file containing multiple episodes uses an explicit range such as `S01E01-E02` and requires unambiguous
  parsing or operator confirmation.
- TV specials use `Season 00` and `S00E##`, belong to their series, and never receive a provider ID. Provider ordering
  is used when available; otherwise the special requires review.
- A video identified as a bonus or extra requires review. The operator may classify it as a movie, a TV special, or
  ignored content. Ignored extras remain in place, receive no provider ID or standalone manifest operation, and may
  move only as children of a renamed parent directory.

### Display Title Authority

- An operator-approved title is authoritative, followed by the selected provider's Czech localized title, the
  existing filesystem title, and finally the provider's original title.
- Using the provider's original title as the fallback requires review.
- Display titles preserve the selected source's diacritics, articles, punctuation, and word order. Lookup
  normalization never becomes display text.
- A material difference between the filesystem and provider titles is shown during review.
- A manually approved title persists across later scans. Changing the selected provider reopens title review.

### TV Series Year

- A normalized TV series folder never includes a release or first-air year. The selected provider ID distinguishes
  series with the same display title, including remakes.
- A terminal year in an input folder is retained as lookup and review metadata, then removed from the planned folder
  name only after provider identity is selected and approved.
- Numbers that are part of the actual series title, such as `1899`, `1923`, `11.22.63`, or `Catch-22`, are preserved.
  An ambiguous number requires review instead of automatic removal.
- A series without a selected provider ID cannot be approved for rename planning. Changing or removing an input year
  does not override a manually approved provider selection.
- Years are never added to season folders or episode filenames.

### Provider Candidate Selection

- Provider candidate confidence is independent of parser and entity-group confidence. Automatic selection requires
  a structurally valid, high-confidence entity and all media-type, ID, year, and conflict gates.
- Normal scoring uses 80% title similarity and 20% year agreement when a reliable source year is available. Without
  a comparable TV year, the score equals title similarity.
- Automatic selection requires score `0.92`, title similarity `0.90`, and a `0.08` lead over the second candidate
  from the same provider. A sole candidate requires score and title similarity `0.97`.
- Movies require an exact year. TV series require an exact reliably parsed input year when present; a yearless series
  may be selected from sufficiently strong title evidence.
- A yearless series may use two or three deterministically sampled episode titles as corroboration. The corroborated
  score uses 75% series-title similarity and 25% average episode-title similarity. Each episode-title match and the
  series title must reach `0.85`, the final score must reach `0.92`, and every sampled coordinate must exist.
- Automatic provider selection only produces `ready_for_approval`; it never approves a rename. Manual overrides are
  explicit and auditable.
- Thresholds are named, versioned policy constants that operators cannot lower in the first release. Cached
  selections are reused automatically only when previously approved under the same policy and unchanged inputs.

### Initial Web UI Deployment

- The first UI is an unauthenticated single-operator application for a trusted machine or private LAN. It is not
  supported on the public Internet or an untrusted network.
- The bind address is configurable and defaults to `0.0.0.0` for WSL, container, Windows-browser, and optional private
  LAN access. Listening outside loopback produces a warning but is allowed.
- Authentication, accounts, roles, application-managed TLS, and Synology account integration are not first-release
  requirements. Synology account integration remains optional.
- The UI supports review, corrections, approvals, manifest preview, and dry-run but has no real-rename endpoint. Real
  execution remains in the CLI behind all existing safety gates.
- Authentication, sessions, CSRF protection, HTTPS reverse-proxy guidance, and remote-access hardening are a later
  add-on rather than a blocker for the functional UI.

### Source-State Fingerprint

- Regular files are fingerprinted by relative path, entry type, size, and filesystem modification time. Full content
  hashes, inode numbers, creation time, ownership, and permissions are excluded from the first release.
- Renamed directories use a SHA-256 tree digest over a sorted inventory. Ignored children contribute only opaque path
  membership and type; they are never opened or given standalone manifest entries.
- Symbolic links are always rejected and never followed. Their presence inside a directory blocks that directory
  from planning or execution.
- The manifest has a separate SHA-256 digest over canonical serialization. A successful dry-run is valid only for
  the exact manifest digest and matching source fingerprints.
- Dry-run, batch start, and each operation independently revalidate source state. Any mismatch stops the complete
  execution run and requires a new scan-through-dry-run workflow; fingerprints are never refreshed in place.
- Target existence and collision checks are performed separately during planning, dry-run, and execution.

### Partial Failure And Rollback

- The first failed operation stops the complete execution run. The application never starts automatic rollback.
- A durable audit distinguishes completed, failed, pending, and uncertain operations. Only confirmed successful
  operations enter an immutable JSON rollback manifest, in reverse execution order.
- Each reverse entry links to the original operation and stores rollback source, rollback target, source fingerprint,
  expected absent target, sequence, and reason. The manifest links to the original run and manifest digest and has
  its own schema version and SHA-256 digest. It never contains shell commands.
- Rollback uses the normal executor and requires validation, dry-run, explicit confirmation, and audit logging. It
  never overwrites an existing path and never mutates its input manifest.
- The operator chooses between executing rollback or preserving completed operations and creating a new workflow for
  the remaining items.

### Container Architecture Support

- The only officially built, tested, and published platform is `linux/amd64`, covering the development environment
  and target Synology DS925+ and DS723+ devices.
- The project does not publish ARM, 32-bit, or multi-platform images in the first release.
- Compose does not set `platform`; unsupported hosts receive the normal no-compatible-image failure rather than
  hidden emulation.
- The Dockerfile remains reasonably portable, and advanced documentation provides native and optional cross-build
  examples for unsupported platforms. Such images are best-effort and receive no release testing or support.

### Compose Write Access

- Normal `docker compose up` starts a long-running `app` service with `/media:ro` and a persistent writable workspace.
- Real rename and rollback use a separate one-shot `executor` service in the explicit `execution` profile. It has
  `/media:rw`, no network, no web port, no restart policy, and is removed after the command completes.
- The documented invocation requires both `--profile execution` and the explicit real-execution CLI flag. The
  executor acquires a global workspace execution lock before any mutation.
- Compose states `:ro` and `:rw` literally. Environment-variable mount modes and writable media on the web service
  are forbidden.
- Writable mounting grants capability only; all manifest integrity, source fingerprint, target safety, successful
  dry-run, confirmation, stop-on-failure, rollback, and audit gates remain mandatory.

## Resolved Product Decisions

All product decisions identified for this documentation alignment have been resolved above. Implementation must
follow these accepted decisions and continue to favor data preservation, explicit review, and reversible operations.
