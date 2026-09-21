# Stage 30 — tailor a master CV to a posting

You receive a master CV spec (`masters/{master}/cv-spec.yaml`), the match verdict
for this posting, the normalised posting, the profile and the search
parameters. Produce `users/{user}/applications/{job_id}/cv-spec.yaml`: the same
kind of document, re-selected and re-worded for this posting, **as a draft that
a person will approve or reject**.

The same rules apply when there is no posting — a master CV built from
`search.yaml` alone: then `job_id` is `null`, the match input is absent, and
the "posting" is the user's target roles.

## How to build it

1. **Copy, then edit.** Start from the master's document; set `based_on:
   masters/{master}`, `job_id: {job_id}`, `status: draft`, `approved_on: null`,
   a new `output_name` (`<Full_Name>_<Role>_<Company>.pdf`, ASCII, no spaces).
   Keep `user`, `language`, `template`, `max_pages` unless the posting's
   language differs — then the target language is the posting's and every
   text is written in it.
2. **Re-select and re-order** entries and bullets by relevance to the posting:
   what the `angle` of the match says first; what the posting's `must`
   requirements name next; the rest after. Drop what does not serve this
   application into `omitted[]`, each with a reason.
3. **Re-word using the posting's vocabulary** where the facts allow it — the
   posting says "ETL pipelines" and the fact says "data loads": say pipelines
   if the fact is one. Every bullet and the summary cite `source_facts`; the
   cited facts must **support every claim in the sentence**: numbers, tools,
   scope, ownership. A sentence with one unsupported clause is an invented
   sentence.
4. **No new skills.** `skills_layout` may reorder and regroup, and may use the
   posting's terms for what the profile evidences; it may not add a technology
   or method that no fact evidences, and it may not promote a `draft` fact's
   content in a spec meant for approval.
5. **`ats_coverage`** is honest: `covered` lists the posting's keywords the
   spec now contains, `missing` the ones it does not — with the ones it does
   not because the profile lacks them, not because you forgot.
6. **Third parties.** Name clients, partners or products of the user's employer
   only if the profile's own facts name them: the profile is the policy.
7. **Never set `status: approved`.** Approval is the user's act; the same holds
   for `approved_on`.
8. **Language**: everything the CV shows — bullets, summary, headline, degree
   names, skill labels — in the spec's `language`; dates and section headings
   are the framework's job.

## Self-review, before asking for approval

Run `cvac validate users/{user}/applications/{job_id}/cv-spec.yaml` and fix until
it passes, then `cvac cv users/{user}/applications/{job_id} --mode draft` for a
watermarked preview. Then present to the user, in this order:

1. **Coverage** — the `must` requirements evidenced, the ones not, and what the
   CV says about them (nothing is a valid answer; a bluff is not).
2. **Page budget** — pages rendered versus `max_pages`.
3. **Declared gaps** — from the match, restated; whether the CV hides any.
4. **Tone** — one sentence: is this the person's voice or a template's.
5. **Fidelity** — for each bullet, the facts it rests on, so the user can check
   the rewording against the source in one read.

Ask for the gate explicitly. On an explicit "approved" the user (or you, on
their instruction) sets `status: approved` and `approved_on`, and runs
`cvac cv … --mode final`.
