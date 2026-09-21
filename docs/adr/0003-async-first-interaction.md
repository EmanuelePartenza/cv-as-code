# ADR-0003 — Async-first interaction: questionnaires and decision entries

- **Status**: accepted
- **Date**: 2026-07-23 (re-authored for the public repository on 2026-09-22 with the same number and decision)

## Context

Two kinds of questions come up when an agent works with a person on a CV.
Questions about the person's *career* (what did you actually do, with what
numbers, which of these thirty facts are true) and questions about the
*project* (which option, which trade-off). Both suffer when asked on screen:
the answer is composed under conversational pressure, detail is lost, and
nothing remains afterwards but the transcript.

## Decision

- **Substantive questions become documents.** Career facts are gathered with a
  structured questionnaire in the user's `interviews/` directory, written in
  the user's language, answered at the user's pace; when the user says it is
  complete, the agent extracts facts from it (always as `draft`) and the
  questionnaire becomes evidence like any note.
- **Project decisions that belong to the maintainer** get the same treatment:
  an entry with context, options with trade-offs and a recommendation in
  `docs/05-decisions-open.md`, answered in the document. Meanwhile the agent
  proceeds with the recommendation only if it is reversible and low-risk,
  marked provisional; otherwise that thread pauses.
- **Interactive questions are reserved for technical micro-clarifications.**

## Consequences

- Higher answer quality and an automatic evidence trail; the person studies
  the question before answering.
- Cost: wall-clock latency between question and answer, accepted; the session
  continues on non-blocked work.
- The two channels stay distinct on purpose: career facts and project decisions
  are different things and live in different places.

## Alternatives considered

- **Interactive interview in session.** Faster in the moment, scattered in the
  result; the first career interview of the maintainer's own project ran this
  way and was judged too lossy.
- **An external tracker for decisions.** Better notifications, but the decision
  leaves the repository and the agent needs an integration to see it.
