# ADR-0011 — Local commits free, push on explicit request

- **Status**: accepted
- **Date**: 2026-09-22

## Context

An agent working through a session produces many changes. Frequent restore
points are needed: without intermediate commits a failed attempt costs hours of
reconstruction and the review faces one unreadable diff. Asking for
confirmation at every commit turns the session into a queue of interruptions.
A push is different in kind: it is outward-facing, it triggers CI, and on a
public repository it cannot be undone. The cost of a wrong push is not
symmetric with the cost of a wrong local commit.

## Decision

**Frequent local commits, without asking**, at every completed step, provided
the local gates are green. One completed step = one commit, Conventional
Commits message, the *why* in the body.

**Push, pull requests and merges only on explicit request** of the maintainer,
usually at session end. The agent never performs them on its own initiative;
`.claude/settings.json` denies `git push` to it.

Constraints that make free local commits safe: never `--amend`; never
`git add -A` (selective staging, so no local configuration or artefact lands
by accident); never `--no-verify` (a failing hook is fixed, not bypassed);
commits grouped by category — code, tests, docs, configuration.

The one exception to "never rewrite": a repository that has **never been
pushed** may have its history rewritten to remove a publication-boundary hit
([ADR-0009](0009-publication-boundary.md)).

## Consequences

- Continuous restore points; a history that tells the real path; reviews on
  small commits; nothing leaves the machine without a decision.
- Cost: a noisier local history than a curated one, and work that stays
  exposed to machine loss until pushed — a missing backup, not only missing
  visibility. The maintainer's data root has its own encrypted backup for that
  reason.

## Alternatives considered

- **Confirmation at every commit.** Maximum control; in practice fewer commits
  and fewer restore points.
- **No commits until session end.** One clean diff, too large to review, and a
  mid-session failure costs everything.
- **Automatic push to a working branch.** Solves the backup, publishes
  unreviewed work; rejected for a repository meant to be read by strangers.
