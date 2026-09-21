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

---

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
