# Commit Message Conventions

This project uses a structured commit message style inspired by **Conventional Commits**.

## Format

```

<type>\[optional scope]\[!]: <short description>

\[optional body]

\[optional footer(s)]

````

- **type** – category of the change (see table below)
- **scope** – optional, specifies the module/component affected
- **!** – indicates a **breaking change**
- **short description** – concise summary (~max 72 chars)
- **body** – detailed explanation if needed
- **footer** – references to issues, `BREAKING CHANGE: ...`, etc.

---

## Commit Types (Glossary)

| Type / Keyword | Meaning | Example |
|----------------|---------|---------|
| **feat**       | New feature for users or API | `feat(auth): add JWT login` |
| **fix**        | Bug fix | `fix(api): handle null payload` |
| **docs**       | Documentation changes only | `docs(readme): update installation steps` |
| **style**      | Formatting, whitespace, no functional change | `style(ui): unify button spacing` |
| **refactor**   | Code restructuring without changing behavior | `refactor(db): simplify query builder` |
| **perf**       | Performance improvements | `perf(cache): reduce allocations` |
| **test**       | Adding or updating tests | `test(api): add integration tests` |
| **chore**      | Maintenance tasks (build, configs, dev tooling) | `chore(ci): update workflow` |
| **ci**         | CI/CD pipeline changes | `ci: add linting step` |
| **build**      | Build process or dependency changes | `build: switch to pnpm` |
| **bump**       | Version increase or dependency update | `chore: bump version to 1.4.0` |
| **upgrade**    | Significant technology upgrade | `upgrade: migrate to Django 5` |
| **downgrade**  | Dependency downgrade | `downgrade: revert PostgreSQL to 14.x` |
| **hotfix**     | Urgent production fix | `hotfix: fix critical NPE` |
| **revert**     | Reverting a previous commit | `revert: "feat: add search"` |
| **wip**        | Work in progress | `wip: dashboard layout` |
| **init**       | Initial commit | `init: project skeleton` |
| **sync**       | Branch/submodule synchronization | `sync: merge develop into feature/x` |
| **cleanup**    | Remove unused code/files | `cleanup: remove v1 API` |

---

## SemVer & Release Cheat Sheet

Automation tools (e.g., `semantic-release`, `conventional-changelog`) usually map commit types to version bumps like this:

### General Rules
- **MAJOR (X.y.z)** — any **breaking change**:
  - Add `!` after `type` or `scope`: `feat!: drop deprecated endpoints`
  - **or** include in the footer:  
    ```
    BREAKING CHANGE: Removed legacy authentication
    ```
- **MINOR (x.Y.z)** — `feat` (new feature, no breaking changes).
- **PATCH (x.y.Z)** — `fix` and often `perf` (if behavior changes), or `revert`.

### Typically **No Release**
- `docs`, `style`, `test`, `chore`, `ci`, `build`, `cleanup`, `wip`, `sync`, `init`  
  → unless explicitly marked with `!` or `BREAKING CHANGE:`.

### Dependency-Specific
- **Security fix** in runtime dependency → `fix(...)` ⇒ **PATCH**.
- Regular dev dependency update → `chore(deps): ...` ⇒ **no release** (if runtime not affected).
- If an upgrade changes **public API**/runtime behavior → mark with `!` or `BREAKING CHANGE:` ⇒ **MAJOR**.

### Quick Mapping Summary

| Commit Type                 | SemVer Impact |
|-----------------------------|---------------|
| `feat`                      | **MINOR**     |
| `fix`, `perf` (behavior)    | **PATCH**     |
| `revert`                    | **PATCH**     |
| `type!` or `BREAKING CHANGE:`| **MAJOR**    |
| `docs`, `style`, `test`, `chore`, `ci`, `build`, `cleanup` | none (default) |

> Note: Tools can be configured differently; above is the common default.

---

## Examples

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

**No release**:
```

chore(deps): bump black from 24.2 to 24.8

```

---

## Best Practices

- Use **imperative mood** and be concise: “add”, “fix”, “remove” — not “added”, “fixed”.
- Keep the **subject** line to ~72 characters; move details to the body.
- Use **scope** to narrow context (`feat(auth): ...`, `fix(db): ...`).
- Always mark breaking changes with `!` or `BREAKING CHANGE:` in the footer.
- Reference issues in the **footer**:
```

Closes #123
Related to #456

```

---

## Optional Tooling

- **Commit linting**: `commitlint` + `husky` (pre-commit / commit-msg hook).
- **Changelog generation**: `conventional-changelog` or `semantic-release`.
- **CI enforcement**: validate commits in PR pipelines.
