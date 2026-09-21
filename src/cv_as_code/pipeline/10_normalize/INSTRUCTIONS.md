# Stage 10 — normalize a job posting

You receive one job posting, stored verbatim in `jobs/{job_id}/raw.txt`. Produce
`jobs/{job_id}/job.yaml`: the same posting as structured data, so that later
stages can quote it and check a CV against it.

## What the input looks like

`raw.txt` may start with a few header lines written by the person who saved it
(`SOURCE:`, `COMPANY:`, `TITLE:`, `LOCATION:`, `NOTE:`), then a separator, then
the posting text as published. Use the header lines for `source` and `company`
when present; the posting text is the authority for everything else.

## Rules

1. **Quote, never paraphrase.** Each entry of `requirements[].text` is a phrase
   copied from the posting, in the posting's language, trimmed of bullets and
   trailing punctuation only. If the posting lists ten requirements you list ten;
   you do not merge, split, rank or reword them.
2. **`kind` follows the posting's own framing**: `must` for what it calls
   required, must-have, essential or simply lists as requirements; `nice` for
   what it calls preferred, nice-to-have, a plus, bonus. When the posting does
   not say, `must`.
3. **Nothing is inferred.** `salary`, `location`, `modes`, `company.industry`,
   `company.location` are filled only from what the posting states; otherwise
   `null` (or `[]` for `modes`). Do not guess seniority, team size, salary bands
   or working hours.
4. **`responsibilities`** are the posting's own phrases for what the role does,
   one per entry, shortened only by dropping filler.
5. **`keywords`** lists the technologies, methods, certifications and role words
   the posting names, as it spells them, without duplicates. They feed ATS
   coverage checks later; do not add synonyms the posting does not use.
6. **`language`** is the ISO 639-1 code of the posting's language.
7. **`id`** equals `{job_id}`; `raw` is the literal string `raw.txt`;
   `dedup_key` is `null`; `source.captured_on` is today's date; `source.channel`
   comes from the header (`SOURCE:`) or, if absent, from what the text shows
   (a company careers page, a job board), or `unknown`.
8. `schema_version: 1`, `kind: job`.

## Output

Write only the YAML document to `jobs/{job_id}/job.yaml`, then run
`cvac validate jobs/{job_id}/job.yaml`. If it fails, fix the document and run it
again. Do not modify `raw.txt`: it is the immutable record of what was published.
