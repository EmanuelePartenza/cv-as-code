# ADR-0005 — Interview preparation as a pipeline stage

- **Status**: accepted
- **Date**: 2026-07-24 (re-authored for the public repository on 2026-09-22 with the same number and decision)

## Context

Sending an application is not the end of the pipeline: an interview follows,
and what a candidate *says* there is subject to the same embellishment risk as
what the CV says. Preparing for it is a distinct, repeatable activity, not
something to improvise per application.

## Decision

- A stage **`70_interview_prep`** (LLM, internal artefact) and a skill
  `interview-prep`, **built at a user's first real interview** — until then the
  skill exists as the written manual procedure, per the anti-overengineering
  rule ([ADR-0008](0008-example-user-is-a-user.md)).
- **Inputs**: the posting (`job.yaml`), the profile, the search parameters, the
  application's approved cv-spec (what was claimed) and the match verdict
  (declared gaps and angle).
- **Output**: `users/<slug>/applications/<job_id>/interview-prep.md` with a
  read of the company and role, likely technical and behavioural questions,
  **fact-grounded STAR stories** that cite `source_facts` like CV bullets,
  **honest gap-handling scripts** that never bluff, questions to ask, and
  logistics to clarify.
- **Gate**: the document is internal — for the candidate, never sent — so it
  needs no `approved` status; the fact-grounding rule still holds: a story that
  is not true does not go in.

## Consequences

- Closes the loop application → interview; facts are reused as narrative, not
  re-invented under pressure.
- For a user interviewing in a non-native language the stage doubles as the
  vehicle for practice: mock interviews run against the prepared document.
- Cost: another stage and skill to build, deferred to first real use.

## Alternatives considered

- **Ad-hoc preparation in session.** Works once; the second time it is
  improvised again and the fact-grounding discipline is the first casualty.
- **Folding it into the tailoring stage.** Different inputs (the approved spec
  and the verdict exist only after tailoring) and a different reader.
