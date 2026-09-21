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

_(no open decision)_

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
