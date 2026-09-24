# Stage 40 — a plan to close the gaps a match declared

You receive a match verdict (`matches/{job_id}.yaml`) with its declared gaps,
the posting (`job.yaml`), the user's profile and their search parameters.
Produce `users/{user}/growth/{job_id}.md`: an **internal** document, never
sent, that tells the user what they could do to become citable for what they
are not citable for today — without inventing anything about what they are.

## Rules

1. **One section per gap, the requirement verbatim.** Every `gaps[]` entry of
   the match becomes a section; `requirement` is copied from the match
   exactly, with its `kind`. Do not merge gaps and do not drop one because it
   looks minor.
2. **What the user already has is fact-cited.** `adjacent_facts` lists the
   ids of existing facts that are adjacent to the requirement (the same
   problem with other tools, a related technology, the other side of the same
   process). Cite only facts that exist in the profile; a `draft` fact may be
   cited and must be flagged as unverified in the prose. If nothing is
   adjacent, say "nothing adjacent" — that is a complete answer.
3. **The closing path delivers evidence, never claims.** Each `path[]` step is
   a concrete deliverable — a small project with acceptance criteria, a
   certification, a course with an assessed outcome, a shadowing arrangement
   — with an `artefact`: the thing that would exist afterwards and could be
   dropped in `inbox/` (a repository, a certificate, a dated report, a note
   signed by someone). Add `effort` as an honest estimate in hours or weeks.
   A step without an artefact is not a step.
4. **Candidate facts are future claims, labelled as such.** `candidate_facts`
   are sentences the user could write in their profile *after* the artefact
   exists, phrased in the past tense as a fact would be. They are never
   written to the profile by this stage or by anyone: a candidate becomes a
   fact only through stage 03 on the produced evidence and the user's
   verification.
5. **Do not soften and do not inflate.** Never assert that the user holds a
   skill the profile does not evidence; never call a `must` gap "minor";
   never propose a path longer than the search can bear (see
   `search.yaml`: constraints, salary floor, markets).
6. **Order and priority.** Sections are ordered `must` gaps first, then
   `nice`; within a kind, the gap with the most adjacent evidence first
   (shortest path). Say in one line at the top which gap, if closed, changes
   the verdict.
7. **Languages.** Prose in the user's `pivot_language`; `requirement` verbatim
   in the posting's language.
8. Frontmatter: `schema_version: 1`, `kind: gap-plan`, `user`, `job_id`,
   `created` = today, `gaps` as specified by the schema. The body repeats each
   gap as a heading with the reasoning, the path and the candidate facts.

## Output

Write the document, then run `cvac validate users/{user}/growth/{job_id}.md`
and fix until it passes. Then tell the user, in one sentence, which gap is
worth closing first and what it would cost.
