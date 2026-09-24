# Decisions to take — open queue

> Choices that belong to the **maintainer**, not to the agent: product scope, legal and licensing, publication, irreversible architecture, a data contract. They are answered **in this document**, calmly, not on screen — see ADR-0003. Archive of closed decisions: [06-decisions-taken.md](06-decisions-taken.md).

## How it works

1. **Opening** — Claude adds an entry with the template at the bottom: context, options with pros and cons, a reasoned recommendation. Command: `/decide`.
2. **Waiting** — if the choice is **reversible and low-risk**, Claude proceeds with the recommendation marked "provisional"; if it is **blocking or hard to undo**, it pauses that part and works elsewhere. The entry always says which.
3. **Answer** — the maintainer writes under *"Your answer"*, several decisions at once if convenient.
4. **Closure** — once taken **and implemented**, Claude fills in *"Outcome"*, moves the entry to [06-decisions-taken.md](06-decisions-taken.md) and removes it from here. A decision taken but not yet implemented **stays here**, marked "decided, implementation in progress".

**What does NOT enter this queue**: technical micro-clarifications (`AskUserQuestion`, immediately); best-effort parameter values (marked `TO VERIFY`, carried on — they open no decision and pause nothing); reversible implementation choices (Claude proceeds and records them in the commit).

---

## Queue

### D-07 — The UI as the bridge to a person's data: scope, engine, order of the slices

**Opened:** 2026-09-24 · **Blocks:** no — proceeding with the recommendation provisionally; the three questions at the end are the only ones that pause anything. **Status:** points 1-3 of option A built (engine, UI slice 2, stages 40 and 70); point 4 (deterministic apply, form editor) roadmap.

**Context.** After D-06 (option A, slice 1 built) the maintainer described what the UI is for: a bridge between the framework and a person's own data. On first open it asks where that data lives; then it offers (1) a place to configure one's data and have it written to that folder, (2) a place to read and edit it, (3) a place to drop documents from which Claude compiles the data, (4) a jobs area where postings are uploaded and from which Claude produces CVs, cover letters, interview preparation and gap-closing plans — and, throughout, the possibility to "ask Claude" by starting Claude processes from the UI. Every item maps onto something the framework already defines: (1) is `cvac init` plus a user scaffold plus the questionnaire of stage `05_interview`; (2) is the profile screen plus an editor over the data files; (3) is `inbox/` plus stage `03_extract`; (4) is `jobs/<id>/raw.txt` plus stages 10, 20, 30, 60 and the two stages still on trigger, `40_gap_plan` (plan WP-13, D24) and `70_interview_prep` (ADR-0005) — this request is their trigger. "Ask Claude" is the engine question of D-06 slice 3: verified on 2026-09-24, Claude Code's print mode can run a stage as a subprocess with the person's own login (ADR-0015); no API key is needed. What the framework does not have yet: a deterministic *apply* of an evidence note into the profile (roadmap: it needs a layout-preserving YAML writer) — today the skills have Claude apply the note in session.

**Option A — Build it in this order (recommended)**
1. The engine, `cvac stage run` over Claude Code print mode, confined by an allow-list of tools and checked by the validator (ADR-0015); a run log the UI can show.
2. In the UI: the data-root chooser on first open (recent roots remembered in the user's config directory, never in the data root); a "new user" form that scaffolds `profile.yaml` and `search.yaml`; the jobs area (paste a posting → `raw.txt`, then buttons that run 10 → 20 → 30 → 60 → 70 and 40 with the run's log and the same gates as before); the documents area (upload to `inbox/`, run 03, generate the questionnaire with 05); an editor over `profile.yaml`, `search.yaml`, questionnaires and notes that validates before it saves.
3. Stages 40 and 70 as contracts, with schemas and validator rules, exercised on Robin through the engine; skills `gap-plan` and `interview-prep` become stage orchestrators.
4. Next: the deterministic apply of a note into the profile; a form-based editor once a layout-preserving YAML writer exists.
- Pros: every screen is a button over an existing contract; nothing is invented in the UI; the engine is the same for the terminal and the browser.
- Cons: the engine spends the person's Claude usage; a run can take minutes and the UI shows a log, not a chat.

**Option B — A chat panel inside the UI**
- Pros: closest to "ask Claude".
- Cons: a chat that can write into the data root is a second Claude Code, without its permission model; the rules would have to be restated in the panel. Rejected: the terminal (Claude Code with the skills) is that chat already, and the UI links to it.

**Recommendation.** A. Three things are yours:

1. **The `claude` executable.** It is not on this machine's PATH; the copy bundled with the VS Code extension works and is used as a fallback. Installing Claude Code's CLI (`npm install -g @anthropic-ai/claude-code` or the official installer) makes the engine independent of the editor. `TO VERIFY` on your side once.
2. **Applying extraction notes.** Until the deterministic apply exists, the UI's "extract" button runs stage 03 only (the note); a second button "apply with Claude" runs the same engine with the onboarding skill's step 3. Say if you prefer to wait for the deterministic apply instead.
3. **Cost and model.** Runs use your subscription; defaults: no spend cap, the account's default model, 40 turns. Say if you want a cap or a specific model as the default.

**Your answer.**
> _(to fill in)_

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