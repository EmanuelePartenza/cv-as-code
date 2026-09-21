# Architecture Decision Records

One architectural or process decision per file, lightweight MADR form.

## Rules

- **File name:** `NNNN-title-in-kebab-case.md`, four-digit sequential numbering.
- **Status:** `proposed` → `accepted` → possibly `superseded by ADR-XXXX`.
- **Accepted ADRs are immutable.** A decision that changes is written as a *new*
  ADR that supersedes the old one; only the old one's status changes.
- **Link with the code:** where the choice is embodied, a comment `# see ADR-NNNN`
  makes it findable from the code.
- Created with `/adr`. Template: [0000-template.md](0000-template.md).

## When an ADR is needed

When the choice is architectural or about process **and** not obvious **or**
costly to undo. Not for reversible local implementation choices nor for style
preferences already covered by the [conventions](../02-engineering-conventions.md).

An ADR does not replace an entry in
[05-decisions-open.md](../05-decisions-open.md): if the choice belongs to the
maintainer, the decision is opened first, then — once taken — formalised in an ADR.

## Index

| ADR | Title | Status |
|---|---|---|
| [0001](0001-fact-grounded-profile.md) | Fact-grounded profile with provenance and a human gate | accepted |
| [0002](0002-file-contract-llm-stages.md) | File-contract LLM stages, three engines | accepted |
| [0003](0003-async-first-interaction.md) | Async-first interaction: questionnaires and decision entries | accepted |
| [0004](0004-reserved.md) | Reserved | — |
| [0005](0005-interview-preparation-stage.md) | Interview preparation as a pipeline stage | accepted |
| [0006](0006-code-data-split-and-data-root.md) | Code/data split: two repositories and the data-root contract | accepted |
| [0007](0007-language-layers.md) | Language layers: English framework surface, user locale data | accepted |
| [0008](0008-example-user-is-a-user.md) | Anti-overengineering rule amended: the example user is a user | accepted |
| [0009](0009-publication-boundary.md) | Publication boundary: fresh history and a mechanical test | accepted |
| [0010](0010-documentation-in-the-repository.md) | Documentation lives in the repository, single home in `docs/` | accepted |
| [0011](0011-commit-cadence-push-on-request.md) | Local commits free, push on explicit request | accepted |
| [0012](0012-rendering-reproducibility.md) | Rendering reproducibility: Typst from PyPI, vendored fonts | accepted |

Numbers 0001–0005 were first recorded in the maintainer's private working
repository, from which this framework was extracted; they are re-authored here
with the same numbers and the same decisions so that cross-references stay
stable. Number 0004 records a decision about the maintainer's own data and does
not apply to the framework; it is reserved.
