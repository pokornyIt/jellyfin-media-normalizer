# jellyfin-media-normalizer

Normalize movie and TV series names for Jellyfin, validate matches, and add provider IDs for reliable library identification.

## Overview

`jellyfin-media-normalizer` is a project intended to clean up and standardize a large media library before it is imported into Jellyfin.

The project focuses on:

- scanning an existing media library
- classifying files as movies, TV series episodes, or unknown items
- normalizing file and folder names into a consistent format
- validating parsed results before any rename is executed
- looking up a single provider ID for movies and TV series
- preparing safe batch rename plans

The goal is to keep the media library readable on disk while also improving Jellyfin recognition and matching.

## Main Principles

- No `.nfo` files
- Only one provider ID per movie or TV series
- No episode-level IDs in filenames
- No automatic rename without validation
- No direct bulk rename without a generated plan
- Safe execution in logical batches

## Naming Rules

### Movies

Movie filenames:

- `Czech Title (Year) - CZ.ext`
- `Czech Title (Year) - EN (tit. CZ).ext`

Movie folder names:

- `Czech Title (Year) [imdbid-tt1234567]`
- `Czech Title (Year) [tmdbid-12345]`

### TV Series

Series folder names:

- `Series Name [tvdbid-12345]`
- `Series Name [tmdbid-12345]`

Episode filenames:

- `Czech Episode Title S01E02 - CZ.ext`
- `Czech Episode Title S01E02 - EN (tit. CZ).ext`

Notes:

- TV series folder names do not contain the year
- Episode filenames do not contain IDs
- Language markers always use two-letter codes such as `CZ`, `EN`, `DE`

## Core Features

### Library Scan

The project starts by scanning the media library and collecting information about files, folders, and naming patterns.

### Classification

Each item is classified as:

- movie
- TV episode
- unknown
- manual review required

### Name Normalization

Parsed names are converted into a unified internal representation that can be used for validation, provider ID lookup, and rename planning.

### Validation

Only sufficiently reliable matches should be allowed to continue automatically. Ambiguous items must be marked for manual review.

### Provider ID Lookup

The project looks up a single recommended provider ID:

- movies: typically TMDb or IMDb ID
- TV series: typically TVDB or TMDb ID

Only one final ID is stored in the folder name.

### Rename Planning

The project generates a rename manifest containing original paths, proposed new paths, confidence information, and action status.

### Batch Rename Execution

Renaming is executed only after review and only in controlled batches.

## Development Stack

| Tool                                            | Purpose                               |
| ----------------------------------------------- | ------------------------------------- |
| Python 3.14.2                                   | Core implementation language          |
| [uv](https://github.com/astral-sh/uv)           | Dependency and environment management |
| [ruff](https://github.com/astral-sh/ruff)       | Linting and formatting                |
| [pyright](https://github.com/microsoft/pyright) | Static type checking                  |
| [pytest](https://pytest.org)                    | Test framework                        |

## Technical Approach

The recommended implementation is:

- core logic in Python
- rename execution via filesystem operations over mounted storage or shell/SSH
- strict separation between scan, validation, lookup, planning, and execution

## Documentation

For the detailed project design, workflow, and metadata strategy, see:

- [PROJECT-DESCRIPTION.md](PROJECT-DESCRIPTION.md)
