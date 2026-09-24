# ADR-0016 — The UI's chrome speaks the person's language; the library stays English

- **Status**: accepted
- **Date**: 2026-09-25

## Context

[ADR-0007](0007-language-layers.md) fixed the framework's surface in English:
identifiers, CLI output, error messages, documentation, stage instructions.
It was written for a tool driven from a terminal by people who read
documentation. The UI ([ADR-0014](0014-local-ui-thin-adapter.md)) is a
different surface: a window a person uses daily in their own language to
verify facts and approve CVs, and the maintainer asked for it in English,
French, German and Italian. What must not change: the rules live once, in
the library, whose messages the validator and the runner produce; the CLI
stays English; documentation, ADRs and stage instructions stay English; user
data stays in the user's languages, driven by `pivot_language` and the labels
files.

## Decision

- **The UI's chrome is translated**: menus, headings, form labels, buttons,
  explanations and the messages the UI itself composes — in the four
  languages `en`, `fr`, `de`, `it`. The English string is the key; catalogs
  live in the package (`ui/i18n/<lang>.yaml`); a test proves every key used
  by a template or a handler exists in every catalog, and no catalog carries
  an unused key.
- **Library messages stay English** and are shown as they are: validation
  errors, refusals of a gate, engine logs. They name ids and paths and are
  the same in the terminal; translating them would create a second wording
  of every rule.
- **The choice is the person's, once**: a selector in the header, persisted
  in the user's config directory next to the recent roots; before a choice,
  the browser's language among the four, else English.
- **Data stays data**: a CV language is a labels file, and the four UI
  languages each have one (`labels.de.yaml` arrives with this decision);
  the UI language and a CV's language are independent.

## Consequences

- ADR-0007 is amended, not replaced: its rule now reads "the framework's
  surface is English, except the UI's chrome, which is translated".
- Every new chrome string is written four times or the test fails; a
  translation is reviewed like code.
- A person sees two registers on one page: their language for the chrome,
  English for a validator's finding. The finding names the file and the id,
  which is what they need to act.

## Alternatives considered

- **Everything translated, library included.** Every rule would exist in
  five wordings, the CLI and the UI would disagree, and tests would have to
  match translated messages.
- **English UI only.** Fails the request: the person who verifies facts in
  Italian should not read "Verify" in English.
- **gettext.** Built for larger applications; a YAML mapping keyed by the
  English text is enough for a few hundred strings and reviewable by eye.
