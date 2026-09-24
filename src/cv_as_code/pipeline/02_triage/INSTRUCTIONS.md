# Stage 02 — triage the documents, read together

You receive every document in the user's `inbox/`, the documents already
archived under `sources/`, the previous index (`sources.yaml`) if one exists,
and the profile if one exists. People upload everything they have, without
sorting: three versions of one CV, a company's role descriptions, a
performance review, a ferry timetable. Produce `users/{user}/sources.yaml`:
one entry per document, saying what it is and why, so that extraction reads
the right documents once and with the right context.

## The four kinds

- **`evidence`** — the document is about the person: what they did, built,
  decided, achieved, hold. A CV, a performance review, a reference letter, a
  certificate, a report they wrote, a logbook. It will be extracted (stage 03).
- **`context`** — the document is about the organisation, the team, the role,
  a product or a system, not about the person: a role description, an org
  chart, a product sheet, a process manual. It is never a source of facts
  about the person; it is read while extracting the evidence documents it
  informs, so that roles, teams and systems are named precisely. Fill
  `context_for` with the documents (paths) or experience ids it informs.
- **`duplicate`** — the same content as another document in the batch or in
  `sources/`: another language, another format, an older export with nothing
  new. Fill `duplicate_of` with the primary. Choose as primary the most
  complete version, then the one in the user's `pivot_language`. A document
  that carries *anything* the primary lacks is not a duplicate: it is
  `evidence`, and you say in `about` what it adds.
- **`irrelevant`** — nothing a CV or an application could use: a timetable,
  a receipt, someone else's document, an empty file. Say why in one line.

## Rules

1. **Read everything before classifying anything.** Duplicates and context
   only appear when the documents are compared.
2. **Keep the previous index.** A document already listed keeps its entry
   unless a new document changes it (a newly uploaded fuller version makes
   the old one a duplicate). Documents under `sources/` were archived by an
   earlier round: list them too, unchanged unless the comparison says
   otherwise, and never re-extract them (`note` names their note).
3. **Never invent the person.** `about` describes the document, not the
   person's merits; a document you cannot read (binary you have no tool for,
   unknown language) is `irrelevant` with the reason "could not be read", not
   guessed.
4. **Languages.** `about` in the user's `pivot_language` (English if there is
   no profile yet); `language` is the document's own.
5. Frontmatter: `schema_version: 1`, `kind: sources`, `user`, `updated` =
   today, `documents` as the schema specifies; paths relative to the user's
   directory (`inbox/…` or `sources/…`).

## Output

Write the index, then run `cvac validate users/{user}/sources.yaml` and fix
until it passes. End with one line per document: its kind and, for a
duplicate, its primary.
