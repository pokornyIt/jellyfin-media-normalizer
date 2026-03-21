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

## Naming Rules

### Movies

Movie files will be normalized into the following format:

- `Czech Title (Year) - CZ.ext`
- `Czech Title (Year) - EN (tit. CZ).ext`

The movie folder will contain a single provider ID:

- `Czech Title (Year) [imdbid-tt1234567]`
- `Czech Title (Year) [tmdbid-12345]`

Only one ID will be stored, based on the selected provider recommendation.

### TV Series

The TV series root folder will be normalized into:

- `Series Name [tvdbid-12345]`
- `Series Name [tmdbid-12345]`

No year will be used in the TV series folder name, because it may be misleading or confusing.

Episode filenames will not contain any ID and will use this format:

- `Czech Episode Title S01E02 - CZ.ext`
- `Czech Episode Title S01E02 - EN (tit. CZ).ext`

Language markers will always use standard two-letter codes such as `CZ`, `EN`, `DE`, etc.

## Metadata Strategy

The project avoids local metadata sidecar files such as `.nfo` in order to keep the filesystem readable and uncluttered when browsing the storage directly.

Instead, Jellyfin identification will be improved by adding a single provider ID only to the main movie or series folder name.

Recommended provider usage in this project:

- Movies: primary lookup through TMDb, with one final selected ID stored in the folder name
- TV Series: primary lookup through TVDB or TMDb TV, with one final selected ID stored in the series folder name
- Episodes: no provider ID lookup; no ID stored in the filename

## Project Phases

### 1. Inventory and Scan

The first phase is a full scan of the media library.

This phase collects:

- current file paths
- folder structure
- filename patterns
- file extensions
- possible movie/year extraction
- possible series/season/episode extraction
- detection of unclassified or suspicious files

The output of this phase is an inventory dataset used as the input for all following phases.

### 2. Classification

Each media item is classified into one of these categories:

- movie
- TV episode
- unknown
- manual review required

Classification is based on filename and path parsing. Examples include:

- title + year for movies
- title + `SxxEyy` for TV episodes
- folder grouping for series detection

Items that cannot be classified with sufficient confidence are not renamed automatically.

### 3. Name Normalization

Once classified, each item is normalized into a canonical internal representation.

For movies, the normalized data should contain at least:

- title
- year
- language marker
- subtitle marker
- target folder name
- target file name

For TV episodes, the normalized data should contain at least:

- series title
- season
- episode
- episode title
- language marker
- subtitle marker
- target folder and file name

This phase removes technical junk from source filenames, such as release tags, codecs, resolutions, and similar non-library metadata.

### 4. Validation

Validation is required before any provider ID lookup or rename planning.

The purpose of validation is to ensure that parsed data is consistent and reliable enough for automation. Validation should include:

- structure validation of parsed fields
- consistency validation within a movie or series folder
- conflict detection
- detection of duplicate or ambiguous matches

A confidence-based approach is recommended:

- high-confidence items can proceed automatically
- medium-confidence items should be marked for review
- low-confidence items should be skipped until manually resolved

### 5. Provider ID Lookup

After names are normalized and validated, the system performs provider ID lookup.

This lookup must be efficient and should operate on media entities, not on every file individually.

Recommended strategy:

- movies are matched per movie
- TV series are matched per series
- episodes are not matched individually for stored IDs

This keeps the number of API requests low and improves overall reliability.

The result of this phase is:

- selected provider
- selected provider ID
- confidence level
- candidate matches if review is needed

Only one final ID will be attached to each movie or TV series.

### 6. Rename Planning

Rename operations must never be executed directly from raw lookup results.

Instead, the system should generate a rename manifest containing:

- original path
- detected media type
- normalized title data
- selected provider ID
- confidence
- proposed new path
- action status

The rename manifest is the authoritative source for batch execution. Dry-run mode must be supported and should be the default behavior.

### 7. Batch Renaming

Renaming should be executed only after review of the generated plan.

Execution should happen in logical batches, for example:

- movies by letter range
- movies by parent folder
- TV series one show at a time
- manually approved subsets

The process should support:

- dry-run mode
- execution logging
- collision detection
- rollback capability

### 8. Review Workflow

Not all items should be renamed automatically.

A separate review process is required for:

- ambiguous provider matches
- unrecognized filenames
- conflicting titles or years
- inconsistent series grouping
- duplicate candidates

Review should be done over a generated report rather than directly in the filesystem.

Suitable report formats include:

- CSV
- JSON
- HTML summary

## Technical Approach

The recommended implementation is:

- logic written in Python
- filesystem operations executed either over a mounted NAS share or via shell/SSH against the NAS
- rename execution separated from scan and lookup logic

Shell should be used only as the execution layer for rename-related operations. Core logic such as parsing, classification, validation, provider ID lookup, and planning should remain in Python.

This approach makes the system easier to test, safer to run, and easier to extend.

## Design Principles

The project should follow these principles:

- no direct rename without a generated plan
- no bulk rename without validation
- no `.nfo` files
- no episode-level ID storage
- one provider ID per movie or TV series only
- readable filesystem structure
- safe, incremental execution
- manual review for uncertain cases
- priority on correctness over aggressive automation

## Expected Outcome

After completion, the media library should have:

- consistent and readable file naming
- consistent folder naming
- improved Jellyfin recognition
- a repeatable workflow for future additions
- a safe process for renaming in batches
- minimal filesystem clutter
- controlled handling of uncertain matches

The result should be a media library that is both easy to browse directly on disk and much more reliable when scanned by Jellyfin.

## Project schema

The project can be structured into the following modules:

```
src/jellyfin_media_normalizer/
├── __init__.py
├── main.py
├── constants.py
├── settings.py
├── cli/
│   ├── __init__.py
│   └── app.py
├── services/
│   ├── __init__.py
│   └── scan_service.py
├── scanners/
│   ├── __init__.py
│   └── library_scanner.py
├── models/
│   ├── __init__.py
│   └── media_item.py
└── utils/
    ├── __init__.py
    ├── logging.py
    └── paths.py
```
