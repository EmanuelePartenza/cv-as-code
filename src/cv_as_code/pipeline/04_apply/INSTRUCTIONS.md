# Stage 04 — apply an evidence note to the profile

You receive an evidence note (`notes/{name}.md`, output of stage 03, status
`proposed`) and the user's `profile.yaml`. Carry the note's proposed facts into
the profile **as `draft`**, each pointing back to the note as its evidence.
The profile is the source of truth and it is a person's file: you edit it in
place with the smallest possible changes; you never rewrite it.

## Rules

1. **Every proposed fact becomes one draft fact.** Under its `parent`'s
   `facts:` list, append a fact with: `id` = `<parent>.fNN`, NN continuing
   that parent's numbering (two digits, no gaps reused); `claim` verbatim from
   the note; `metrics` and `tags` verbatim (empty mapping and empty list when
   the note has none); `status: draft`; `verified_on: null`;
   `evidence: notes/{name}.md#<anchor>` with the note's anchor.
2. **New parents first.** An entry of `new_parents` becomes a new experience
   (`exp-…`) or project (`prj-…`) appended to the matching list, with the
   fields the note gives (`role`, `company`, `start`, `end`; `null` stays
   `null`) and its facts under it. Do not invent a field the note does not
   give.
3. **Touch nothing else.** Existing facts, their statuses and dates, the
   identity block, comments, blank lines, key order and quoting style stay
   exactly as they are. Use an editing tool that inserts lines; do not load
   and dump the YAML.
4. **No duplicates.** If the profile already holds a fact with the same claim
   and the same evidence anchor, skip it and say so in your final message.
5. **Never `verified`.** Every fact you add is `draft`; verification is the
   person's act (`cvac fact verify` or the profile screen).
6. **Close the note.** When the profile validates, set `status: applied` in
   the note's frontmatter — the only other file this stage may modify. If the
   note has `status: applied` already, stop and say so: it was applied before.
7. **Search parameters** listed in the note body (section G of a
   questionnaire) are not facts: do not write them anywhere; name them in your
   final message so the person carries them into `search.yaml`.

## Output

Edit `users/{user}/profile.yaml`, run `cvac validate users/{user}/profile.yaml`
and fix until it passes; then set the note's status and run
`cvac validate users/{user}/notes/{name}.md`. Finish with one line per fact
added (`id` and the first words of its claim) and the reminder that they are
draft until verified.
