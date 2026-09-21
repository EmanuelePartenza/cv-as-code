# Stage 05 — the profile interview

You produce a questionnaire the user fills in at their own pace, in their own
language, away from any chat: `users/{user}/interviews/{name}.md`. Its answers
become facts later (stage 03), always as `draft`, verified by the user. The
questionnaire is the standard way data enters a profile; do not interview the
user interactively instead.

## Two modes, decided by what exists

- **Full** — `profile.yaml` is absent or has no facts: instantiate the whole
  skeleton (attached) for this user.
- **Update** — `profile.yaml` exists: instantiate **only what is missing or
  thin**. Missing: an experience without facts, a skill without
  `evidence_facts`, an unknown date, a language without a level, an empty
  search parameter. Thin: an experience with fewer than three facts, facts
  without a single number, a project with no outcome. Pre-fill what is known
  so the user confirms instead of retyping, and never ask again what the
  profile already answers.

## Rules

1. **Language.** Write the questionnaire in the user's `pivot_language` (from
   the profile; if there is no profile yet, in the language the user asked
   for, or English). The skeleton is English; you translate it, section
   titles included. Keep the framework's field names (`status`, `kind`)
   untouched in the frontmatter.
2. **One question, one thing.** Each question asks for one fact-sized answer.
   Where a number matters (volumes, durations, counts, money), ask for it and
   say that "I don't know" is a valid answer — a guessed number is worse than
   none.
3. **Ask for what happened, not for how it should sound.** No "describe your
   leadership style"; instead "what did you personally decide, and what
   happened as a result". Facts, not adjectives.
4. **Ask for evidence.** For each experience, ask which documents exist
   (reviews, reports, repositories, certificates) that could be dropped in
   `inbox/` for extraction.
5. **Ask what to leave out.** For each experience, "anything you would rather
   not show on a CV" — the answer becomes `omitted` reasons, not facts.
6. **Never propose facts.** The skeleton asks; it does not suggest answers a
   user might adopt without them being true.
7. **Frontmatter**: `schema_version: 1`, `kind: questionnaire`, `user`,
   `language`, `status: to-fill`, `created` (today), `mode: full | update`.
   The user sets `status: filled` when done.

## Output

Write the questionnaire, then run `cvac validate users/{user}/interviews/{name}.md`.
Tell the user where it is and that the next step, once it is `filled`, is stage
03 on that file. Do not fill it in yourself.
