# Engineering conventions

> How code is written in this project. **Binding**: deviations are justified in an
> ADR. Complementary to [03-development-process.md](03-development-process.md)
> (the *how we work*). Underlying goal: a project in which finding *where to put
> your hands* is immediate, for a person and for the agent.

## Summary

| Area | Decision |
|---|---|
| Home of the documentation | Markdown in the repository (`docs/`), versioned with the code — [ADR-0010](adr/0010-documentation-in-the-repository.md) |
| Architectural decisions | Lightweight ADRs (MADR) in `docs/adr/`, one per decision, immutable |
| Diagrams | Mermaid inside the Markdown |
| Naming | English throughout; framework vocabulary from `docs/ARCHITECTURE.md` (fact, spec, stage, data root, gate) |
| Prose | English throughout |
| Formatter + linter | Ruff (`ruff format`, `ruff check`) |
| Type checker | none; annotations on every public function all the same |
| Tests | pytest; behaviour tests on invented data; golden values checked by hand |
| Error handling | `CvacError` hierarchy + explicit results for expected outcomes |
| Dependencies | `pyproject.toml`; `uv` locally, `pip` in CI; no lock file |
| Commits | Conventional Commits |
| Branching | trunk-based on `main`; short branches and PRs only when a second contributor exists |

---

## 1. Principles

1. **No drift.** Documentation and diagrams live in the repository as text,
   versioned with the code. What cannot be verified eventually lies.
2. **Correctness before speed** on the parts that cannot be wrong: the
   anti-invention gates, the publication boundary, anything that writes into a
   data root.
3. **Explicit boundaries.** Modules talk through declared interfaces; the data
   root is the only place user files are read from or written to.
4. **Every decision leaves a trace.** Non-obvious choices → ADR; comments that
   point to ADRs.
5. **Code is read more than it is written.** Explicit names, short functions, no
   unnecessary cleverness.

## 2. Language

### Naming
- English everywhere. Framework vocabulary is fixed: *fact*, *profile*, *search*,
  *cv-spec*, *master*, *application*, *stage*, *data root*, *gate*, *labels*.
- `snake_case` functions and variables, `PascalCase` classes, `UPPER_SNAKE`
  constants; `kebab-case` for CLI subcommands, stage directories and ids in data.

### Prose
- Docstrings, comments, commits, ADRs: English. User data is never assumed to be
  English and never appears in this repository.

## 3. Module visibility and structure

- Prefix `_` for what is **private to the module**.
- The public API is what the module exports on purpose; everything else is detail.
- **Imports at the top of the file**, never mid-file. A mid-file import "to break a
  cycle" is the symptom of a misplaced dependency: extract the shared helper into a
  neutral module.
- **No circular imports.** `dataroot` → `errors`; `validate`, `resolve`, `render` →
  `dataroot`; `letter` → `render`, `resolve`; `cli` → everything. Nothing points
  back.

## 4. Size and responsibility (anti-degradation)

1. **Budgets as triggers, not limits.** Soft caps: module ~500 lines, function
   ~60 lines. When crossed, **consider** a split before adding more; preferred
   split: façade + sub-modules.
2. **Single responsibility.** A feature outside a module's responsibility goes into
   a **new module**, not grafted onto a full one.
3. **Typed structures instead of ad-hoc tuples and dicts** for results
   (`ResolveResult`, `RenderResult`, `Report`).
4. No dead code, no TODOs untracked in [DEVLOG](../DEVLOG.md).

## 5. Output and logging

- The `cvac` command is a CLI: its output *is* the interface, so `print` is right
  there; messages are one line, English, and name ids and paths, never user text.
- Library modules do not print: they return values and raise.
- No user data in any log or message beyond what is needed to locate a problem.

## 6. Error handling

- **Raise** domain errors: `CvacError` and its subclasses (`ValidationError`,
  `RenderError`) in `src/cv_as_code/errors.py`; never a bare `Exception`.
- **Catch** specifically and only where you can act; a wide `except` that swallows
  everything hides bugs. The one broad catch is in `cli.main`, which turns a
  `CvacError` into exit code 1.
- **Expected outcomes** (validation failed, resource absent) are not exceptions:
  the validator returns a `Report`; the resolver reports unverified facts in draft
  mode instead of raising.
- Malformed input is **rejected at the boundary** — schema validation of every
  document — never left to propagate as a technical error ten levels down.

```
CvacError
├── ValidationError
└── RenderError
```

## 7. Comments and docstrings

- **Default: no comment.**
- Comment **only** the non-obvious *why*: a hidden constraint, a workaround for a
  known bug, surprising behaviour.
- Never the *what* (names say it). Never "removed X" or "added for Y": that goes in
  the commit.
- Docstrings: **one concise line** for the contract.
- Where a choice embodies an ADR: `# see ADR-NNNN`.

## 8. File format

- UTF-8 without BOM, LF line endings, 4-space indentation.
- Line length 100 (Ruff enforces it); no aggressive reformatting of code you are
  not touching.
- **No emoji** in code and documentation unless explicitly requested; the state
  markers in CHANGELOG/DEVLOG are the one convention.
- Markdown tables in **compact** form (no alignment padding).

## 9. Tests

Process detail in [03-development-process.md § Definition of Done](03-development-process.md).

- Every **new part** has behaviour tests: happy path **+ edges + malformed input
  rejected at the boundary + invariants**.
- Fixtures build **invented** data (`tests/conftest.py`); a real person's profile
  never enters a test — the publication boundary enforces it.
- A failing test is **diagnosed**, not disabled or rewritten to pass. If the test
  was wrong, it is updated **and** the reason goes in the commit.
- Touching an uncovered area: at least one **smoke test** before closing the task.
- `tests/README.md` states what is deliberately not covered.

## 10. Git

- **Conventional Commits.** First line ≤ 72 characters. Body after a blank line,
  explaining the **why**.
- Types: `feat` `fix` `docs` `refactor` `test` `chore` `perf` `build` `ci` `style`.
  Optional scope: module or area (`resolve`, `boundary`, `process`).
- `!` after the type for a breaking change of a data contract or the CLI.
- **Local** commits frequently, without asking, with green gates. **Push, PRs and
  merges only on explicit request** — [ADR-0011](adr/0011-commit-cadence-push-on-request.md).
- Never `--amend`, never `git add -A`. If a hook fails, fix the cause; never
  `--no-verify`.
- The only history rewrite ever allowed is on a repository that has **never been
  pushed**, to remove a publication-boundary hit before the first push.

Example:

```
fix(validate): reject a broken evidence path at validation time

A fact could cite a note that did not exist and still pass; the
resolver would not notice either. Existence is now checked relative
to the user directory and reported with the fact id.
```

## 11. Environment

- Any OS; paths always through `pathlib`, never by concatenating separators.
- Every command goes through the project's `.venv` (`make install`).
- Real commands live in `.claude/project.conf`, the single source for the
  verification engine, the skills and the git hooks; it is not versioned.
