# STATUS — cv-as-code

> **Live** snapshot, not history: overwritten freely. History lives in
> [CHANGELOG.md](CHANGELOG.md), the why in commit bodies, open proposals in
> [DEVLOG.md](DEVLOG.md). First file to read at session start, last to update at
> session end.

**Updated:** 2026-09-24
**Phase:** v0.1.0 published (2026-09-22); v0.2 in progress

## In progress

v0.1.0 is public and tagged; CI is green on both Python versions. v0.2, not yet
tagged, adds: the data-in commands (`cvac profile report`, `cvac fact
verify|reject`); `identity_fields` per language and per spec; the local web UI
`cvac ui` (ADR-0014); `cvac stage run`, a stage executed by Claude Code in
print mode as a confined subprocess (ADR-0015); stages `40_gap_plan` and
`70_interview_prep` with schemas, validator rules and skills.

The UI (decision D-07, 2026-09-24) is the bridge to a person's data: first
open asks for the folder; new user; documents in (upload, extract, question-
naire); an editor that saves only what validates; the jobs area with one
button per stage; CV and letter gates; run logs. Every button is a library
call; nothing verifies or approves without the person's click.

The example user exercises stages 40 and 70 through the real engine (the
outputs under `example/users/robin/growth/` and the application).

## Blockers

(none)

## Next steps

1. Maintainer: answer the three questions of D-07 (the `claude` executable on
   PATH, applying extraction notes, cost and model defaults); try `cvac ui`
   on the personal data root end to end (a posting → stage 10 → 20).
2. Maintainer: review v0.2, `git push`, `git tag -a v0.2.0`.
3. A deterministic apply of an evidence note into the profile (layout-
   preserving), so extraction no longer needs a second Claude run.
4. Form-based editing once a layout-preserving YAML writer exists.

## Decisions pending

Full queue in [docs/05-decisions-open.md](docs/05-decisions-open.md).

| ID | Title | Blocks? |
|---|---|---|
| D-07 | The UI as the bridge to a person's data | no — three questions open, proceeding provisionally |

## Open proposals

Details in [DEVLOG.md](DEVLOG.md), which is the source of truth.

| ID | Priority | Title |
|---|---|---|
| 1.2 | low | cover-letter length is warned, not enforced |
| 2.1 | low | Typst compile diagnostics assumed to arrive as `RuntimeError` |
| 2.2 | low | Windows untested |

## Last 5 commits

<!-- AUTO:COMMITS -->
| Hash | Date | Message |
|---|---|---|
| `6b8d96e` | 2026-09-24 | feat(ui): the data-root chooser, jobs, documents, editor, runs |
| `9951353` | 2026-09-24 | feat(runner): cvac stage run over Claude Code, stages 40 and 70 |
| `d2a6498` | 2026-09-23 | docs(ui): same-origin rule, one assertion tightened, STATUS |
| `833dae2` | 2026-09-23 | feat(ui): a local web UI for the gates and views, cvac ui |
| `67cef24` | 2026-09-22 | docs(decide): D-06, a user interface for the tool |
<!-- /AUTO:COMMITS -->
