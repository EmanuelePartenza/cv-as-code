---
description: Create a new numbered ADR from the template, or supersede an existing one
argument-hint: "[title of the decision | supersede NNNN]"
disable-model-invocation: true
---

Record an architectural or process decision in `docs/adr/`. The why must outlive
the session.

Argument received: `$ARGUMENTS`

> This skill **creates files and proposes a commit**: it runs only when you type it.

## When an ADR is needed

When the choice is **architectural or about process** and **not obvious** or
**costly to undo**: a data contract, a boundary between the framework and a data
root, a library or format, a binding convention, a change to the public CLI, a
change to the process.

Not needed for: reversible local implementation choices, style preferences already
covered by the conventions, configuration values.

An ADR **does not replace** an entry in `docs/05`: if the choice belongs to the
maintainer, the decision is opened first (`/decide`), then - once taken -
formalised here.

## Steps

1. `ls docs/adr/` to find the next number (4 digits, sequential).
2. If the argument is `supersede NNNN`: read ADR NNNN, write the new ADR explaining
   what changed since, and in the old one change only the status to
   `Superseded by ADR-<new>`. **Change nothing else in the old ADR: accepted ADRs
   are immutable.**
3. Create `docs/adr/NNNN-title-in-kebab-case.md` from
   [docs/adr/0000-template.md](../../../docs/adr/0000-template.md) and fill it in:
   - **Context** - the force that requires the decision, the real constraints. Not
     the story of how we got here: the problem.
   - **Decision** - one or two plain sentences, indicative mood: "We adopt X".
   - **Consequences** - positive, **negative and costs** (if there are none, you are
     not looking hard enough), risks with mitigation.
   - **Alternatives considered** - with the concrete reason each was discarded.
4. Update the index in [docs/adr/README.md](../../../docs/adr/README.md).
5. Where the choice is embodied in code, add a comment `# see ADR-NNNN` at the
   relevant point: that is what makes the ADR findable from the code.
6. If the ADR changes a binding rule, update in the same commit
   [docs/02-engineering-conventions.md](../../../docs/02-engineering-conventions.md)
   or [docs/03-development-process.md](../../../docs/03-development-process.md), and -
   if it changes a non-negotiable rule - [CLAUDE.md](../../../CLAUDE.md).
7. Commit `docs: ADR-NNNN <title>`, asking for confirmation before running it.

Report in two lines what you recorded and which files you touched besides the ADR.
