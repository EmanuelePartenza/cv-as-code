# Decisions to take — open queue

> Choices that belong to the **maintainer**, not to the agent: product scope,
> legal and licensing, publication, irreversible architecture, a data contract.
> They are answered **in this document**, calmly, not on screen — see
> [ADR-0003](adr/0003-async-first-interaction.md). Archive of closed decisions:
> [06-decisions-taken.md](06-decisions-taken.md).

## How it works

1. **Opening** — Claude adds an entry with the template at the bottom: context,
   options with pros and cons, a reasoned recommendation. Command: `/decide`.
2. **Waiting** — if the choice is **reversible and low-risk**, Claude proceeds
   with the recommendation marked "provisional"; if it is **blocking or hard to
   undo**, it pauses that part and works elsewhere. The entry always says which.
3. **Answer** — the maintainer writes under *"Your answer"*, several decisions at
   once if convenient.
4. **Closure** — once taken **and implemented**, Claude fills in *"Outcome"*,
   moves the entry to [06-decisions-taken.md](06-decisions-taken.md) and removes
   it from here. A decision taken but not yet implemented **stays here**, marked
   "decided, implementation in progress".

**What does NOT enter this queue**: technical micro-clarifications
(`AskUserQuestion`, immediately); best-effort parameter values (marked
`TO VERIFY`, carried on — they open no decision and pause nothing); reversible
implementation choices (Claude proceeds and records them in the commit).

---

## Queue

### D-06 — A user interface for the tool: which kind, where it lives, what it does first

**Opened:** 2026-09-22 · **Blocks:** yes — the UI is product scope that the plan
explicitly cut (D14: "no TUI, no web UI, HTML is a roadmap line"); nothing is
built until this entry is answered. Meanwhile the framework work continues
where it is (v0.2.0 tag, `40_gap_plan` on trigger).

**Context.** The maintainer wants a UI to work with the tool. Today the tool
has three surfaces: the `cvac` CLI (deterministic tail, gates, report), the
Claude Code skills (an LLM engine in session) and `cvac stage pack` (any chat,
by copy and paste). What a person actually does with the tool, in order of
frequency: read the profile and see what is missing; verify or reject facts;
fill a questionnaire; run a stage on a posting; review a draft PDF and
approve a spec or a letter; render the final; keep track of applications. The
first five are the human gate and its views — exactly what a UI is for. What a
UI cannot be: a fourth copy of the rules. Every rule lives once, in the
library (`validate`, `resolve`, `render`, `facts`, `report`, `stages`); the CLI
is already a thin adapter over it, and a UI must be one too, in the same
sense that the skills are ([ADR-0002](adr/0002-file-contract-llm-stages.md)).
Constraints that bind any option: the UI reads and writes only through a
data root ([ADR-0006](adr/0006-code-data-split-and-data-root.md)); the human
gate stays a human act — a button is fine, an auto-click is not
([ADR-0001](adr/0001-fact-grounded-profile.md)); the framework's surface is
English, the data it shows is in the user's languages
([ADR-0007](adr/0007-language-layers.md)); no infrastructure before a user
exercises it, Robin counts ([ADR-0008](adr/0008-example-user-is-a-user.md));
Python 3.10+, CI on Linux, ruff and pytest as the quality floor (D22 of the
plan). One more fact shapes the ordering: running a stage *from* a UI needs an
LLM engine the UI can call, and the API runner (`cvac stage run`) is roadmap.
Without it a UI can only pack a stage and take the answer back — the manual
path in a browser. So the UI's first value is the gate and the views, not the
stages.

**Option A — Local web UI inside the package, server-rendered (recommended)**
- Shape: `pip install "cv-as-code[ui]"`, `cvac ui` starts a local server bound
  to `127.0.0.1` and opens the browser. Flask + Jinja2 templates + HTMX
  (vendored single file, no build step, works offline). A module `ui/` in the
  package that imports the library and that nothing in the library imports;
  the CLI stays the reference adapter.
- Pros: one language, one toolchain, same gates and CI; PDF preview in the
  browser (`<iframe>` on the rendered file); gates become buttons that call
  the same functions the CLI calls; a screen per user job; installable by a
  stranger with one command; the extra keeps the core dependency set
  unchanged for CLI-only users.
- Cons: a second surface to keep honest (every screen must be exercised on
  Robin and tested); Flask and Jinja2 are new dependencies (`TO VERIFY`: Flask
  3.x supports Python 3.10; htmx licence is 0BSD); a local server is still a
  server — bind to loopback only, no auth by design, single user.
- Cost / reversibility: first slice ~2 owner sessions; reversible — deleting
  `ui/` and the extra leaves the library untouched.

**Option B — Terminal UI (Textual)**
- Pros: closest to the CLI culture; keyboard-driven; one dependency; runs
  over SSH.
- Cons: no PDF preview (the artefact reviewers look at); long text
  (questionnaires, letters, evidence quotes) is painful in a terminal; Textual
  apps are harder to test than HTTP routes; for the person who asked, "a UI"
  most likely means a window.
- Cost / reversibility: similar to A, same reversibility.

**Option C — Single-page app (React or Vue) over a JSON API**
- Pros: richest interaction; a JSON API could serve other clients later.
- Cons: a Node toolchain, a second language, a build step in CI, a bundle to
  ship as package data; for a single-user local tool of ~2000 lines of Python
  this is the over-engineering rule 9 exists for. If a JSON API is wanted
  later, Flask routes can return JSON next to HTML without a SPA.
- Cost: 2-3× option A; the frontend becomes the heaviest part of the repo.

**Option D — Streamlit or NiceGUI**
- Pros: fastest first screen.
- Cons: their state model fights file-based data (reruns on every click,
  widgets keyed to session state); heavy dependency trees; hard to make a
  gate feel deliberate; weak fit for a portfolio project meant to be read.
- Cost: cheapest start, most expensive to keep honest.

**Option E — Keep Claude Code and Obsidian as the UI**
- Pros: zero code; the skills already sequence the stages; `profile.report.md`
  already opens in Obsidian; the maintainer uses both.
- Cons: the gates stay in the terminal; no PDF preview; a stranger without
  Claude Code has only the CLI; does not answer the request.

**Recommendation.** Option A, in three vertical slices, each exercised on
Robin and each a session with its own commit and tests:

1. **Gate and views** (no LLM involved): profile screen built from the
   report's data (not from its Markdown) with statuses, evidence quotes and
   the completeness checklist; *verify* / *reject* buttons calling
   `facts.set_status`; the list of masters and applications with *render
   draft*, PDF preview, *approve* (sets `status: approved` and `approved_on`
   on the person's click, nothing else) and *render final*; a validate
   button showing the report. This alone is the human gate with a face.
2. **Manual stage path in the browser**: choose a stage and its params, copy
   the pack, paste the answer, validate, see the result — `cvac stage pack`
   with a text box. Ugly but honest, and it works with any chat today.
3. **API runner** (`cvac stage run`, roadmap item, its own ADR) and then the
   stage screen calls it with progress and the same gate afterwards.

Also decided if A is chosen: `ui/` is inside the package, not a separate
repository (a second repository would duplicate the process machinery and
split the data contracts); the UI never commits to git — it shows the data
root's `git status` and leaves committing to the person; nothing in the UI
sets `verified` or `approved` except a handler bound to a button; the
publication boundary and the existing tests keep running unchanged; an ADR
records the choice (thin adapter over the library, server-rendered, local
only) since it is costly to undo once screens exist. Roadmap wording in
`docs/ARCHITECTURE.md` §10 ("HTML view of the profile report") is superseded
by that ADR.

If the real wish is a *conversational* UI — talking to the tool rather than
clicking through it — then the answer is not A but slice 3 first (the API
runner) and Claude Code as the surface, which already exists; say so and the
recommendation changes.

**Your answer.**
> _(to fill in: option; if A, confirm the slice order and whether the
> Italian labels' date-of-birth default should appear as a toggle in the UI)_

**Outcome.** _(filled in by Claude once implemented)_

---

## Template of an entry

```markdown
### D-NN — <title of the choice>

**Opened:** YYYY-MM-DD · **Blocks:** <what is paused, or "no, proceeding with X provisionally">

**Context.** Why the choice arises now, what makes it necessary, what is already
decided upstream (with links to the ADRs).

**Option A — <name>**
- Pros: <concrete>
- Cons: <concrete>
- Cost / reversibility: <...>

**Option B — <name>**
- Pros: <...>
- Cons: <...>
- Cost / reversibility: <...>

**Recommendation.** <Which and why, possibly conditional: "if speed matters, A;
if durability matters, B".>

**Your answer.**
> _(to fill in)_

**Outcome.** _(filled in by Claude once implemented: what was done, ADR if any)_
```
