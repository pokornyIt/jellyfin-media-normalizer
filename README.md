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

## Configuration

### Quick Start

Once you have configured the API keys in a `.env` file, start the parsing and online provider lookup with:

```bash
# Load .env and run parse command with online provider lookup
export $(cat .env | grep -v '^#' | xargs) && uv run jellyfin-media-normalizer parse
```

This will:
1. Scan your media library
2. Parse and classify files and folders
3. Validate parsed results
4. Look up provider IDs online (if API keys are configured)
5. Generate a review report to `data/workspace/reports/parse-review-report.json`

### Provider API Keys

The project uses TMDb and TVDB APIs for online provider ID lookup. To enable online matching, configure the following environment variables:

#### TMDb API Key

1. Visit [The Movie Database (TMDb)](https://www.themoviedb.org/) and create a free account
2. Go to **Settings → API** in your account dashboard
3. Copy your **API Key (v3 auth)**
4. Set the environment variable:

```bash
export JMN_TMDB_API_KEY="your-tmdb-api-key-here"
```

#### TVDB API Key

1. Visit [TheTVDB.com API Information](https://www.thetvdb.com/api-information)
2. Create a free account (if you don't have one)
3. Click **Sign Up** to register a new project
4. Fill in the registration form with the following information:
   - **Company / Project Revenue:** `Less than $50k per year`
   - **Company or Project Name:** `jellyfin-media-normalizer`
   - **Description:**
     ```
     Non-commercial open-source tool for automatically normalizing and validating
     media library names for Jellyfin. Uses TVDB provider data for matching TV series metadata.
     Project: https://github.com/pokornyIt/jellyfin-media-normalizer
     ```
5. Copy the **API Key** provided for your project
6. Set the environment variable:

```bash
export JMN_TVDB_API_KEY="your-tvdb-api-key-here"
```

**Licensing Note:** TVDB's free tier requires attribution. Ensure you include proper attribution in your documentation and comply with their [licensing terms](https://www.thetvdb.com/api-information).

**Note:** TVDB API keys are project-based, not person-based. You need to register your application as a project to obtain an API key.

#### Applying Configuration

Once API keys are set, the online provider resolver will automatically use them during lookup:

```bash
# Option 1: Set environment variables in current shell
export JMN_TMDB_API_KEY="your-tmdb-api-key-here"
export JMN_TVDB_API_KEY="your-tvdb-api-key-here"
uv run jellyfin-media-normalizer parse

# Option 2: Set in .env file (if using a tool like python-dotenv)
echo "JMN_TMDB_API_KEY=your-tmdb-api-key-here" >> .env
echo "JMN_TVDB_API_KEY=your-tvdb-api-key-here" >> .env
uv run jellyfin-media-normalizer parse

# Option 3: Docker environment (if running in container)
docker run \
  -e JMN_TMDB_API_KEY="your-tmdb-api-key-here" \
  -e JMN_TVDB_API_KEY="your-tvdb-api-key-here" \
  jellyfin-media-normalizer:latest parse
```

**Note:** If API keys are not configured, the lookup chain will use only the local provider cache. This is suitable for re-processing previously matched items but will not add new matches from online sources.

## Development Stack

| Tool                                            | Purpose                               |
| ----------------------------------------------- | ------------------------------------- |
| Python 3.14.2                                   | Core implementation language          |
| [uv](https://github.com/astral-sh/uv)           | Dependency and environment management |
| [ruff](https://github.com/astral-sh/ruff)       | Linting and formatting                |
| [pyright](https://github.com/microsoft/pyright) | Static type checking                  |
| [pytest](https://pytest.org)                    | Test framework                        |

## CLI Commands

The application provides several command-line utilities for scanning, parsing, validating, and reporting on your media library:

### `scan`

Scan the media library and print a summary of discovered files.

```bash
uv run jellyfin-media-normalizer scan
```

Outputs:
- Total count of discovered media files
- Preview of first 10 files with relative paths

### `parse`

Scan, parse, classify, validate, and perform provider ID lookup. Generates a detailed review report.

```bash
# With API keys loaded from .env
export $(cat .env | grep -v '^#' | xargs) && uv run jellyfin-media-normalizer parse

# Or with inline environment variables
JMN_TMDB_API_KEY="your-key" JMN_TVDB_API_KEY="your-key" uv run jellyfin-media-normalizer parse
```

Outputs:
- Validation summary (passed, review_needed, failed counts)
- Review report to `data/workspace/reports/parse-review-report.json`

**Note:** This is the main command for analyzing your library and discovering provider matches.

### `report-scan`

Scan, parse, and generate a JSON report of results.

```bash
uv run jellyfin-media-normalizer report-scan [--output /custom/path/report.json]
```

Outputs:
- JSON report to `data/workspace/reports/report-scan-results.json` (or custom path)

### `bootstrap-providers`

Initialize or refresh the provider cache file. Useful for resetting cached provider matches.

```bash
uv run jellyfin-media-normalizer bootstrap-providers
```

Outputs:
- Empty provider cache at `data/workspace/cache/provider_ids.json`

### `info`

Display current runtime settings and configuration.

```bash
uv run jellyfin-media-normalizer info
```

Shows all active settings including:
- Library and workspace paths
- Cache, reports, and logs directories
- Log level and format
- API keys status (configured or not)
- Dry-run mode setting

### `validate-path`

Validate an arbitrary path for diagnostics (useful for testing).

```bash
uv run jellyfin-media-normalizer validate-path /path/to/check
```

## Technical Approach

The recommended implementation is:

- core logic in Python
- rename execution via filesystem operations over mounted storage or shell/SSH
- strict separation between scan, validation, lookup, planning, and execution

## Documentation

For the detailed project design, workflow, and metadata strategy, see:

- [PROJECT-DESCRIPTION.md](PROJECT-DESCRIPTION.md)
