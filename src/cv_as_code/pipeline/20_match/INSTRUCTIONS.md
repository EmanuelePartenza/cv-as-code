# Stage 20 — match a posting against a profile

You receive a normalised posting (`job.yaml`), a user's profile (`profile.yaml`)
and their search parameters (`search.yaml`). Produce
`users/{user}/matches/{job_id}.yaml`: an honest verdict on whether this person
should apply, with the evidence for it. A severe recruiter would write it; so do
you.

## The verdict

- **`apply`** — every `must` requirement is evidenced by facts in the profile.
- **`stretch`** — one or more `must` requirements are not evidenced, but the
  profile holds *adjacent* evidence (a related technology, the same problem
  solved with other tools). The user may still apply; they must know it is a
  stretch.
- **`skip`** — a hard blocker: a `must` requirement with no adjacent evidence at
  all, a working language the profile does not have at the required level, a
  location or mode outside `search.markets`, years of experience far above the
  profile's, or a salary ceiling below `search.salary.min` when the posting
  states one. The match file is written anyway: a `skip` with reasons is worth
  keeping.

## Rules

1. **Strengths cite facts.** Each `strengths[]` entry names the fact ids
   (`exp-x.fNN`, `prj-x.fNN`) that support it. Cite only facts that exist; if a
   cited fact is `draft`, say so in the text ("not yet verified"). Never write a
   strength the profile does not evidence, however plausible.
2. **Gaps quote requirements.** Each `gaps[]` entry copies `requirement` from
   `job.yaml` exactly, keeps its `kind`, and says in `note` what the profile has
   that is adjacent — or that it has nothing. Do not soften: "no evidence" is a
   complete note.
3. **`angle`** is the positioning in two or three sentences: what makes this
   person credible for this posting, and what they must be upfront about. It
   is the seed of the tailored CV and the letter, not marketing copy.
4. **Confidentiality.** If `search.confidential` is true, list in
   `confidential_flags` every step of this posting that could expose the search
   to the current employer: application forms asking for a current-employer
   reference, public "open to work" requirements, referral schemes through the
   current employer's clients. Empty list otherwise.
5. **No numeric score.** A number would pretend a precision this analysis does
   not have.
6. **Languages.** Write `strengths[].text`, `gaps[].note` and `angle` in the
   profile's `pivot_language`. Keep `gaps[].requirement` in the posting's
   language, verbatim.
7. `schema_version: 1`, `kind: match`, `user`, `job_id`, `created` = today.

## Output

Write only the YAML document, then run
`cvac validate users/{user}/matches/{job_id}.yaml` and fix until it passes. Then
tell the user the verdict in one blunt sentence and ask whether to proceed to
tailoring; do not start stage 30 on your own.
