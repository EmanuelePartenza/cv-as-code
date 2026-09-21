# Stage 03 — extract facts from a document

You receive one document belonging to the user — a filled questionnaire, an old
CV, a performance review, a report, notes — and, if it exists, the user's
profile. Produce an **evidence note**, `users/{user}/notes/{name}.md`: a YAML
frontmatter listing the facts the document supports, and a body that quotes
the document so that each fact can be checked against its source in one read.

Facts you propose here are **not yet in the profile**. They enter it as
`draft`, each pointing back to this note as its evidence, and become
`verified` only when the user confirms them, one by one. You never write
`verified`.

## Rules

1. **Only what the document says.** A fact is a statement the document
   supports about what the person did, built, decided, was responsible for,
   achieved, or holds (a certificate, a degree). No inference from job
   titles, no "must have also done", no rounding a number the document does
   not give. If the document says "several", the fact says "several".
2. **Atomic and citable.** One fact = one thing that happened, in one
   sentence in the user's `pivot_language`, with the real numbers the
   document carries in `metrics`. Two things in one sentence are two facts.
3. **Quote the source.** Every proposed fact carries `quote`: the passage of
   the document it rests on, verbatim, in the document's language. The body
   of the note repeats the quotes under headings, so `anchor` can point at
   them (`evidence: notes/{name}.md#<anchor>` in the profile).
4. **Attach to the right parent.** `parent` is the id of the experience or
   project the fact belongs to (`exp-…`, `prj-…`), taken from the profile.
   If the document describes a position or project the profile does not
   have, propose it in `new_parents` with the dates the document gives
   (`null` where it does not), and use its id as `parent`.
5. **Do not duplicate.** If the profile already has a fact saying the same
   thing, do not propose it again; if the document adds precision (a number,
   a date) to an existing fact, propose the precision as a new fact and say
   in the body which existing fact it sharpens.
6. **Questionnaires are documents too.** A filled questionnaire is extracted
   like any other document: its answers are the quotes. Its answers to
   section G (what the user is looking for) are not facts: list them in the
   body under "Search parameters" for the user to carry into `search.yaml`.
7. **Frontmatter**: `schema_version: 1`, `kind: evidence`, `user`, `source`
   (the document's path relative to the user's directory), `document_date`
   (the document's own date, or `null`), `extracted_on` (today), `language`
   (of the document), `status: proposed`, `new_parents` (may be empty),
   `facts`.

## After the note

Run `cvac validate users/{user}/notes/{name}.md`. Then, in a Claude Code
session, add the proposed facts to `profile.yaml` under their parents with
the next free ids (`<parent>.fNN`), `status: draft`, `verified_on: null` and
`evidence: notes/{name}.md#<anchor>`; add any `new_parents`; set the note's
`status: applied`; move the source document from `inbox/` to `sources/` if it
came from the inbox; run `cvac validate --all`. In the manual path the user
does the same by hand — the note is written so that it can be copied.

Then tell the user how many facts are waiting for their confirmation and
where. Confirmation is theirs: `cvac fact verify <id>…`, or an explicit "yes"
per fact in session.
