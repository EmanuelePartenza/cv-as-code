---
description: Store a job posting verbatim, normalise it (stage 10) and give the user an honest match verdict (stage 20)
argument-hint: "<job_id> [--user <slug>]  (then paste the posting, or give its URL)"
disable-model-invocation: true
---

Take a posting from the user — pasted text, or a URL you may fetch — and run
the first two stages of the pipeline. Nothing here needs the user's approval;
the verdict is the point, and it must be blunt.

Argument received: `$ARGUMENTS`

> This skill writes into the user's data root: it runs only when the user types it.

## Steps

1. **Store the posting verbatim** in `jobs/<job_id>/raw.txt`. `job_id` is
   `YYYYMMDD-<company-slug>-<role-slug>` (today's date, lowercase, hyphens).
   Start the file with the header lines the contract expects (`SOURCE:`,
   `COMPANY:`, `TITLE:`, `LOCATION:`, `NOTE:`), a separator line, then the
   posting text exactly as published: no cleaning, no summarising. Postings
   disappear; this file is the record.
2. **Normalise**: `cvac stage show 10_normalize --job <job_id>` prints the
   inputs and the output path; follow `INSTRUCTIONS.md` of the stage and write
   `jobs/<job_id>/job.yaml`; `cvac validate jobs/<job_id>/job.yaml` until green.
3. **Match**: `cvac stage show 20_match --job <job_id>` (the user is the data
   root's `default_user` unless given); follow the stage's `INSTRUCTIONS.md`
   and write `users/<user>/matches/<job_id>.yaml`; validate it.
4. **Report the verdict in one blunt sentence** — `apply`, `stretch` or
   `skip` — with the gaps that drive it and, if the search is confidential, the
   flags the match raised. Then ask whether to tailor. **Do not start stage
   30 on your own**: `/cv-tailor <job_id> --master <name>` is the user's call.
5. **Commit** `raw.txt`, `job.yaml` and the match (Conventional Commits, no push).

Never fetch or automate anything from a platform whose terms forbid it; if the
user gives a URL on such a platform, ask for the text instead.
