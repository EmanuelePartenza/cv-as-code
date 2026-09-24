# Getting data in, and seeing it

The profile is a YAML file of atomic facts — right for an agent, hostile to a
person who wants to know what is there and what is missing. Three things solve
that without a UI: a standard questionnaire, extraction from documents, and a
generated report ([ADR-0013](adr/0013-data-in.md)).

## 1. The questionnaire (stage `05_interview`)

```bash
cvac stage pack 05_interview --user <slug> --name 01-onboarding > bundle.md
```

The bundle carries the questionnaire skeleton and the stage's rules; any
engine instantiates it in your language as `users/<slug>/interviews/01-onboarding.md`.
You fill it in at your own pace, in your own words, and set `status: filled`.
With an existing profile the stage works in **update mode**: it asks only for
what is missing or thin, pre-filling what it knows.

## 1b. Sorting the documents (stage `02_triage`)

People upload everything: three versions of one CV, a role description, a
review, a timetable. Stage 02 reads the whole inbox together with what is
already archived and writes `users/<slug>/sources.yaml`, one verdict per
document: `evidence` (about you: extracted), `context` (about the role or the
company: read while extracting so that roles and systems are named as the
organisation names them, never a source of facts), `duplicate` (the same
content as another document, in another language or format: extracted once,
through the primary it names) or `irrelevant` (nothing for a CV), with one
line saying why. The UI's *Sort, extract and apply everything* button runs
02, then 03 and 04 on each evidence document, then archives every document
under `sources/` with its verdict on record.

```bash
cvac stage run 02_triage --user <slug>
```

## 2. Extraction (stage `03_extract`)

Any document — the filled questionnaire, an old CV, a review, a logbook —
dropped under `users/<slug>/inbox/` (or already in `sources/`):

```bash
cvac stage pack 03_extract --user <slug> --document inbox/old-cv.md --name old-cv > bundle.md
```

The output is an **evidence note**, `users/<slug>/notes/old-cv.md`: its
frontmatter lists the proposed facts, each with the verbatim passage it rests
on; its body repeats the quotes under anchors. `cvac validate` checks that
every proposed fact attaches to an existing experience or a declared new one.
Then stage `04_apply` carries the note into the profile — deterministic
code, no model:

```bash
cvac stage run 04_apply --user <slug> --name old-cv      # or the UI's button on the note
```

The facts are appended under their parent as `draft`, pointing at the note
(`evidence: notes/old-cv.md#<anchor>`), ids continue the parent's numbering,
new parents are appended to their list, and every existing line of the
profile stays as it was; a fact the profile already holds is skipped; a
result that would not validate is not written. The note becomes `applied`
and the document moves from `inbox/` to `sources/`, the note repointed at
it (pass `archive=False` to `apply_note` to keep it where it is).

## 2b. Your own words (the curriculum form)

What no document says, you add on the curriculum page under the position or
project it belongs to: one fact, one thing that happened, with real numbers
if any. It enters `profile.yaml` like an extracted fact, with its evidence:
`notes/own-words.md#own-NNN`, a note that quotes your words and dates them
(ADR-0017). It is `draft` unless you add it with *confirm*, which is your
explicit act; a confirmed fact whose words you later change goes back to
draft.

## 3. Verification (the human gate as a command)

```bash
cvac fact verify exp-acme.f03 exp-acme.f04      # sets status and verified_on
cvac fact reject exp-acme.f05                   # never deleted, only rejected
```

`verify` refuses a fact whose evidence does not exist. Only the `status:` and
`verified_on:` lines of the named facts change; the file keeps its layout.

## 4. Seeing the profile (`cvac profile report`)

```bash
cvac profile report <slug>        # → users/<slug>/profile.report.md
```

Identity, timeline, every fact per experience with status, numbers and
whether its evidence resolves, skills with their evidence facts, education,
languages — and a **Completeness** checklist: draft facts to confirm, facts
without a number, skills without evidence, missing dates. It is derived,
gitignored, and regenerated on demand; the update-mode questionnaire asks for
the same items.

## The loop on the example

Robin's data root shows it end to end: `interviews/01-onboarding.md` →
`notes/01-onboarding.md` → `profile.yaml`, then a second document
(`sources/skerra-logbook-2025-excerpt.md` → `notes/02-logbook-excerpt.md`) that
sharpened two draft facts with dates and numbers; one was verified with
`cvac fact verify`, one stayed draft on purpose.
