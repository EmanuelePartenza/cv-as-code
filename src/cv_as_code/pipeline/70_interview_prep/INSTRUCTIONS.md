# Stage 70 — prepare an interview from facts

You receive the posting (`job.yaml`), the match verdict (declared gaps and
angle), the application's `cv-spec.yaml` (what was claimed — normally
approved; if it is still `draft`, say so at the top and prepare anyway), the
user's profile and their search parameters. Produce
`users/{user}/applications/{job_id}/interview-prep.md`: an **internal**
document for the candidate, never sent, under the same anti-invention rule as
the CV (ADR-0005).

## Content, in this order

1. **A read of the company and the role**, from the posting only: what they
   seem to optimise for, what the role owns, what to clarify in the
   interview. No research beyond the inputs; say what is unknown.
2. **Likely questions** — technical and behavioural — for this posting, each
   followed by the fact ids that answer it. A question the profile cannot
   answer is listed too, with "no fact answers this" and a pointer to the gap
   script.
3. **Three to five STAR stories** (`stories` in the frontmatter, each with
   `title` and `source_facts`). Situation, task, action, result — every
   number and date taken from the cited facts; no invented detail, no
   rounding a number the facts do not carry. A `draft` fact may be used only
   if the story says it is not yet verified.
4. **Gap scripts** — for every gap in the match (`gaps_addressed` lists the
   requirements verbatim): an honest sentence the user can say — what they
   have not done, what is adjacent, how they would ramp. Never a bluff.
5. **Questions to ask them**, and **logistics and red flags to settle**
   (compensation against `search.salary`, hours, language of the job, mode
   and location against `search.markets`, scope).

## Rules

- A story that is not true, or not the user's, does not go in.
- The document needs no `approved` status; the user reads it and strikes what
  they would not say.
- Prose in the user's `pivot_language`; if the interview will be in another
  language (the posting's), add the rehearsal answers in that language under
  each story.
- Frontmatter: `schema_version: 1`, `kind: interview-prep`, `user`, `job_id`,
  `language` (of the prose), `created` = today, `stories`, `gaps_addressed`.

## Output

Write the document, then run
`cvac validate users/{user}/applications/{job_id}/interview-prep.md` and fix
until it passes. Then offer, in one line, a mock interview against it.
