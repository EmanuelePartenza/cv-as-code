# STATUS — cv-as-code

> **Live** snapshot, not history: overwritten freely. History lives in
> [CHANGELOG.md](CHANGELOG.md), the why in commit bodies, open proposals in
> [DEVLOG.md](DEVLOG.md). First file to read at session start, last to update at
> session end.

**Updated:** 2026-09-24
**Phase:** v0.1.0 published (2026-09-22); v0.2 in progress

## In progress

v0.1.0 and v0.2.0 are public and tagged. v0.2.0 tags the data-in commands
(`cvac profile report`, `cvac fact verify|reject`). After it, on main and not
yet tagged: `identity_fields` per language and per spec; the local web UI
`cvac ui` (ADR-0014); `cvac stage run`, a stage executed by Claude Code in
print mode as a confined subprocess (ADR-0015); stages `40_gap_plan` and
`70_interview_prep` with schemas, validator rules and skills.

The UI (decision D-07, taken 2026-09-24) is the bridge to a person's data: first
open asks for the folder; new user; documents in (upload, extract, question-
naire); an editor that saves only what validates; the jobs area with one
button per stage; CV and letter gates; run logs. Every button is a library
call; nothing verifies or approves without the person's click. The UI speaks
English, French, German or Italian (ADR-0016); German CV labels ship. The
guided path (Start, Documents with many uploads and chained extraction,
Review with passages, the questionnaire as a form) is the UI's centre; stage
`02_triage` reads the documents together (context, duplicates, irrelevant);
the curriculum page edits `profile.yaml` in place, own words as evidence
(ADR-0017).

The example user exercises stages 03, 40 and 70 through the real engine and
04 through its code (two more documents extracted and applied; the gap plan
under `example/users/robin/growth/`; the preparation in the application).

## Blockers

(none)

## Next steps

1. Maintainer: try `cvac ui` on the personal data root end to end (a document
   → 03 → 04 → verify; a posting → 10 → 20 → 30); install Claude Code's CLI so
   the engine no longer depends on the VS Code extension's bundle.
2. Maintainer: tag the work pushed on 2026-10-02 once it has been tried end to
   end; `v0.2.0` points to `a303794`, the data-in commands only.
3. Form-based editing of the profile (the layout-preserving insertions of
   `apply.py` are the seed of the writer it needs).

## Decisions pending

Full queue in [docs/05-decisions-open.md](docs/05-decisions-open.md).

| ID | Title | Blocks? |
|---|---|---|
| — | (none) | — |

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
| `515ef3c` | 2026-09-24 | test(curriculum): own-words anchors relative to the note's content |
| `fe3aa22` | 2026-09-24 | feat(example): a fact in Robin's own words, through the curriculum form |
| `f6d806d` | 2026-09-24 | feat(ui): the curriculum, profile.yaml edited in place |
| `ece18bd` | 2026-09-24 | feat(example): Robin's inbox triaged by the real engine and archived |
| `5b16855` | 2026-09-24 | feat(stages): 02_triage, the documents read together |
<!-- /AUTO:COMMITS -->
