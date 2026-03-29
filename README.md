# jellyfin-media-normalizer

Normalize movie and TV series names for Jellyfin. Scans a media library, classifies files, validates parsed results, and looks up provider IDs from TMDb and TVDB.

For the full project design, naming conventions, and implementation phases, see [PROJECT-DESCRIPTION.md](PROJECT-DESCRIPTION.md).

## Requirements

- Python 3.14.2
- [uv](https://github.com/astral-sh/uv) for dependency management

## Installation

```bash
git clone https://github.com/pokornyIt/jellyfin-media-normalizer.git
cd jellyfin-media-normalizer
uv sync
```

## Quick Start

```bash
# Scan only — no API keys needed
uv run jellyfin-media-normalizer scan

# Full parse with provider lookup — requires API keys
export $(cat .env | grep -v '^#' | xargs)
uv run jellyfin-media-normalizer parse
```

The `parse` command:
1. Scans the media library
2. Classifies and normalizes filenames
3. Validates parsed results
4. Looks up provider IDs (TMDb, TVDB) — first checks embedded IDs in folder names, then the local cache, then online APIs
5. Writes `data/workspace/reports/parse-review-report.json`
6. Writes `data/workspace/reports/unresolved-provider-report.json` for items without a resolved ID

## Configuration

All settings are read from environment variables. Create a `.env` file in the project root:

```ini
# Paths
JMN_LIBRARY_PATH=./data/library
JMN_WORKSPACE_PATH=./data/workspace

# Logging
JMN_LOG_LEVEL=INFO
JMN_LOG_FORMAT=text

# Safety
JMN_DRY_RUN=true

# Provider API keys
JMN_TMDB_API_KEY=your-tmdb-api-key
JMN_TVDB_API_KEY=your-tvdb-api-key

# How often to log provider lookup progress (default: every 100 items)
JMN_PROVIDER_LOOKUP_PROGRESS_INTERVAL=100
```

### Full environment variable reference

| Variable                                | Default                     | Description                                         |
| --------------------------------------- | --------------------------- | --------------------------------------------------- |
| `JMN_APP_NAME`                          | `jellyfin-media-normalizer` | Application name used in logs                       |
| `JMN_LIBRARY_PATH`                      | `./data/library`            | Root path of the media library to scan              |
| `JMN_WORKSPACE_PATH`                    | `./data/workspace`          | Root path for generated files                       |
| `JMN_CACHE_PATH`                        | `{workspace}/cache`         | Provider ID cache directory                         |
| `JMN_REPORTS_PATH`                      | `{workspace}/reports`       | Report output directory                             |
| `JMN_MANIFESTS_PATH`                    | `{workspace}/manifests`     | Rename manifest directory                           |
| `JMN_LOGS_PATH`                         | `{workspace}/logs`          | Log file directory                                  |
| `JMN_LOG_LEVEL`                         | `INFO`                      | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `JMN_LOG_FORMAT`                        | `text`                      | Log format (`text` or `json`)                       |
| `JMN_DRY_RUN`                           | `true`                      | Disable destructive operations by default           |
| `JMN_TMDB_API_KEY`                      | *(none)*                    | TMDb API key for online movie lookup                |
| `JMN_TVDB_API_KEY`                      | *(none)*                    | TVDB API key for online TV series lookup            |
| `JMN_PROVIDER_LOOKUP_PROGRESS_INTERVAL` | `100`                       | Log progress every N items during provider lookup   |

### TMDb API Key

1. Register at [themoviedb.org](https://www.themoviedb.org/) and create a free account.
2. Go to **Settings → API** and copy your **API Key (v3 auth)**.
3. Set `JMN_TMDB_API_KEY` to that value.

### TVDB API Key

TVDB API keys are **project-based**, not personal. You must register your application:

1. Visit [thetvdb.com/api-information](https://www.thetvdb.com/api-information) and create an account.
2. Click **Sign Up** to register a new project and fill in:
   - **Company / Project Revenue:** `Less than $50k per year`
   - **Company or Project Name:** `jellyfin-media-normalizer`
   - **Description:**
     ```
     Non-commercial open-source tool for normalizing and validating media library
     names for Jellyfin. Uses TVDB data for TV series metadata matching.
     Project: https://github.com/pokornyIt/jellyfin-media-normalizer
     ```
3. Copy the **API Key** and set `JMN_TVDB_API_KEY` to that value.

TVDB's free tier requires attribution. Comply with their [licensing terms](https://www.thetvdb.com/api-information).

**Note:** Without API keys, provider lookup uses only the local cache. Previously resolved items are still matched; new items are left unresolved.

## CLI Commands

### `scan`

Scans the media library and prints a summary.

```bash
uv run jellyfin-media-normalizer scan
```

Output:
```
Discovered 13342 media files.
- Filmy/Akcni/Avatar (2009) - CZ.mkv
...
```

---

### `parse`

Scans, parses, validates, and performs provider ID lookup. This is the main analysis command.

```bash
export $(cat .env | grep -v '^#' | xargs)
uv run jellyfin-media-normalizer parse

# or with custom report path
uv run jellyfin-media-normalizer parse --output /path/to/custom-report.json
```

Output:
```
Parsed 13342 media files.
Validation summary: passed=13127, review_needed=215, failed=0
Provider lookup summary: resolved=12697 (cache=12695, online=0, embedded=2), unresolved=430
Review report written to: data/workspace/reports/parse-review-report.json
Unresolved provider report written to: data/workspace/reports/unresolved-provider-report.json
```

Provider ID resolution order:
1. Embedded ID in folder name — e.g. `[imdbid-tt1234567]` or `[tmdbid-12345]`
2. Local provider cache (`data/workspace/cache/provider_ids.json`)
3. Online API (TMDb or TVDB, if API keys are configured)

---

### `report-scan`

Scans and parses, then writes a full JSON report of all parsed items.

```bash
uv run jellyfin-media-normalizer report-scan
uv run jellyfin-media-normalizer report-scan --output /custom/path/report.json
```

Default output: `data/workspace/reports/report-scan-results.json`

---

### `bootstrap-providers`

Initializes an empty provider cache file. Use this to reset cached provider matches.

```bash
uv run jellyfin-media-normalizer bootstrap-providers
```

Output:
```
Provider cache bootstrapped: data/workspace/cache/provider_ids.json
```

---

### `info`

Displays current runtime settings.

```bash
uv run jellyfin-media-normalizer info
```

---

### `validate-path`

Checks whether a given path exists on the filesystem. Useful for diagnosing path configuration.

```bash
uv run jellyfin-media-normalizer validate-path /path/to/check
```

## Development

### Stack

| Tool                                            | Purpose                               |
| ----------------------------------------------- | ------------------------------------- |
| Python 3.14.2                                   | Core language                         |
| [uv](https://github.com/astral-sh/uv)           | Dependency and environment management |
| [ruff](https://github.com/astral-sh/ruff)       | Linting and formatting                |
| [pyright](https://github.com/microsoft/pyright) | Static type checking                  |
| [pytest](https://pytest.org)                    | Test framework                        |

### Common commands

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/jellyfin_media_normalizer --cov-report=term-missing

# Lint and format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type check
uv run pyright
```
