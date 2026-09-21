# DEVLOG — cv-as-code

Problems found and **not** fixed on the spot, proposals, technical decisions still
to take. It keeps what is noticed in passing traceable without derailing the
current task.

**Rule**: when exploring the code you find a weakness, a latent bug, dead code or a
broken convention outside the task's scope, **register it here and nothing more**.
Before adding, `grep` this file and the CHANGELOG for the file or function name:
the problem is often already tracked and should be updated, not rewritten.

States: `⏳ To do` · `🔄 Partial` · `✅ Done (commit <hash>)` · `❌ Discarded (reason)`

---

## Index

Single source of truth for state and priority. STATUS.md references it, never
duplicates it.

| ID | State | Priority | Area | Title |
|---|---|---|---|---|
| 1.1 | ⏳ | medium | resolve | `identity_fields` per language not yet consumed by the resolver |
| 1.2 | ⏳ | low | letter | cover-letter length is warned, not enforced |
| 2.1 | ⏳ | low | render | Typst compile diagnostics assumed to arrive as `RuntimeError` |
| 2.2 | ⏳ | low | platform | Windows untested |

---

## Template of an entry

```markdown
### X.Y Short title — ⏳ To do

**Problem**: description with file:line references.

**Impact**: what breaks, which risk is run.

**Proposed fix**: concrete steps.

**Priority**: low | medium | high + a one-line justification.
```

## Closing an entry

1. Cite the id in the commit body: `[closes DEVLOG X.Y]` (or `[advances DEVLOG X.Y]`).
2. Update the state on the `### X.Y` line and in the index.
3. Add a slim entry in [CHANGELOG.md](CHANGELOG.md) citing `[closes DEVLOG X.Y]`.

---

## 1. Pipeline

### 1.1 `identity_fields` per language not yet consumed by the resolver — ⏳ To do

**Problem**: which identity fields a CV shows (date of birth, photo) is a market
convention and belongs in data, not in template logic (ADR-0007). The labels
schema does not declare it yet and `resolve.py` copies every identity field into
the resolved JSON unconditionally; the `classic` template simply ignores `born`.

**Impact**: a template that renders `born` would do so for every language; there
is no per-language default and no per-spec override.

**Proposed fix**: add `identity_fields` to `labels.schema.json` and the three
labels files, filter `identity` in `resolve.py` accordingly, allow a cv-spec
override; land it with the example user so the change is exercised and the
maintainer's committed resolved snapshots are re-baselined knowingly.

**Priority**: medium — needed before a photo-bearing market template exists.

### 1.2 Cover-letter length is warned, not enforced — ⏳ To do

**Problem**: `letter.py` warns when a letter exceeds one page in any mode; a final
CV render fails on its page budget, a final letter does not.

**Impact**: an approved two-page letter renders cleanly.

**Proposed fix**: add `max_pages` to the letter frontmatter (default 1) and apply
the same draft-warns / final-fails rule as the CV; needs the letter schema (stage
contracts work package).

**Priority**: low — a letter's length is visible at approval time.

## 2. Rendering and platform

### 2.1 Typst compile diagnostics assumed to arrive as `RuntimeError` — ⏳ To do

**Problem**: `render.compile_typst` catches `RuntimeError` from the `typst` PyPI
package to turn compiler diagnostics into a `RenderError`. `TO VERIFY`: the
exception type was taken from the package's behaviour as observed, not from a
test with a deliberately broken template.

**Impact**: a different exception type would surface as a traceback instead of a
one-line error.

**Proposed fix**: a test rendering a template with a syntax error, asserting a
`RenderError` whose message contains the Typst diagnostic.

**Priority**: low — only the error path is affected.

### 2.2 Windows untested — ⏳ To do

**Problem**: paths use `pathlib` throughout and the `typst` package ships Windows
wheels, but nothing has run on Windows.

**Impact**: unknown; most likely candidates are the shell scripts under `.claude/`
and `.githooks/` (Git Bash required).

**Proposed fix**: one CI job on `windows-latest` running the test suite once a
contributor needs it.

**Priority**: low.
