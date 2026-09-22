# STATUS — cv-as-code

> **Live** snapshot, not history: overwritten freely. History lives in
> [CHANGELOG.md](CHANGELOG.md), the why in commit bodies, open proposals in
> [DEVLOG.md](DEVLOG.md). First file to read at session start, last to update at
> session end.

**Updated:** 2026-09-23
**Phase:** v0.1.0 published (2026-09-22); v0.2 in progress

## In progress

Building the public framework from the maintainer's private working repository,
with fresh history. Done so far: the `cvac` package and CLI with data-root
discovery (validate, resolve, render, cv, letter), the test suite and CI, the
publication boundary (structural rules + keyed denylist, pre-commit and CI),
the working method (verification engine, git hooks, process skills), the six
stage contracts with `cvac stage list|show|pack`, the example user Robin
Ashcombe produced through the stages and rendered by CI, the six domain skills
installed by `cvac skills install`.

v0.1.0 is public and tagged; CI is green on both Python versions. v0.2, not yet
tagged, adds the data-in commands (`cvac profile report`, `cvac fact
verify|reject`, extraction on a second document of the example),
`identity_fields` per language and per spec (DEVLOG 1.1 closed), and the
local web UI `cvac ui` (ADR-0014, decision D-06 option A): slice 1 of 3, the
gate and the views, exercised on Robin and on the synthetic fixture.

Audit of the plan (private `docs/PLAN-2026-09.md`) on 2026-09-22: every work
package up to WP-12 is delivered. `05_interview` update mode is delivered
differently from the plan's `--mode update` flag: the stage decides full or
update from what the profile holds, and the questionnaire frontmatter records
it. WP-13 (`40_gap_plan`) stays on its trigger (D24: the first session in which
a user asks for it); WP-14 is roadmap only.

## Blockers

(none)

## Next steps

1. Maintainer: review v0.2 (`cvac profile report`, `cvac fact verify`,
   `identity_fields`), then `git push` and `git tag -a v0.2.0`.
2. Maintainer, in the personal data root: the Italian master now shows the
   date of birth by default (labels.it.yaml); keep it or set
   `identity_fields: [phone, links]` in the spec.
3. UI slice 2: the manual stage path in the browser (pack, paste the answer,
   validate); then slice 3 over the API runner (`cvac stage run`, its own ADR).
4. `40_gap_plan` when a user first asks for it; Robin's stretch match is the
   test bed.

## Decisions pending

Full queue in [docs/05-decisions-open.md](docs/05-decisions-open.md).

| ID | Title | Blocks? |
|---|---|---|
| D-06 | A user interface for the tool | decided (A); slices 2-3 in progress |

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
| `833dae2` | 2026-09-23 | feat(ui): a local web UI for the gates and views, cvac ui |
| `67cef24` | 2026-09-22 | docs(decide): D-06, a user interface for the tool |
| `be1afc6` | 2026-09-22 | docs(status): plan audit, v0.2 scope, DEVLOG 1.1 closed with its hash |
| `51bcd00` | 2026-09-22 | feat(i18n): identity_fields per language and per spec |
| `a303794` | 2026-09-22 | feat(data-in): profile report, fact verify/reject, second extraction |
<!-- /AUTO:COMMITS -->
