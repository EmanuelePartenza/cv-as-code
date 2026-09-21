# The manual path: any chat, no agent

The intelligent steps of the pipeline are file contracts
([ADR-0002](adr/0002-file-contract-llm-stages.md)). A Claude Code skill reads
them in session; an API runner (roadmap) would call a model with them. This
page is the third engine: **you and a chat window**. It needs nothing but the
`cvac` command and a model you can paste text into.

## The loop

1. **See what a stage needs.**
   ```bash
   cvac stage list
   cvac stage show 20_match --user robin --job 20260915-saltmere-port-operations-officer
   ```
   `show` prints the resolved inputs (and whether each is present), the output
   path, its schema and the gate.

2. **Pack it.**
   ```bash
   cvac stage pack 20_match --user robin --job 20260915-saltmere-port-operations-officer > bundle.md
   ```
   `bundle.md` holds the stage's instructions, every input fenced, and what to do
   with the answer — including the language the output must be written in,
   resolved from the user's profile.

3. **Paste `bundle.md` into any chat**, take the answer, and save it where the
   bundle says (for `20_match`: `users/robin/matches/<job_id>.yaml`).

4. **Validate.**
   ```bash
   cvac validate users/robin/matches/20260915-saltmere-port-operations-officer.yaml
   ```
   A failing validation names the problem (an unknown fact id, a missing field,
   a requirement that does not quote the posting). Fix the file — or paste the
   error back into the chat — and validate again.

5. **Gates stay yours.** For `30_tailor` and `60_letter` the output is a draft:
   preview it (`cvac cv <dir> --mode draft`, `cvac letter <dir> --mode draft`),
   read every line against the facts it cites, and only then set
   `status: approved` and `approved_on` yourself and render `--mode final`.
   No chat and no agent may do that step.

## The stages

| Stage | Params | Gate | Output |
|---|---|---|---|
| `10_normalize` | `--job` | none | `jobs/<job_id>/job.yaml` |
| `20_match` | `--user --job` | none | `users/<u>/matches/<job_id>.yaml` |
| `30_tailor` | `--user --job --master` | human | `users/<u>/applications/<job_id>/cv-spec.yaml` |
| `60_letter` | `--user --job` | human | `users/<u>/applications/<job_id>/letter.md` |

`--user` defaults to the data root's `default_user`.

## Why it is the same thing

The bundle is exactly what a skill reads and what a runner would send: the
`INSTRUCTIONS.md` and the inputs named in `io.yaml`. Nothing is hidden in an
agent's context; if the manual path works, the contract is complete — and the
test suite packs every stage on the example user to keep it that way.
