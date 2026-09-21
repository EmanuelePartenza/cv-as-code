# ADR-0008 — Anti-overengineering rule amended: the example user is a user

- **Status**: accepted
- **Date**: 2026-09-21

## Context

The project's binding anti-overengineering rule reads: *no infrastructure file
is built before the session in which it is used on real data*. It has kept the
repository honest — nothing documented-but-unbuilt survives for long. It
collides with a tool that strangers must be able to clone and use: the example
user, the onboarding path and the stage contracts exist for users who do not
exist yet, and under a literal reading none of them could ever be built.

## Decision

The rule is amended as follows:

> No infrastructure file is built before the session in which **a user of the
> framework exercises it end to end**. The example user counts as a user, on
> one condition: **its data is produced through the framework's own stages and
> gates** — questionnaire, extraction, verification, master, posting, match,
> tailoring, letter — **never hand-written as a fixture**. Unit-test fixtures
> are minimal invented data derived for the test, never copies of a person's
> data and never the example's files.

What the rule still forbids: anything no user — the maintainer or the example —
exercises before publication. Connectors, an API runner, application tracking,
a browsing agent, remain roadmap until someone needs them.

## Consequences

- Reusability and honesty are reconciled: what the example exercises is, by
  construction, used.
- The example's data gains provenance: its questionnaire, notes and verdicts
  are real outputs of the pipeline and double as documentation of what each
  stage produces.
- Cost: producing example data through the stages costs agent time; the
  alternative — typed fixtures — would be faster and would prove nothing.
- Risk: the example drifts from the stages as they evolve. Mitigation: the
  end-to-end test renders the example on every CI run.

## Alternatives considered

- **Keep the rule literal and ship no example.** A stranger could not see a
  PDF without entering their own data first; the claim/reality gap the rule
  exists to prevent would reappear as "works on my data".
- **Drop the rule.** The repository would fill again with scaffolding for
  hypothetical users; the rule's track record argues against it.
