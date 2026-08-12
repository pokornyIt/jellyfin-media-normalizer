# media-library-normalizer

[English](README.md) | [Čeština](README.cs.md)

Normalizuje názvy filmů a televizních seriálů pro Jellyfin. Prohledá knihovnu médií, klasifikuje soubory,
ověří parsované výsledky a vyhledá ID poskytovatelů v TMDb a TVDB.

> **Aktuální stav:** Toto vydání slouží pouze k analýze. Skenuje, parsuje, ověřuje, provádí základní párování
> poskytovatelů a zapisuje kontrolní sestavy. Plánování přejmenování, dry-run provedení, skutečné změny souborového
> systému, trvalá schválení a interaktivní kontrolní UI zatím nejsou implementované.

Úplný návrh projektu, konvence názvů a fáze implementace najdete v
[Popisu projektu](docs/cs/PROJECT-DESCRIPTION.md).

## Požadavky

- Python 3.14 (`>=3.14,<3.15`)
- [uv](https://github.com/astral-sh/uv) pro správu závislostí

## Instalace

```bash
git clone https://github.com/pokornyIt/media-library-normalizer.git
cd media-library-normalizer
uv sync
```

## Rychlý začátek

```bash
# Pouze skenování — API klíče nejsou potřeba
uv run media-library-normalizer scan

# Úplné parsování s vyhledáním poskytovatele — vyžaduje API klíče
export $(cat .env | grep -v '^#' | xargs)
uv run media-library-normalizer parse
```

Příkaz `parse`:

1. Prohledá knihovnu médií.
2. Klasifikuje a normalizuje názvy souborů.
3. Ověří parsované výsledky.
4. Vyhledá ID poskytovatelů — nejprve zkontroluje vložená ID v názvech složek, poté místní mezipaměť a
   nakonec online API v tomto pořadí: film -> TMDb; `tv_episode` (vyhledání na úrovni seriálu) -> TMDb TV, poté TVDB.
5. Zapíše `data/workspace/reports/parse-review-report.json`.
6. Zapíše `data/workspace/reports/parse-review-report.html` pro přehlednou kontrolu člověkem.
7. Zapíše `data/workspace/reports/unresolved-provider-report.json` pro položky bez nalezeného ID.
8. Zapíše `data/workspace/reports/unresolved-provider-report.html` pro přehlednou kontrolu nevyřešených položek.

## Konfigurace

Všechna nastavení se načítají z proměnných prostředí. V kořeni projektu vytvořte soubor `.env`:

```ini
# Cesty
MLN_LIBRARY_PATH=./data/library
MLN_WORKSPACE_PATH=./data/workspace

# Protokolování
MLN_LOG_LEVEL=INFO
MLN_LOG_FORMAT=text

# Bezpečnost
MLN_DRY_RUN=true

# API klíče poskytovatelů
MLN_TMDB_API_KEY=your-tmdb-api-key
MLN_TVDB_API_KEY=your-tvdb-api-key

# Jak často protokolovat průběh vyhledávání poskytovatelů (výchozí: každých 100 položek)
MLN_PROVIDER_LOOKUP_PROGRESS_INTERVAL=100
```

### Úplný přehled proměnných prostředí

<!-- markdownlint-disable MD013 -->
| Proměnná                                | Výchozí hodnota             | Popis                                                      |
| --------------------------------------- | --------------------------- | ---------------------------------------------------------- |
| `MLN_APP_NAME`                          | `media-library-normalizer`  | Název aplikace používaný v protokolech                     |
| `MLN_LIBRARY_PATH`                      | `./data/library`            | Kořenová cesta prohledávané knihovny médií                 |
| `MLN_WORKSPACE_PATH`                    | `./data/workspace`          | Kořenová cesta pro generované soubory                      |
| `MLN_CACHE_PATH`                        | `{workspace}/cache`         | Adresář mezipaměti ID poskytovatelů                        |
| `MLN_REPORTS_PATH`                      | `{workspace}/reports`       | Výstupní adresář sestav                                    |
| `MLN_MANIFESTS_PATH`                    | `{workspace}/manifests`     | Adresář manifestů přejmenování                             |
| `MLN_LOGS_PATH`                         | `{workspace}/logs`          | Adresář souborů protokolu                                  |
| `MLN_LOG_LEVEL`                         | `INFO`                      | Úroveň protokolování (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `MLN_LOG_FORMAT`                        | `text`                      | Formát protokolu (`text` nebo `json`)                      |
| `MLN_DRY_RUN`                           | `true`                      | Ve výchozím stavu zakazuje destruktivní operace            |
| `MLN_TMDB_API_KEY`                      | *(žádná)*                   | API klíč TMDb pro online vyhledávání filmů                 |
| `MLN_TVDB_API_KEY`                      | *(žádná)*                   | API klíč TVDB pro online vyhledávání televizních seriálů   |
| `MLN_PROVIDER_LOOKUP_PROGRESS_INTERVAL` | `100`                       | Protokolovat průběh každých N položek vyhledávání          |
<!-- markdownlint-enable MD013 -->

### API klíč TMDb

1. Zaregistrujte se na [themoviedb.org](https://www.themoviedb.org/) a vytvořte si bezplatný účet.
2. Přejděte do **Settings → API** a zkopírujte svůj **API Key (v3 auth)**.
3. Nastavte `MLN_TMDB_API_KEY` na tuto hodnotu.

### API klíč TVDB

API klíče TVDB jsou vázané na **projekt**, nikoli na osobu. Musíte zaregistrovat svou aplikaci:

1. Navštivte [thetvdb.com/api-information](https://www.thetvdb.com/api-information) a vytvořte si účet.
2. Kliknutím na **Sign Up** zaregistrujte nový projekt a vyplňte:
   - **Company / Project Revenue:** `Less than $50k per year`
   - **Company or Project Name:** `media-library-normalizer`
   - **Description:**

     ```text
     Non-commercial open-source tool for normalizing and validating media library
     names for Jellyfin. Uses TVDB data for TV series metadata matching.
     Project: https://github.com/pokornyIt/media-library-normalizer
     ```

3. Zkopírujte **API Key** a nastavte `MLN_TVDB_API_KEY` na tuto hodnotu.

Bezplatná úroveň TVDB vyžaduje uvedení zdroje. Dodržujte jejich
[licenční podmínky](https://www.thetvdb.com/api-information).

**Poznámka:** Bez API klíčů používá vyhledávání poskytovatele pouze místní mezipaměť. Dříve vyřešené položky se stále
spárují, nové položky zůstanou nevyřešené.

## Příkazy CLI

### `scan`

Prohledá knihovnu médií a vypíše souhrn.

```bash
uv run media-library-normalizer scan
```

Výstup:

```text
Discovered 13342 media files.
- Filmy/Akcni/Avatar (2009) - CZ.mkv
...
```

---

### `parse`

Prohledá knihovnu, parsuje názvy, ověří výsledky a vyhledá ID poskytovatelů. Jde o hlavní analytický příkaz.

```bash
export $(cat .env | grep -v '^#' | xargs)
uv run media-library-normalizer parse

# Nebo s vlastní cestou sestavy
uv run media-library-normalizer parse --output /path/to/custom-report.json
```

Výstup:

```text
Parsed 13342 media files.
Validation summary: passed=13127, review_needed=215, failed=0
Provider lookup summary: resolved=12697 (cache=12695, online=0, embedded=2), unresolved=430
Review report written to: data/workspace/reports/parse-review-report.json
Review HTML report written to: data/workspace/reports/parse-review-report.html
Unresolved provider report written to: data/workspace/reports/unresolved-provider-report.json
Unresolved HTML report written to: data/workspace/reports/unresolved-provider-report.html
```

Pořadí zjišťování ID poskytovatele:

1. Vložené ID v názvu složky — například `[imdbid-tt1234567]` nebo `[tmdbid-12345]`.
2. Místní mezipaměť poskytovatelů (`data/workspace/cache/provider_ids.json`).
3. Online API (pokud jsou nastavené API klíče), v tomto pořadí: film -> TMDb; `tv_episode`
   (vyhledání na úrovni seriálu) -> TMDb TV, poté TVDB.

---

### `report-scan`

Prohledá knihovnu, parsuje názvy a poté zapíše úplnou sestavu všech parsovaných položek ve formátu JSON.

```bash
uv run media-library-normalizer report-scan
uv run media-library-normalizer report-scan --output /custom/path/report.json
```

Výchozí výstup: `data/workspace/reports/report-scan-results.json`

---

### `bootstrap-providers`

Inicializuje prázdný soubor mezipaměti poskytovatelů. Použijte jej k obnovení mezipaměti nalezených poskytovatelů.

```bash
uv run media-library-normalizer bootstrap-providers
```

Výstup:

```text
Provider cache bootstrapped: data/workspace/cache/provider_ids.json
```

---

### `info`

Zobrazí aktuální běhová nastavení.

```bash
uv run media-library-normalizer info
```

---

### `validate-path`

Ověří, zda zadaná cesta existuje v souborovém systému. Hodí se při diagnostice konfigurace cest.

```bash
uv run media-library-normalizer validate-path /path/to/check
```

## Vývoj

### Technologie

| Nástroj                                         | Účel                          |
| ----------------------------------------------- | ----------------------------- |
| Python 3.14 (`>=3.14,<3.15`)                    | Hlavní programovací jazyk     |
| [uv](https://github.com/astral-sh/uv)           | Správa závislostí a prostředí |
| [ruff](https://github.com/astral-sh/ruff)       | Kontrola stylu a formátování  |
| [pyright](https://github.com/microsoft/pyright) | Statická kontrola typů        |
| [pytest](https://pytest.org)                    | Testovací framework           |

### Běžné příkazy

```bash
# Spuštění všech testů
uv run pytest

# Spuštění testů s pokrytím
uv run pytest --cov=src/media_library_normalizer --cov-report=term-missing

# Kontrola stylu a formátování
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Kontrola typů
uv run pyright
```
