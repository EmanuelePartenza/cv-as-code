---
description: Build or refresh a generic master CV for a user from their verified facts, through the human gate
argument-hint: "<master-name> [--user <slug>] [--language xx]"
disable-model-invocation: true
---

Produce `users/<user>/masters/<master-name>/cv-spec.yaml` — a generic CV driven
by the user's `search.yaml`, not by a posting — and render it once the user has
approved it. The rules live in the stage contract; this skill only sequences.

Argument received: `$ARGUMENTS`

> This skill writes into the user's data root and proposes a commit: it runs only
> when the user types it.

## Steps

1. **Locate the data root and validate it**: `cvac validate --all`. Fix nothing
   silently; a red validation is reported before anything else.
2. **Read the contract**: `cvac stage show 30_tailor --master <master-name>
   --job -` fails on the missing job, which is expected for a master; open
   `<package>/pipeline/30_tailor/INSTRUCTIONS.md` instead (the path is printed
   by `cvac stage list`), read `users/<user>/profile.yaml` and
   `users/<user>/search.yaml`, and apply the contract in **master mode**: no
   posting, no match, `job_id: null`, the target roles of `search.yaml` as the
   "posting". Language: the one requested, else the first of
   `search.cv_languages`.
3. **Write the spec as a draft** and validate it:
   `cvac validate users/<user>/masters/<master-name>/cv-spec.yaml`.
4. **Preview**: `cvac cv users/<user>/masters/<master-name> --mode draft` — a
   watermarked PDF. Open it or describe it; check the page budget.
5. **Self-review**, exactly as the contract's last section asks: coverage of
   the target roles, page budget, tone, and for every bullet the facts it
   rests on.
6. **Ask for the gate.** Only on an explicit "approved" from the user: set
   `status: approved` and `approved_on: <today>`, then
   `cvac cv users/<user>/masters/<master-name> --mode final`.
7. **Commit** the spec, the resolved JSON and the final PDF if the data root
   tracks PDFs (Conventional Commits, no push). Report: where the PDF is, what
   was left out and why (`omitted`), what the user should look at again.

If a master with that name exists, this is a refresh: copy it, keep
`based_on` unchanged, and say what changed since the last approval.
