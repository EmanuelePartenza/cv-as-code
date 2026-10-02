# ADR-0018 — `AGENTS.md` is the navigator; the maintainer's project files sit at the root

- **Status**: accepted
- **Date**: 2026-10-02

## Context

The maintainer runs every personal project under one common contract (Partenza HQ), and cv-as-code is
one of them. The contract asks every repository for the same few files at the root: `progetto.yaml`, an
identity card read by the maintainer's tooling; `STATO.md`, a short status with fixed sections;
`AGENTS.md`, the instructions for any coding agent; and a `CLAUDE.md` that only imports `AGENTS.md`.
The contract's file names, keys and section titles are Italian in every project, whatever the
project's language.

Two accepted ADRs are touched. [ADR-0010](0010-documentation-in-the-repository.md) names `CLAUDE.md` as
the navigator. [ADR-0007](0007-language-layers.md) fixes an English surface for everything in the
repository.

## Decision

- **The navigator moves to `AGENTS.md`,** unchanged in role and content: what the project is, the
  non-negotiable rules, which document to load for which task. `CLAUDE.md` contains only the line
  `@AGENTS.md`, so Claude Code loads the same text and other agents read it directly. This amends
  ADR-0010 on the file name only.
- **`progetto.yaml` and `STATO.md` sit at the root.** `STATO.md` summarises
  [STATUS.md](../../STATUS.md) in a few lines, under the contract's section titles `In breve` (in
  short) and `Prossimi passi` (next steps), with English content, and is updated at session end with
  STATUS. This amends ADR-0007: these two files' names, keys and section titles are the only Italian in
  the repository.
- The publication boundary ([ADR-0009](0009-publication-boundary.md)) applies to these files as to
  every other: nothing personal, and no mention of the maintainer's private projects.

## Consequences

- One copy of the instructions for every agent, not only for Claude Code.
- Two more files at the root and one more to update at session end; the `/wrap` skill does it.
- A reader on GitHub meets two Italian file names; each is short and says what it is.

## Alternatives considered

- **Keep `CLAUDE.md` as the navigator and add a stub `AGENTS.md`.** Two files to keep in sync: the
  drift ADR-0010 exists to prevent.
- **Leave the project out of the contract.** The maintainer's tooling would not see its status, would
  not check it and would not back it up with the other projects.
