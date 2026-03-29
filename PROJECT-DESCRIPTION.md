# PROJECT-DESCRIPTION
## Goal

The goal of this project is to consolidate and normalize a large media library stored on a Synology NAS so that it is clean, consistent, and ready for reliable use in Jellyfin.

The library contains more than 9,000 video files across approximately 1,000 folders and includes both movies and TV series. The main purpose of the project is to standardize file and folder names, improve media identification, and prepare the library for controlled batch renaming without unnecessary metadata clutter on disk.

This project does not use `.nfo` files. Jellyfin identification will instead rely on a single provider ID stored in the main folder name of a movie or TV series, using Jellyfin-supported identifier formats such as `[imdbid-tt...]`, `[tmdbid-...]`, or `[tvdbid-...]`.

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

## Naming Conventions

### Movies

Movie filenames use the following format:

- `Czech Title (Year) - CZ.ext`
- `Czech Title (Year) - EN (tit. CZ).ext`

The movie folder name contains a single provider ID:

- `Czech Title (Year) [imdbid-tt1234567]`
- `Czech Title (Year) [tmdbid-12345]`

Only one ID will be stored, based on the selected provider recommendation.

### TV Series

The TV series root folder name uses the following format:

- `Series Name [tvdbid-12345]`
- `Series Name [tmdbid-12345]`

No year will be used in the TV series folder name, because it may be misleading or confusing.

Episode filenames do not contain any provider ID:

- `Czech Episode Title S01E02 - CZ.ext`
- `Czech Episode Title S01E02 - EN (tit. CZ).ext`

Language markers use standard two-letter codes: `CZ`, `EN`, `DE`, `SK`, `FR`, `IT`, `ES`.

## Metadata Strategy

The project avoids local metadata sidecar files such as `.nfo` in order to keep the filesystem readable and uncluttered when browsing the storage directly.

Instead, Jellyfin identification will be improved by adding a single provider ID only to the main movie or series folder name.

Provider priority:

- Movies: primary lookup through TMDb, with one final selected ID stored in the folder name
- TV Series: primary lookup through TVDB or TMDb TV, with one final selected ID stored in the series folder name
- Episodes: no provider ID lookup; no ID stored in the filename

## Design Principles

- No `.nfo` files
- One provider ID per movie or TV series; no episode-level IDs
- No rename without a validated plan
- No bulk rename without a generated manifest
- Dry-run is the default execution mode
- Side effects are isolated to the executor layer
- Ambiguous or low-confidence items are always routed to review, never automated
- Readable filesystem structure is the priority

## Implementation

### Architecture

The project is organized into distinct layers. Each layer has a single responsibility:

```
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

1. **Embedded ID** — if the folder name already contains `[imdbid-tt...]`, `[tmdbid-...]`, or `[tvdbid-...]`, that ID is used directly and no lookup is performed.
2. **Cache** — the local JSON cache at `data/workspace/cache/provider_ids.json` is checked first for a matching lookup key.
3. **Online API** — if the cache has no match and API keys are configured, TMDb (movies) or TVDB (TV series) is queried.

Items classified as `unknown` are skipped entirely.

### Implementation Phases

| #   | Phase                                 | Status        |
| --- | ------------------------------------- | ------------- |
| 1   | Inventory and scan                    | ✅ Implemented |
| 2   | Classification                        | ✅ Implemented |
| 3   | Name normalization                    | ✅ Implemented |
| 4   | Validation                            | ✅ Implemented |
| 5   | Provider ID lookup                    | ✅ Implemented |
| 6   | Rename planning (manifest generation) | ⏳ Planned     |
| 7   | Batch rename execution                | ⏳ Planned     |
| 8   | Review workflow (HTML/CSV reports)    | ⏳ Planned     |

#### Phase 1 — Inventory and Scan

Scans the media library and collects file paths, folder structure, and filename patterns. Detects supported video extensions. Produces a flat list of `MediaItem` objects used as input for all following phases.

#### Phase 2 — Classification

Each item is classified into one of: `movie`, `tv_episode`, or `unknown`.

Classification is based on filename patterns: a year in parentheses indicates a movie; an `SxxExx` marker (or equivalent) indicates a TV episode. Items that match neither are marked as `unknown`.

#### Phase 3 — Name Normalization

Normalized names are parsed into structured `ParsedName` objects containing title, year, season/episode, language code, and subtitle flags. Release tags (codec names, resolutions, quality markers) are stripped before parsing.

#### Phase 4 — Validation

All parsed items are validated for structural completeness and internal consistency. Each item receives a `ValidationStatus` (`passed`, `review_needed`, or `failed`) and a `ConfidenceLevel` (`high`, `medium`, or `low`). High-confidence items proceed automatically; others are flagged for review.

#### Phase 5 — Provider ID Lookup

After validation, every non-unknown item is matched to a single provider ID. Lookup follows the chain described in the [Provider ID Resolution](#provider-id-resolution) section above.

The result for each resolved item is a `ProviderMatch` object containing: `provider`, `provider_id`, `confidence`, `reason`, and `lookup_key`. Items without a match are written to the unresolved report.

#### Phase 6 — Rename Planning *(planned)*

A rename manifest will be generated before any filesystem change is made. It will contain: original path, media type, normalized title data, selected provider ID, confidence, proposed new path, and action status.

Dry-run mode will be the default. Actual execution requires an explicit opt-in flag.

#### Phase 7 — Batch Rename Execution *(planned)*

Renames will be executed in logical batches (movies by folder, TV series one show at a time) only after the manifest has been reviewed. The executor will support execution logging, collision detection, and rollback capability.

#### Phase 8 — Review Workflow *(planned)*

Items flagged for review will be exported in additional formats (HTML, CSV) to allow manual inspection outside of JSON. This phase has no side effects on the filesystem.

## Expected Outcome

After completion, the media library should have:

- consistent and readable file and folder naming
- improved Jellyfin recognition through embedded provider IDs
- a repeatable workflow for future library additions
- a safe batch rename process with rollback capability
- minimal filesystem clutter — no sidecar files, no embedded metadata
- controlled handling of all uncertain or ambiguous cases
