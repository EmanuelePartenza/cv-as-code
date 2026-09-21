# Stage 60 — cover letter

You receive the normalised posting, the match verdict, the tailored CV spec for
this application and the profile. Produce
`users/{user}/applications/{job_id}/letter.md`: a YAML frontmatter and a
markdown body, **as a draft that a person will approve or reject**.

## Frontmatter

```yaml
---
schema_version: 1
kind: cover-letter
user: {user}
job_id: {job_id}
language: <the CV spec's language>
headline: <the CV spec's headline>
template: classic
output_name: <Full_Name>_Cover_Letter_<Company>.pdf
status: draft
approved_on: null
created: <today, YYYY-MM-DD>
source_facts: [<every fact id the body relies on>]
---
```

## Body

- Four to six short paragraphs; it must render on **one page**. Paragraphs are
  separated by a blank line; there is no markdown formatting in the body, it
  is rendered as plain text.
- Open with why this posting, in one or two sentences that only use what the
  posting itself says about the company and the role; no invented enthusiasm,
  no facts about the company you have not been given.
- Then the evidence: the two or three things from the profile that answer the
  posting's `must` requirements, each resting on facts listed in
  `source_facts`, with the real numbers the facts carry and no others.
- **Say the gap.** If the match verdict is `stretch`, one honest sentence about
  what the person has not done yet and what makes them credible anyway. A
  letter that hides a known gap is a letter the interview will contradict.
- Close in one sentence. Sign with the profile's full name.
- Write in the letter's `language`; keep the register plain and specific. No
  flattery, no superlatives, no claims about soft skills that no fact supports.

## Rules

1. Every factual claim in the body — a number, a technology, a scope, an
   outcome — rests on a fact listed in `source_facts`, and those facts must
   exist in the profile. The validator checks the list; you check the sentences.
2. Nothing from `draft` or `rejected` facts in a letter meant for approval.
3. **Never set `status: approved`.** That is the user's act.

## Output

Write the file, then run
`cvac validate users/{user}/applications/{job_id}/letter.md` and
`cvac letter users/{user}/applications/{job_id} --mode draft` (a watermarked
one-page preview). Present the letter with, for each paragraph, the facts it
rests on, and ask for the gate explicitly.
