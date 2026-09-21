# ADR-0007 — Language layers: English framework surface, user locale data

- **Status**: accepted
- **Date**: 2026-09-21

## Context

A public tool needs one language for its own surface — code, messages,
documentation, stage instructions, skill names — and English is the one that
reaches the widest audience of users and reviewers. Its users do not share that
language: their facts, notes, questionnaires and CVs are in Italian, German,
Portuguese, and a French CV expects things an American one must not carry.
The two separations must stay clean: nothing of the framework's English may
leak into what a user writes or receives, and nothing of a user's language may
be assumed by the framework.

## Decision

- **The framework's surface is English and fixed**: identifiers, CLI output,
  error messages, docs, ADRs, `INSTRUCTIONS.md` of every stage, skill names,
  the questionnaire skeleton.
- **Everything belonging to a user is locale data**, driven by three values:
  the profile's `pivot_language` (the language of facts, notes, questionnaires
  and of what the framework *asks* the user), a cv-spec's `language` (the
  language of that CV), and a `labels.<lang>.yaml` file per CV language holding
  every rendered string and convention: section headings, "present", the date
  format, month names, language and level names. Templates carry zero language
  strings.
- **A stage's `io.yaml` declares its output language** (pivot, target, posting
  or English) so that an engine instantiating an English instruction writes
  the output in the user's language.
- **Labels are validated**: a missing key fails `cvac validate`, never renders
  blank; a cv-spec whose language has no labels file fails validation. A user
  adds a language by dropping `i18n/labels.<lang>.yaml` into their data root and
  may contribute it upstream.
- **Market conventions beyond language** (photo, date of birth, address shape)
  are data too, and a later layer (`i18n/markets/`) when a user needs one:
  language and market are not the same thing.

## Consequences

- A stranger with data in any language uses the tool without touching its code;
  the maintainer's own data root, in Italian, is the first proof.
- Cost: every user-facing string must be routed through labels or through the
  stage's output-language rule; a template that hard-codes a word is a bug.
- Known limit: the framework cannot check that a stage *wrote* in the declared
  language; that is part of the human gate.

## Alternatives considered

- **Everything in the framework's language, users translate the output.** The
  CV is the deliverable; translating it after rendering defeats the lineage.
- **Per-language templates.** Multiplies layout code by languages; labels keep
  one template per layout.
- **A localisation framework (gettext).** Built for application UIs; here the
  strings live in data files a user edits, not in code.
