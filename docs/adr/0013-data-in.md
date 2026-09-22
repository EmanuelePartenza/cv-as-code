# ADR-0013 — Data in: extraction and interview stages, facts enter as draft, verification is a command

- **Status**: accepted
- **Date**: 2026-09-22

## Context

The profile — nested, citable facts in YAML — is the right storage shape for
lineage and for an agent, and the wrong shape for a person: hard to fill in,
hard to read, impossible to see what is missing. Users also arrive with
documents (old CVs, reviews, notes) that already hold most of their facts.
Entering data through an interactive chat proved lossy; a web UI would collide
with the project's size and its engine-agnosticism.

## Decision

- **Data enters through documents, not chats.** Stage `05_interview` instantiates
  a fixed questionnaire skeleton in the user's language (full mode, or update
  mode asking only for what the profile lacks); stage `03_extract` turns any
  document — a filled questionnaire included — into an **evidence note** whose
  frontmatter lists the proposed facts, each with the verbatim passage it rests
  on, under anchors the profile's evidence pointers name.
- **Facts always enter as `draft`.** No stage, no engine and no command
  fabricates or verifies a fact. **Verification is a command**,
  `cvac fact verify|reject`, that changes only the status lines of the named
  facts, refuses a fact without existing evidence, and preserves the file's
  layout — so the gate is available to the manual path too.
- **The human view is generated, never stored.** `cvac profile report` writes
  a Markdown report (identity, timeline, facts with status and evidence
  resolution, skills, completeness checklist) to a gitignored file. The storage
  shape does not change to please a reader; the reader gets a derived view.
- **The profile schema stays at version 1**: evidence may be a list of paths,
  and the validator enforces that each exists.

## Consequences

- Provenance is complete: every fact points at a note that quotes its source,
  and the note points at the document.
- Zero new runtime and no UI; the report opens in any Markdown viewer, and the
  update-mode questionnaire asks exactly what the report lists as missing.
- Cost: applying proposed facts to `profile.yaml` is still an editing step (by
  an agent in session, or by hand in the manual path); a deterministic
  `apply` command would need a format-preserving YAML writer and is deferred.
- Known limit: the report sees structural gaps (no number, no evidence, draft),
  not semantic ones (a role that should have facts about X); that is what the
  update-mode interview and a reviewer add.

## Alternatives considered

- **A web UI to enter and browse the profile.** Collides with the tool's size,
  with engine-agnosticism and with "no useless complexity"; a Markdown report
  gives the reading half for free.
- **A TUI.** A new dependency and a second interface to maintain, still no
  answer to document ingestion.
- **Extraction writing straight into `profile.yaml`.** A model editing the
  source of truth in place is a broken profile waiting to happen, and it
  cannot work from a chat window; the evidence note is the safe intermediate.
