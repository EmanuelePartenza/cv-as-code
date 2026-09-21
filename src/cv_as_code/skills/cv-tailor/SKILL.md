---
description: Tailor a master CV to a posting (stage 30) and render it once the user approves it
argument-hint: "<job_id> --master <master-name> [--user <slug>]"
disable-model-invocation: true
---

Produce `users/<user>/applications/<job_id>/cv-spec.yaml` from a master and the
match verdict, preview it, walk the user through the self-review, and render
the final PDF only after an explicit approval. The rules live in the stage
contract; this skill only sequences.

Argument received: `$ARGUMENTS`

> This skill writes into the user's data root and proposes a commit: it runs only
> when the user types it.

## Preconditions

`jobs/<job_id>/job.yaml` and `users/<user>/matches/<job_id>.yaml` exist (run
`/job-ingest` first) and the master exists. If the verdict is `skip`, say so
and stop unless the user insists in writing.

## Steps

1. `cvac validate --all`; then `cvac stage show 30_tailor --job <job_id>
   --master <master-name>`: every input must be `[present]`.
2. Open the stage's `INSTRUCTIONS.md` (path printed by `cvac stage list`) and
   follow it: copy the master, re-select and re-word for the posting, cite
   facts for every line, keep `status: draft`, write honest `ats_coverage`.
3. `cvac validate users/<user>/applications/<job_id>/cv-spec.yaml` until green.
4. **Preview**: `cvac cv users/<user>/applications/<job_id> --mode draft`.
5. **Self-review**, in the order the contract lists it: coverage of the `must`
   requirements, page budget, declared gaps, tone, fidelity (each bullet with
   its facts).
6. **Ask for the gate.** Only on an explicit "approved": set `status: approved`
   and `approved_on: <today>`, then `cvac cv users/<user>/applications/<job_id>
   --mode final`.
7. **Commit** (Conventional Commits, no push). Report where the PDF is and
   suggest `/cover-letter <job_id>` if the user wants one.
