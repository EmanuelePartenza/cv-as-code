# STATUS — cv-as-code

> **Live** snapshot, not history: overwritten freely. History lives in
> [CHANGELOG.md](CHANGELOG.md), the why in commit bodies, open proposals in
> [DEVLOG.md](DEVLOG.md). First file to read at session start, last to update at
> session end.

**Updated:** 2026-09-22
**Phase:** towards v0.1.0 — the first public release

## In progress

Building the public framework from the maintainer's private working repository,
with fresh history. Done so far: the `cvac` package and CLI with data-root
discovery (validate, resolve, render, cv, letter), the test suite and CI, the
publication boundary (structural rules + keyed denylist, pre-commit and CI),
the working method (verification engine, git hooks, process skills), and the
four production stage contracts with `cvac stage list|show|pack` and the
job/match/cover-letter schemas.

The example user Robin Ashcombe exists as a complete data root produced
through the stages, with the questionnaire and extraction contracts; CI
renders it and proves the PDFs identical across Python versions.

Next block: the domain skills (`cv-master`, `job-ingest`, `cv-tailor`,
`cover-letter`, placeholders `onboard` and `interview-prep`) and
`cvac skills install`.

## Blockers

(none)

## Next steps

1. Example user `robin` through the framework's own stages; CI builds the PDFs.
3. README that earns the positioning; ARCHITECTURE cut to what exists.
5. Publication checklist, `check-history`, tag v0.1.0, repository public.

## Decisions pending

Full queue in [docs/05-decisions-open.md](docs/05-decisions-open.md).

| ID | Title | Blocks? |
|---|---|---|
| — | (none) | — |

## Open proposals

Details in [DEVLOG.md](DEVLOG.md), which is the source of truth.

| ID | Priority | Title |
|---|---|---|
| 1.1 | medium | `identity_fields` per language not yet consumed by the resolver |
| 1.2 | low | cover-letter length is warned, not enforced |
| 2.1 | low | Typst compile diagnostics assumed to arrive as `RuntimeError` |
| 2.2 | low | Windows untested |

## Last 5 commits

<!-- AUTO:COMMITS -->
| Hash | Date | Message |
|---|---|---|
| `c04bdef` | 2026-09-22 | feat(stages): data-in contracts, evidence notes, questionnaires, footer |
| `949b5b5` | 2026-09-22 | feat(stages): stage contracts, job/match/letter schemas, cvac stage |
| `d1f7b9b` | 2026-09-22 | docs: navigator, status, conventions, process, decision queues, ADRs |
| `a467fee` | 2026-09-22 | chore(process): verification engine, git hooks, settings, skills |
| `956e0e9` | 2026-09-22 | feat(boundary): keyed denylist, pre-commit hook, history check |
<!-- /AUTO:COMMITS -->
