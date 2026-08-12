# Commit Message Conventions

[English](COMMIT_CONVENTIONS.md) | [Čeština](../cs/COMMIT_CONVENTIONS.md)

This project uses a structured commit message style inspired by **Conventional Commits**.

## Format

```text
<type>\[optional scope]\[!]: <short description>

\[optional body]

\[optional footer(s)]
```

- **type** – category of the change (see table below)
- **scope** – optional, specifies the module/component affected
- **!** – indicates a **breaking change**
- **short description** – concise summary (~max 72 chars)
- **body** – detailed explanation if needed
- **footer** – references to issues, `BREAKING CHANGE: ...`, etc.

---

## Commit Types (Glossary)

| Type / Keyword | Meaning                                         | Example                                   |
| -------------- | ----------------------------------------------- | ----------------------------------------- |
| **feat**       | New feature for users or API                    | `feat(auth): add JWT login`               |
| **fix**        | Bug fix                                         | `fix(api): handle null payload`           |
| **docs**       | Documentation changes only                      | `docs(readme): update installation steps` |
| **style**      | Formatting, whitespace, no functional change    | `style(ui): unify button spacing`         |
| **refactor**   | Code restructuring without changing behavior    | `refactor(db): simplify query builder`    |
| **perf**       | Performance improvements                        | `perf(cache): reduce allocations`         |
| **test**       | Adding or updating tests                        | `test(api): add integration tests`        |
| **chore**      | Maintenance tasks (build, configs, dev tooling) | `chore(ci): update workflow`              |
| **ci**         | CI/CD pipeline changes                          | `ci: add linting step`                    |
| **build**      | Build process or dependency changes             | `build: switch to pnpm`                   |
| **bump**       | Version increase or dependency update           | `chore: bump version to 1.4.0`            |
| **upgrade**    | Significant technology upgrade                  | `upgrade: migrate to Django 5`            |
| **downgrade**  | Dependency downgrade                            | `downgrade: revert PostgreSQL to 14.x`    |
| **hotfix**     | Urgent production fix                           | `hotfix: fix critical NPE`                |
| **revert**     | Reverting a previous commit                     | `revert: "feat: add search"`              |
| **wip**        | Work in progress                                | `wip: dashboard layout`                   |
| **init**       | Initial commit                                  | `init: project skeleton`                  |
| **sync**       | Branch/submodule synchronization                | `sync: merge develop into feature/x`      |
| **cleanup**    | Remove unused code/files                        | `cleanup: remove v1 API`                  |

---

## SemVer & Release Cheat Sheet

Automation tools (e.g., `semantic-release`, `conventional-changelog`) usually map commit types to version
bumps like this:

### General Rules

- **MAJOR (X.y.z)** — any **breaking change**:
  - Add `!` after `type` or `scope`: `feat!: drop deprecated endpoints`
  - **or** include in the footer:

    ```text
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

| Commit Type                                                | SemVer Impact  |
| ---------------------------------------------------------- | -------------- |
| `feat`                                                     | **MINOR**      |
| `fix`, `perf` (behavior)                                   | **PATCH**      |
| `revert`                                                   | **PATCH**      |
| `type!` or `BREAKING CHANGE:`                              | **MAJOR**      |
| `docs`, `style`, `test`, `chore`, `ci`, `build`, `cleanup` | none (default) |

> Note: Tools can be configured differently; above is the common default.

---

## Examples

**MAJOR**:

```text
feat(auth)!: replace session auth with JWT

BREAKING CHANGE: Session-based endpoints were removed; use /auth/jwt.
```

**MINOR**:

```text
feat(ui): add compact table density mode
```

**PATCH**:

```text
fix(api): prevent crash when payload is null
```

**No release**:

```text
chore(deps): bump black from 24.2 to 24.8
```

---

## Pull Request And Issue Policy

- Before implementing a change intended for `main`, identify an existing open issue that defines the work. If no
  matching issue exists, create one before editing repository files.
- Every change merged into `main` must use a pull request.
- Every pull request targeting `main` must link at least one existing open issue from this repository.
- Put `Closes #123` in the pull request description when the merge completes the issue. GitHub will close the issue
  after the pull request is merged into the default branch.
- If the pull request is only partial work, link it manually through GitHub's Development section and use
  `Related to #123` in the description without a closing keyword.
- Use plain references such as `#123`; GitHub creates the link automatically. Do not construct a Markdown link around
  the issue number.
- Verify that the referenced issue exists and represents the change. Never guess or fabricate an issue number.
- Pull request titles use `<Conventional Commit subject> (#<primary-issue-number>)`, for example:
  `feat(parser): add movie filename parser (#123)`.
- The primary issue suffix must identify an existing open issue and match a supported relationship to that issue in
  the pull request body.
- When a pull request references multiple issues, select one primary issue for the title suffix and keep every
  relationship in the pull request body.
- Individual branch commits do not use the `(#<issue-number>)` suffix. A commit footer may reference an issue when
  useful, but the required traceability is maintained by the pull request.
- With squash merging, the final commit may contain the pull request number added by GitHub. Keep `Closes #123` in the
  pull request description rather than forcing the issue number into every commit subject.

## Commit Message Best Practices

- Use **imperative mood** and be concise: “add”, “fix”, “remove” — not “added”, “fixed”.
- Keep the **subject** line to ~72 characters; move details to the body.
- Use **scope** to narrow context (`feat(auth): ...`, `fix(db): ...`).
- Always mark breaking changes with `!` or `BREAKING CHANGE:` in the footer.
- Optionally reference an issue in a commit **footer** when it improves context:

```text
Related to #456
```

---

## Optional Tooling

- **Commit linting**: `commitlint` + `husky` (pre-commit / commit-msg hook).
- **Changelog generation**: `conventional-changelog` or `semantic-release`.
- **CI enforcement**: validate commits in PR pipelines.
