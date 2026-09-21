# ADR-0010 — Documentation lives in the repository, single home in `docs/`

- **Status**: accepted
- **Date**: 2026-09-22

## Context

Project documentation serves two readers with almost identical needs: the
person coming back after weeks, and the agent that must orient itself at every
session without prior context. If the two readers have separate documents, the
documents diverge — the most predictable failure mode there is. The
documentation must also be versioned with the code, so that a change and the
description of that change can sit in the same commit.

## Decision

Documentation lives **in Markdown inside the repository**, with **`docs/` as the
single home** for everything with content: architecture, conventions, process,
decisions, ADRs. `.claude/` holds **only** what is specific to the agent and has
no human reader: permissions, hooks, skills, scripts. No project rule lives in
`.claude/`.

`CLAUDE.md` at the root is a **navigator**: what the project is, the
non-negotiable rules, which document to load for which task. It indexes, it
does not duplicate.

## Consequences

- One copy of every rule, hence no drift between a "human" and an "agent"
  version; the documentation is versioned and reviewed with the code.
- Cost: `CLAUDE.md` is not self-sufficient — the agent opens the linked
  documents, which costs a few reads per session and saves loading everything
  every time.
- Risk: `docs/` ages against the code. Mitigation: the "documentation in the
  same commit" rule and the advisory link check run by the verification engine
  and the pre-commit hook.

## Alternatives considered

- **All instructions under `.claude/`.** Close to the agent, invisible to a
  person opening the repository on GitHub, and tied to one tool.
- **An external wiki.** Better editing, but outside the repository: not
  versioned with the code, not in the review, not visible to the agent without
  an integration.
- **Generated from docstrings.** Useful for an API reference, useless for
  architecture, process and decisions.
