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
The facts then go into `profile.yaml` as `draft`, pointing at the note
(`evidence: notes/old-cv.md#<anchor>`); the document moves from `inbox/` to
`sources/`.

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
