# Decisions taken — archive

> Closed entries, moved here from [05-decisions-open.md](05-decisions-open.md)
> **once taken and implemented**. Reverse chronological order: newest at the top.
>
> This archive keeps the **path** of a decision (which options there were, what
> was discarded and why). Architectural decisions **also** have an [ADR](adr/),
> which is their normative form: the ADR says *what holds*, this archive says
> *how we got there*.

## Index

| ID | Date | Decision | ADR |
|---|---|---|---|
| D-01 | 2026-09-21 | Two repositories: public framework, private data roots, one copy of the code | [0006](adr/0006-code-data-split-and-data-root.md) |
| D-02 | 2026-09-21 | The framework's surface is English; user data is in the user's languages | [0007](adr/0007-language-layers.md) |
| D-03 | 2026-09-21 | The example user counts as a user of the framework | [0008](adr/0008-example-user-is-a-user.md) |
| D-04 | 2026-09-21 | Fresh public history with a mechanical publication boundary | [0009](adr/0009-publication-boundary.md) |
| D-05 | 2026-09-21 | Typst from PyPI, vendored fonts, reproducible PDFs | [0012](adr/0012-rendering-reproducibility.md) |
| D-06 | 2026-09-23 | A local, server-rendered web UI inside the package, a thin adapter over the library | [0014](adr/0014-local-ui-thin-adapter.md) |
| D-07 | 2026-09-24 | The UI as the bridge to a person's data: chooser, documents, jobs, stages run by Claude Code, an apply stage | [0015](adr/0015-claude-code-headless-engine.md) |

---

### D-07 — The UI as the bridge to a person's data — 2026-09-24

The maintainer described the UI he wanted: it asks where the data lives,
lets him configure and edit his data, drop documents from which Claude
compiles facts, and load postings from which Claude produces CVs, letters,
interview preparation and gap plans — "asking Claude" from the UI. Options:
(A) build it in slices, every screen a button over an existing stage
contract, with Claude Code's print mode as the engine (ADR-0015); (B) a chat
panel inside the UI. Chosen (A), answered "A" on 2026-09-24 with the
recommendation's defaults: the executable found on PATH or in the VS Code
extension's bundle, no spend cap, the account's model, and applying an
extraction note through the engine until a deterministic engine exists.
Built: `cvac stage run`, the chooser, the new-user form, the documents area
(upload, extract, apply, questionnaire), the jobs area with one button per
stage, the validating editor, stages `40_gap_plan`, `70_interview_prep` and
`04_apply` with their schemas and rules, all exercised on Robin. Left to the
roadmap: a deterministic engine for `04_apply`, a form-based editor.

### D-06 — A user interface for the tool — 2026-09-23

The maintainer asked for a UI; the plan had cut every UI. Options weighed: (A)
a local web UI inside the package, server-rendered, Flask and plain forms; (B)
a terminal UI; (C) a single-page application over a JSON API; (D) Streamlit or
NiceGUI; (E) keep Claude Code and Obsidian as the UI. Chosen (A): the only
option with a PDF preview, one language and one toolchain, and gates that are
buttons over the same library functions the CLI calls. Built in slices: the
gate and the views (2026-09-23); the data-root chooser, documents, jobs, the
editor and stage runs (2026-09-24, D-07). The planned "manual stage path in
the browser" was superseded by the engine of ADR-0015, which runs a stage
directly. Outcome: [ADR-0014](adr/0014-local-ui-thin-adapter.md).

### D-01 — Two repositories, one copy of the code — 2026-09-21

The maintainer's working repository held code and data together, with a git
history containing personal documents. Options weighed: (a) two repositories with
a configurable data root; (b) a private repository embedding the public one as a
submodule; (c) periodic copy from private to public. Chosen (a): it is the only
one that demonstrates something architectural — a clean boundary with an explicit
contract — and the only one without a daily tax (submodules) or guaranteed drift
(copies). Outcome: [ADR-0006](adr/0006-code-data-split-and-data-root.md).

### D-02 — English surface, any user language — 2026-09-21

A public tool needs one language for its own surface; its users do not. Chosen:
everything in this repository is English, and nothing in it assumes the language
of a user's facts, notes or CVs. Outcome: [ADR-0007](adr/0007-language-layers.md).

### D-03 — The example user is a user — 2026-09-21

The anti-overengineering rule ("no infrastructure before its first real use")
collided with a tool that strangers must be able to clone and run. Chosen: the
example persona is a first-class user whose data goes through the framework's
own stages, so what it exercises counts as used. Outcome:
[ADR-0008](adr/0008-example-user-is-a-user.md).

### D-04 — Fresh history and a mechanical boundary — 2026-09-21

The private history was not reliably scrubbable. Chosen: a new repository, a
structural boundary test committed before any code, a keyed denylist for the
maintainer's own strings, and a history check before the repository goes public.
Outcome: [ADR-0009](adr/0009-publication-boundary.md).

### D-05 — Typst from PyPI and vendored fonts — 2026-09-21

An external compiler binary and system fonts made the install story longer and
the PDFs machine-dependent. Chosen: the `typst` package from PyPI and the Lato
family vendored under its open licence, system fonts ignored. Outcome:
[ADR-0012](adr/0012-rendering-reproducibility.md).
