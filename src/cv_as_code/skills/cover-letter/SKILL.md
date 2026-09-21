---
description: Write a fact-grounded cover letter for an application (stage 60) and render it once the user approves it
argument-hint: "<job_id> [--user <slug>]"
disable-model-invocation: true
---

Produce `users/<user>/applications/<job_id>/letter.md`, preview it, and render
the final PDF only after an explicit approval. The rules live in the stage
contract; this skill only sequences.

Argument received: `$ARGUMENTS`

> This skill writes into the user's data root and proposes a commit: it runs only
> when the user types it.

## Preconditions

The tailored spec `users/<user>/applications/<job_id>/cv-spec.yaml` exists (run
`/cv-tailor` first); the letter is written against what the CV claims.

## Steps

1. `cvac stage show 60_letter --job <job_id>`: every input `[present]`.
2. Open the stage's `INSTRUCTIONS.md` and follow it: frontmatter with
   `kind: cover-letter`, `status: draft` and every fact the body relies on in
   `source_facts`; four to six short paragraphs; the gap said, not hidden.
3. `cvac validate users/<user>/applications/<job_id>/letter.md` until green.
4. **Preview**: `cvac letter users/<user>/applications/<job_id> --mode draft`
   — it must be one page.
5. **Present** the letter with, for each paragraph, the facts it rests on, and
   **ask for the gate**.
6. Only on an explicit "approved": set `status: approved` and
   `approved_on: <today>`, then `cvac letter users/<user>/applications/<job_id>`
   (final is the default for an approved letter).
7. **Commit** (Conventional Commits, no push). Report where the PDF is.
