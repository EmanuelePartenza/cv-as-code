---
description: Open an entry in the asynchronous decision queue (docs/05-decisions-open.md)
argument-hint: "[title of the decision]"
disable-model-invocation: true
---

A choice has come up that **belongs to the maintainer**, not to you. Do not ask it
on screen: open it asynchronously, so it can be answered calmly with the whole
context at hand (ADR-0003).

Argument received: `$ARGUMENTS`

> This skill **writes into the project documents**: it runs only when you type it.

## First: is it really a decision to open?

**Yes**, if it is: product scope, make-vs-buy, legal or licensing, publication,
architecture that is not reversible, a data-contract change, or anything costly to
undo.

**No**, if it is: a technical micro-clarification (ask with `AskUserQuestion`), a
best-effort parameter value (mark it `TO VERIFY` and carry on), or a reversible
low-risk choice with a clear recommendation (proceed, mark it provisional, and
record it anyway).

If it falls under "no", say so and do not open an entry.

## Steps

1. Read [docs/05-decisions-open.md](../../../docs/05-decisions-open.md) and
   [docs/06-decisions-taken.md](../../../docs/06-decisions-taken.md): make sure the
   decision is not already open or taken. If it exists, update it.

2. Add an entry with the template at the end of `docs/05`, taking the next free id
   (`D-NN`). It must contain:
   - **Context** - why the choice arises now, what makes it necessary, what is
     already decided upstream (with links to the ADRs).
   - **Options** - at least two, each with **concrete pros and cons**: cost, risk,
     reversibility, impact on the schedule. No decoy options.
   - **Recommendation**, reasoned, possibly conditional ("if speed matters, A; if
     durability matters, B").
   - **Blocks?** - if yes, which part of the work is paused; if no, which option you
     are proceeding with provisionally.

3. Update the "Decisions pending" table in [STATUS.md](../../../STATUS.md).

4. **Meanwhile**: if the decision is reversible and low-risk, proceed with the
   recommendation marked "provisional, awaiting confirmation"; if it is blocking or
   hard to undo, pause that part and move to other useful work. State explicitly
   which of the two you are doing.

5. Report in two lines: what you opened, whether you are proceeding or paused, what
   you are working on now.

## On closure (when the maintainer answers)

Implement the decision, fill in the **Outcome** of the entry, **move** it to
`docs/06-decisions-taken.md`, **remove** it from `docs/05` and update STATUS. If the
decision is architectural, formalise it with `/adr` as well. A decision taken but
not yet implemented stays in the queue, marked "decided, implementation in progress".
