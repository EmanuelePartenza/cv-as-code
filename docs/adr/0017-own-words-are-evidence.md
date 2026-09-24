# ADR-0017 — The curriculum is the profile, edited in place; the person's own words are evidence

- **Status**: accepted
- **Date**: 2026-09-25

## Context

The UI had four places for one thing: documents in, notes extracted, a
review page, a profile view. The maintainer asked for one curriculum: every
fact about the person, whether a document proposed it or the person typed
it, in one structured place, to be confirmed and completed there, in any
order — the questionnaire's questions asked where the gap is, not in a
separate file. Two rules bound the design: `profile.yaml` is the single
source of truth ([ADR-0001](0001-fact-grounded-profile.md)) and a fact cites
its evidence, `verified` being the person's explicit act
([ADR-0013](0013-data-in.md)). A fact typed by the person has no document
behind it; forbidding it would send the person back to the questionnaire
file for every sentence.

## Decision

- **The curriculum page is `profile.yaml`, read and written in place.** Every
  edit from the form — identity, a language, an experience or project, its
  dates and company, an education entry, a skill — is a layout-preserving
  edit through the shared editor (`profile_edit.py`), validated before it
  stands and restored otherwise. Nothing is regenerated from an object
  model; comments and ordering survive.
- **The person's own words are evidence.** A fact the person types under an
  entry is appended to the profile with `evidence: notes/own-words.md#<anchor>`:
  one evidence note per user, `source: the person's own words, entered in
  the curriculum form`, where each addition is quoted verbatim and dated.
  The note is the same shape as an extraction note, so every fact of the
  profile cites a passage a reviewer can open.
- **Draft unless confirmed in the same act.** An added fact is `draft`; the
  form offers "add and confirm", which sets `verified` with today's date as
  the person's explicit act — the only case in which a write that creates a
  fact also verifies it, because the words are the person's own and no
  engine has reworded them.
- **What the documents found appears in the same place**: draft facts from
  extraction sit under their entry with their passage, to confirm, reword
  or reject; the review page stays as the filtered view of what awaits a
  decision.
- **The questionnaire remains** as the engine-agnostic path (stage 05, the
  form of the previous slice) for people who prefer prose or work from a
  chat; the curriculum form asks the same questions inline where an entry
  lacks facts, numbers or dates.

## Consequences

- One page to grow one's curriculum; the documents area feeds it, the
  jobs area consumes it.
- A fact without a document behind it is visible as such: its evidence
  note says it was stated by the person, and a reviewer sees the date.
- Cost: the editor must handle both list layouts (safe_dump's and the
  hand-written one) and flow or block mappings; the tests round-trip both.
- `search.yaml` is edited by replacing top-level keys; comments inside a
  replaced block are lost, comments between blocks survive.

## Alternatives considered

- **Facts without evidence when typed by the person.** Breaks the invariant
  every downstream rule relies on (evidence paths exist, verify needs
  evidence) and makes such facts indistinguishable from unsupported ones.
- **A form that regenerates `profile.yaml` from objects.** Loses comments,
  quoting and order in a person's file, and would silently rewrite what an
  agent or a text editor wrote.
- **Keeping the questionnaire as the only way to add one's own facts.** Slow
  for a person who knows what to say; the questionnaire's value is its
  prompts, which the form now shows inline.
