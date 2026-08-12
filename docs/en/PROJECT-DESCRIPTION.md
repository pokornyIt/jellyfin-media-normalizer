# PROJECT-DESCRIPTION

[English](PROJECT-DESCRIPTION.md) | [Čeština](../cs/PROJECT-DESCRIPTION.md)

## Goal

The goal of this project is to consolidate and normalize a large media library stored on
a Synology NAS so that it is clean, consistent, and ready for reliable use in Jellyfin.

The library contains more than 9,000 video files across approximately 1,000 folders and includes both
movies and TV series. The main purpose of the project is to standardize file and folder names,
improve media identification, and prepare the library for controlled batch renaming without unnecessary metadata
clutter on disk.

This project does not use `.nfo` files. Jellyfin identification will instead rely on a single provider ID stored
in the movie filename or TV series folder name, using Jellyfin-supported identifier formats such as
`[imdbid-tt...]`, `[tmdbid-...]`, or `[tvdbid-...]`.

## Scope

The project covers:

- scanning and inventory of the existing media library
- classification of items into movies, TV series, and unknown/problematic files
- normalization of names into a unified naming scheme
- validation of parsed media information
- provider ID lookup for each movie or TV series
- generation of a rename plan
- controlled batch renaming in logical groups
- review reporting for ambiguous and unresolved items

The project does not include:

- `.nfo` generation
- embedding metadata into media files
- storing episode-level IDs
- storing IDs in episode filenames
- automatic renaming without validation
- full automation of uncertain matches

## Library Layout And Classification

The application scans one configured library root that may contain movies and TV series. The library root is a
neutral container and is not classified as either media type. A movie file or TV series folder directly in the
library root remains processable and may become ready for planning, but receives a non-blocking warning because
the mixed root is not a suitable final Jellyfin library layout.

Directories below the root are classified by their contents as movie collections, series collections, TV series,
seasons, or incompatible directories. A classified movie collection must not contain a TV series subtree, and a
classified series collection must not contain movie files. Folder names may contribute evidence, but content and
structure determine the classification.

Scanning descends through at most five directory levels below the configured root. The root has depth zero and a
file does not add a directory level. Content beyond this limit is reported as incompatible instead of being
silently omitted.

The normalized TV layout is strict:

```text
Series Name [provider-id]/
└── Season 01/
    └── Episode Title S01E01 - CZ.ext
```

A series folder contains only normalized season folders, and a season folder contains episode files and their
supported associated files without another directory level. Direct episode files in an input series folder are
repairable: an explicit `SxxExx` selects that season, while an episode number without a season proposes
`Season 01` and requires review. Ambiguous episode numbering requires review without an automatic plan. Nested
season directories and mixed movie/series content are incompatible and receive corrective guidance.

An item that can be grouped safely but has uncertain metadata enters review. An item whose ownership or structural
role cannot be determined is incompatible and cannot enter provider selection, approval, or a rename manifest.
`.nfo` files are always ignored and never enter the domain model or a standalone filesystem operation. They may move
only as children of a renamed parent directory.

## Naming Conventions

### Movies

Movie filenames use the following format:

- `Czech Title (Year) [imdbid-tt1234567] - CZ.ext`
- `Czech Title (Year) [tmdbid-12345] - EN (tit. CZ).ext`

A movie is a video file and does not require or create a dedicated movie folder. Organizational folders for genres
and collections remain readable and do not receive provider IDs. A supported associated file uses the same filename
stem as its owning video and is renamed with it.

An official `Part 1` or `Part 2` in the movie title remains part of the display title when the releases have distinct
provider identities. One movie physically split across multiple files instead uses a terminal component marker:

- `Czech Title (Year) [tmdbid-12345] - CD1 - CZ.ext`
- `Czech Title (Year) [tmdbid-12345] - CD2 - CZ.ext`

Component numbering must start at one and remain contiguous. A `Part` marker alone never proves that files belong to
one movie; provider identity or explicit operator confirmation must distinguish components from separate releases.

Alternate versions remain separate files under one movie entity and one selected provider ID. Their controlled
edition label precedes the language marker, for example:

- `Czech Title (Year) [tmdbid-12345] - Director's Cut - CZ.ext`
- `Czech Title (Year) [tmdbid-12345] - Theatrical - EN (tit. CZ).ext`

Multiple files with the same title, year, and provider require review before they can be classified as components,
alternate versions, duplicates, or distinct movies.

### TV Series

The TV series folder name uses the following format:

- `Series Name [tvdbid-12345]`
- `Series Name [tmdbid-12345]`

The normalized TV series folder never includes a release or first-air year. A terminal year in an input folder is
used for lookup and review, then removed only after the provider identity is selected and approved. The provider ID
distinguishes remakes with the same display title.

Numbers that are part of the actual title, such as `1899`, `1923`, `11.22.63`, or `Catch-22`, remain unchanged. An
ambiguous number requires review. Years are never added to season folders or episode filenames.

Season folder names use `Season XX`, for example `Season 01`.

TV specials use `Season 00` and `S00E##`. They belong to the series and never receive a provider ID. A single file
containing multiple episodes uses an explicit range such as `S01E01-E02`. Multi-part stories stored as separately
numbered episodes remain separate episodes; `Part 1` and `Part 2` remain part of their display titles.

Episode filenames do not contain any provider ID:

- `Czech Episode Title S01E02 - CZ.ext`
- `Czech Episode Title S01E02 - EN (tit. CZ).ext`

Language markers use standard two-letter codes: `CZ`, `EN`, `DE`, `SK`, `FR`, `IT`, `ES`.

### Display Titles

The display title is selected in this order: an operator-approved title, the selected provider's Czech localized
title, the existing filesystem title, and the provider's original title. The last fallback requires review.

Display titles preserve diacritics, articles, punctuation, and word order from their selected source. Lookup
normalization never rewrites display text. A manually approved title persists across later scans, while changing the
selected provider reopens title review.

### Associated Files

The first release supports subtitle files with `.srt`, `.ass`, `.ssa`, `.vtt`, and `.sub` extensions. A subtitle
belongs to a video when it uses the same filename stem or adds only recognized language and subtitle qualifiers,
such as `cs`, `en`, `forced`, `sdh`, `cc`, or `default`. Qualifiers are preserved during renaming. Orphaned subtitles
and target-name collisions require review.

Other file types are ignored as individual items and remain inside a directory when that parent directory is
renamed. An `.nfo` file is never read, parsed, modeled, created, modified, deleted, or targeted by a standalone
manifest operation. It may move only as ignored content of a renamed parent directory.

A video recognized as a bonus or extra requires review. The operator may classify it as a movie, TV special, or
ignored content. Ignored extras receive no provider ID or standalone manifest operation and may move only as content
of a renamed parent directory.

## Metadata Strategy

The project avoids local metadata sidecar files such as `.nfo` in order to keep the filesystem readable
and uncluttered when browsing the storage directly.

Instead, Jellyfin identification will be improved by adding a single provider ID to the movie filename or TV series
folder name.

Provider priority:

- Movies: primary lookup through TMDb, with one final selected ID stored in the video filename
- TV Series: online lookup order is TMDb TV first, then TVDB; one final selected ID is stored in the series folder name
- Episodes: no provider ID lookup; no ID stored in the filename

### Provider Selection Policy

Provider candidates are scored independently of parser and entity-group confidence. Automatic selection is allowed
only for a structurally valid, high-confidence entity with a matching media type, a provider-valid ID, and no
conflict with an embedded or manually approved selection. A valid embedded ID and an explicit manual selection take
precedence over candidate scoring.

With a reliable source year, the candidate score uses 80% normalized title similarity and 20% year agreement. An
exact year scores `1.0`, a one-year difference scores `0.5`, and a larger difference or missing candidate year scores
`0.0`. Movies require an exact year for automatic selection. TV series require an exact input year when one was
reliably parsed; without one, their normal score equals title similarity.

Automatic selection requires score `0.92`, title similarity `0.90`, and a `0.08` lead over the second candidate from
the same provider. A sole candidate requires score and title similarity `0.97`. API ordering, popularity, artwork,
overview availability, and metadata completeness do not contribute to identity scoring.

A yearless TV series may use provider episode titles as additional evidence when title-only scoring is insufficient.
Up to three suitable episodes are sampled deterministically as the first, middle, and last usable episode, preferably
across different seasons. At least two samples with usable episode titles are required. Specials, `Season 00`,
multipart or multi-episode files, and unparseable episodes are excluded.

Every sampled season and episode coordinate must exist for the candidate, and every sampled title must have at least
`0.85` similarity to a localized or original provider episode title. The corroborated score uses 75% series-title
similarity and 25% average episode-title similarity. It requires series-title similarity `0.85`, final score `0.92`,
the normal `0.08` lead, and no sampled conflict. Episode lookup provides series-level identity evidence only and
never creates an episode provider ID.

Automatic provider selection produces `ready_for_approval`, not rename approval. Manual overrides are explicit and
auditable. The thresholds are named, versioned policy constants that operators cannot lower in the first release.
Cached selections are automatically reusable only when previously approved under the same policy version with
unchanged identity inputs; other cached results require rescoring or review.

## Design Principles

- No standalone `.nfo` processing or manifest operations
- One provider ID per movie or TV series; no episode-level IDs
- No rename without a validated plan
- No bulk rename without a generated manifest
- Dry-run is the default execution mode
- Side effects are isolated to the executor layer
- Ambiguous or low-confidence items are always routed to review, never automated
- Readable filesystem structure is the priority
- Symbolic links are always rejected and never followed, modeled, planned, or renamed

## Source-State Safety

Every regular source file in a rename manifest has a required fingerprint containing its relative path, entry type,
size, and modification time at the precision reported by the filesystem. The first release does not hash complete
media content and does not use inode number, creation time, ownership, or permissions as identity fields.

A renamed directory uses a SHA-256 tree digest over a canonically sorted inventory. Every descendant contributes its
relative path and entry type; managed regular files also contribute size and modification time. Ignored children,
including `.nfo`, contribute only opaque membership and are never opened, parsed, modeled, or assigned a standalone
manifest entry. A symbolic link is always invalid, is never followed, and blocks its containing directory from
planning and execution.

The manifest has a separate SHA-256 digest over its canonical serialization. Dry-run is valid only for the exact
manifest digest and matching source fingerprints. Source state is revalidated during dry-run, immediately before
each batch, and before every operation. Any mismatch stops the complete execution run and requires a new scan,
analysis, approval, manifest, and dry-run. Target existence and collision checks are independent and repeat at
planning, dry-run, and execution boundaries.

## Partial Failure And Rollback

The first failed rename stops the complete execution run. The application does not attempt automatic rollback.
Instead, its durable audit identifies confirmed successful, failed, pending, and uncertain operations. Only confirmed
successful operations are reversed, in reverse execution order, into an immutable JSON rollback manifest.

Each rollback entry links to the original operation and contains the current source path, original target path,
source fingerprint, expected absent target, sequence, and recovery reason. The manifest records its schema and kind,
the original run and manifest digest, creation time, and its own SHA-256 digest. It stores structured data rather than
shell commands.

The normal manifest executor handles rollback. Source state and target absence are validated again, dry-run is
mandatory, real rollback requires explicit confirmation, and every result is written to a separate audit. Rollback
never overwrites an existing path or mutates its manifest. The operator may instead preserve completed operations and
create a new workflow for the remaining items.

## Initial Web UI Deployment

The first web UI is an unauthenticated single-operator application for a trusted machine or private LAN. The bind
address is configurable and defaults to `0.0.0.0` so a Windows browser can reach an application running in WSL or a
container. Listening outside loopback emits a warning but does not prevent startup. Host firewall rules and Compose
port publishing define which trusted devices can connect.

The initial UI supports setup, analysis, review, correction, approval, manifest preview, audit history, and dry-run.
It has no endpoint for real rename execution. Actual filesystem changes remain CLI-only and still require a validated
manifest, successful dry-run, and separate explicit confirmation. State-changing UI routes never use `GET`.

Public Internet and untrusted-network exposure are unsupported. Authentication, accounts, roles, sessions, CSRF
protection, application-managed TLS, HTTPS reverse-proxy guidance, and remote-access hardening are later add-ons.
Synology account integration is optional and is not required for the first supported deployment.

## Container Architecture Support

The project officially builds, smoke-tests, and publishes only `linux/amd64` container images. This platform covers
the `x86_64` WSL development environment and both target NAS devices: Synology DS925+ with AMD Ryzen V1500B and
Synology DS723+ with AMD Ryzen R1600.

The first release does not publish ARM, 32-bit, or multi-platform images. Compose does not set `platform`, so an
unsupported host fails with Docker's normal incompatible-image error instead of silently using AMD64 emulation.

The Dockerfile remains portable where practical. Advanced documentation will include native `docker build` and
optional single-platform `docker buildx build` examples for users who want to try another architecture. Such builds
are best-effort, receive no project release testing, and are not officially supported or published.

## Compose Write Access

Normal `docker compose up` starts only the long-running `app` service. It mounts the media library explicitly at
`/media:ro` and uses a persistent writable `/workspace`. The web service never receives writable media access.

Real rename and rollback execution use a separate one-shot `executor` service in the `execution` profile. It mounts
`/media:rw`, has no network or web port, uses `restart: "no"`, and is removed after the command completes. The
documented invocation has the following form:

```bash
docker compose --profile execution run --rm executor <command> <explicit-execution-flag>
```

Compose records `:ro` and `:rw` literally; an environment variable never switches the media mount mode. Before any
mutation, the executor acquires a global execution lock in the workspace. The writable mount and lock do not bypass
manifest integrity, source fingerprint, target safety, successful dry-run, explicit confirmation, stop-on-failure,
rollback, or audit requirements.

## Implementation

### Architecture

The project is organized into distinct layers. Each layer has a single responsibility:

```text
src/jellyfin_media_normalizer/
├── constants.py            — project-wide string and tuple constants
├── settings.py             — runtime configuration via environment variables
├── main.py                 — application entry point
├── cli/
│   └── app.py              — CLI commands (scan, parse, report-scan, ...)
├── models/
│   ├── media_item.py       — raw scanned file entry
│   ├── media_type.py       — movie / tv_episode / unknown enum
│   ├── parsed_media_item.py — fully parsed and validated item
│   ├── parsed_name.py      — structured name data extracted from filename
│   ├── provider_match.py   — selected provider ID with confidence and reason
│   ├── scan_result.py      — scan run result summary
│   ├── validation_result.py — validation errors and warnings
│   ├── validation_status.py — passed / review_needed / failed enum
│   └── confidence_level.py — high / medium / low enum
├── scanners/
│   └── library_scanner.py  — filesystem scan and file inventory
├── parsers/
│   ├── patterns.py         — shared compiled regex patterns
│   ├── filename_cleaner.py — strip release tags and normalize separators
│   ├── classifier.py       — classify filename as movie or TV episode
│   ├── movie_name_parser.py — extract title, year, language from movie name
│   ├── tv_episode_parser.py — extract series, season, episode, language
│   ├── media_parser.py     — coordinate cleaning, classification, and parsing
│   └── provider_id_extractor.py — detect embedded provider IDs in folder names
├── validators/
│   ├── structure_validator.py   — validate required fields in parsed items
│   ├── confidence_scorer.py     — compute confidence level
│   ├── consistency_validator.py — validate internal consistency across items
│   └── validation_service.py   — coordinate validation pipeline
├── providers/
│   ├── provider_clients.py      — HTTP clients for TMDb and TVDB APIs
│   ├── provider_id_cache.py     — local JSON cache for resolved provider IDs
│   ├── online_provider_resolver.py — online lookup via TMDb and TVDB
│   └── provider_resolver_chain.py  — chain of resolvers (cache → online)
├── services/
│   ├── scan_service.py          — run and return scan results
│   ├── parse_service.py         — coordinate parse + validate + provider lookup
│   └── provider_lookup_service.py — resolve provider IDs for all parsed items
├── reporters/
│   ├── json_reporter.py         — full JSON report of all parsed items
│   ├── review_reporter.py       — report of items needing review
│   └── unresolved_reporter.py   — report of items without a resolved provider ID
└── utils/
    ├── logging.py               — LoggingMixin and setup helpers
    └── paths.py                 — path resolution utilities
```

### Provider ID Resolution

Provider IDs are resolved in this priority order:

1. **Embedded ID** — if a movie filename or TV series folder name already contains exactly one syntactically valid
   provider ID compatible with that media type, that ID is selected and no cache or online lookup is performed.
   Provider IDs elsewhere, multiple IDs, and episode-level IDs do not resolve an entity and require validation.
2. **Cache** — the local JSON cache at `data/workspace/cache/provider_ids.json` is checked first for
   a matching lookup key.
3. **Online API** — if the cache has no match and API keys are configured, clients are queried in this order:
    - `movie`: TMDb
    - `tv_episode` (series-level lookup): TMDb TV, then TVDB

Items classified as `unknown` are skipped entirely.

### Implementation Phases

| #   | Phase                                 | Status         |
| --- | ------------------------------------- | -------------- |
| 1   | Inventory and scan                    | ✅ Implemented |
| 2   | Classification                        | ✅ Implemented |
| 3   | Name normalization                    | ✅ Implemented |
| 4   | Validation                            | ✅ Implemented |
| 5   | Provider ID lookup                    | 🚧 Partial     |
| 6   | Rename planning (manifest generation) | ⏳ Planned     |
| 7   | Batch rename execution                | ⏳ Planned     |
| 8   | Review workflow (HTML/CSV reports)    | ⏳ Planned     |

#### Phase 1 — Inventory and Scan

Scans the media library and collects file paths, folder structure, and filename patterns.
Detects supported video extensions. Produces a flat list of `MediaItem` objects used as input for all following phases.

#### Phase 2 — Classification

Each item is classified into one of: `movie`, `tv_episode`, or `unknown`.

Classification is based on filename patterns: a year in parentheses indicates a movie; an `SxxExx` marker
(or equivalent) indicates a TV episode. Items that match neither are marked as `unknown`.

#### Phase 3 — Name Normalization

Normalized names are parsed into structured `ParsedName` objects containing title, year, season/episode, language code,
and subtitle flags. Release tags (codec names, resolutions, quality markers) are stripped before parsing.

#### Phase 4 — Validation

All parsed items are validated for structural completeness and internal consistency.
Each item receives a `ValidationStatus` (`passed`, `review_needed`, or `failed`)
and a `ConfidenceLevel` (`high`, `medium`, or `low`). High-confidence items proceed automatically;
others are flagged for review.

#### Phase 5 — Provider ID Lookup

After validation, every non-unknown item is matched to a single provider ID. Lookup follows the chain described
in the [Provider ID Resolution](#provider-id-resolution) section above.

The result for each resolved item is a `ProviderMatch` object containing: `provider`, `provider_id`, `confidence`,
`reason`, and `lookup_key`. Items without a match are written to the unresolved report.

The current online resolver accepts the first returned result with fixed confidence. Multiple candidates,
explainable scoring, ambiguity thresholds, episode-title corroboration, policy-versioned cache reuse, and persisted
selection provenance remain to be implemented before this phase satisfies the product policy.

#### Phase 6 — Rename Planning *(planned)*

A rename manifest will be generated before any filesystem change is made. It will contain: original path, media type,
normalized title data, selected provider ID, confidence, proposed new path, and action status.

Dry-run mode will be the default. Actual execution requires an explicit opt-in flag.

#### Phase 7 — Batch Rename Execution *(planned)*

Renames will be executed in logical batches (movies by folder, TV series one show at a time) only after the manifest
has been reviewed. The executor will support audit logging, collision detection, immediate stop on failure, and
explicit rollback through an immutable reverse manifest. Automatic rollback is not supported.

#### Phase 8 — Review Workflow *(planned)*

Items flagged for review will be exported in additional formats (HTML, CSV) to allow manual inspection outside of JSON.
This phase has no side effects on the filesystem.

## Expected Outcome

After completion, the media library should have:

- consistent and readable file and folder naming
- improved Jellyfin recognition through embedded provider IDs
- a repeatable workflow for future library additions
- a safe batch rename process with rollback capability
- minimal filesystem clutter — no generated metadata sidecars and no embedded metadata changes
- controlled handling of all uncertain or ambiguous cases
