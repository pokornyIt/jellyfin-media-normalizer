# Commit Message Conventions

Tento projekt používá strukturované commit zprávy inspirované **Conventional Commits**.

## Formát

```

<type>\[optional scope]\[!]: <short description>

\[optional body]

\[optional footer(s)]

````

- **type** – kategorie změny (viz tabulka níže)
- **scope** – volitelné, upřesňuje modul/část
- **!** – signalizuje **breaking change**
- **short description** – stručný popis (~max 72 znaků)
- **body** – delší popis
- **footer** – odkazy na issue, `BREAKING CHANGE: ...` apod.

---

## Typy commitů (slovník)

| Type / Keyword | Význam | Příklad |
|----------------|--------|---------|
| **feat**       | Nová funkce pro uživatele nebo API | `feat(auth): add JWT login` |
| **fix**        | Oprava chyby | `fix(api): handle null payload` |
| **docs**       | Změny dokumentace | `docs(readme): update installation steps` |
| **style**      | Formátování, mezery, bez vlivu na chování | `style(ui): unify button spacing` |
| **refactor**   | Přestrukturování bez změny chování | `refactor(db): simplify query builder` |
| **perf**       | Zlepšení výkonu | `perf(cache): reduce allocations` |
| **test**       | Testy | `test(api): add integration tests` |
| **chore**      | Údržba (build, configs, dev tooling) | `chore(ci): update workflow` |
| **ci**         | CI/CD | `ci: add linting step` |
| **build**      | Build, závislosti | `build: switch to pnpm` |
| **bump**       | Zvýšení verze / aktualizace závislosti | `chore: bump version to 1.4.0` |
| **upgrade**    | Významnější upgrade technologie | `upgrade: migrate to Django 5` |
| **downgrade**  | Downgrade závislosti | `downgrade: revert PostgreSQL to 14.x` |
| **hotfix**     | Rychlá oprava v produkci | `hotfix: fix critical NPE` |
| **revert**     | Vrácení předchozí změny | `revert: "feat: add search"` |
| **wip**        | Rozpracovaná změna | `wip: dashboard layout` |
| **init**       | Inicializační commit | `init: project skeleton` |
| **sync**       | Sladění větví/submodulů | `sync: merge develop into feature/x` |
| **cleanup**    | Úklid nepoužívaného kódu | `cleanup: remove v1 API` |

---

## SemVer & Release tahák

Automatizace (např. `semantic-release`, `conventional-changelog`) typicky odvozuje verzi takto:

### Základní pravidla
- **MAJOR (X.y.z)** — jakákoliv **breaking change**:
  - Přidej `!` za `type` nebo `scope`: `feat!: drop deprecated endpoints`
  - **nebo** použij footer:  
    ```
    BREAKING CHANGE: Removed legacy authentication
    ```
- **MINOR (x.Y.z)** — **feat** (nová funkce, bez breaking změn).
- **PATCH (x.y.Z)** — **fix** a většinou také **perf** (když opravuje chování), případně **revert**.

### Co obvykle **nevede** k releasu
- `docs`, `style`, `test`, `chore`, `ci`, `build`, `cleanup`, `wip`, `sync`, `init`  
  → pokud explicitně neoznačíš `!` nebo nepřidáš `BREAKING CHANGE:`.

### Specifika závislostí
- **Security fix** v runtime závislosti → `fix(...)` ⇒ **PATCH**.
- Běžné aktualizace dev závislostí → `chore(deps): ...` ⇒ **bez releasu** (pokud neovlivňují runtime).
- Pokud upgrade mění **public API**/runtime chování → označ `!` nebo `BREAKING CHANGE:` ⇒ **MAJOR**.

### Rychlá mapa (shrnutí)

| Commit typ                 | SemVer dopad |
|---------------------------|--------------|
| `feat`                    | **MINOR**    |
| `fix`, `perf` (behavior)  | **PATCH**    |
| `revert`                  | **PATCH**    |
| `type!` nebo `BREAKING CHANGE:` | **MAJOR** |
| `docs`, `style`, `test`, `chore`, `ci`, `build`, `cleanup` | žádný release (typicky) |

> Pozn.: Nástroje lze nakonfigurovat jinak; výše je běžný výchozí stav.

---

## Příklady

**MAJOR**:
```

feat(auth)!: replace session auth with JWT

BREAKING CHANGE: Session-based endpoints were removed; use /auth/jwt.

```

**MINOR**:
```

feat(ui): add compact table density mode

```

**PATCH**:
```

fix(api): prevent crash when payload is null

```

**Bez releasu**:
```

chore(deps): bump black from 24.2 to 24.8

```

---

## Doporučení pro praxi

- Piš v **imperativu** a stručně: „add“, „fix“, „remove“, ne „added“, „fixed“.
- Udrž **subject** do ~72 znaků; detaily do body.
- Používej **scope** pro modul/část (`feat(auth): ...`, `fix(db): ...`).
- Při breaking změně **vždy** použij `!` nebo `BREAKING CHANGE:` ve footeru.
- Odkazuj issue v **footeru**:
```

Closes #123
Related to #456

```

---

## Tipy pro nástroje (volitelné)

- **Linting commitů**: `commitlint` + `husky` (pre-commit / commit-msg hook).
- **Generování changelogu**: `conventional-changelog` nebo `semantic-release`.
- **CI kontrola**: validace commitů v PR pipeline.
