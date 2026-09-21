---
description: Run every deterministic gate on the code just written and report GREEN or RED
argument-hint: "[--quick | --tests-only]"
allowed-tools: Bash(bash .claude/scripts/verify.sh:*)
---

Run the **verification engine** on the code just written, then report.
Argument received (may be empty): `$ARGUMENTS`

## Steps

1. Run all gates in one go:
   ```bash
   bash .claude/scripts/verify.sh $ARGUMENTS
   ```
   The gates come from `.claude/project.conf`: format, lint, the publication
   boundary, tests. Gates that are not configured are skipped, not failed.

2. **Read the report** and the final result (`GREEN` / `RED`).

3. If **RED**: open the output of the failing gate, **fix the cause** in line with
   [the conventions](../../../docs/02-engineering-conventions.md), and re-run until
   green. Do not bypass a check, widen an exclusion, or mark a test as skipped:
   **the code is fixed, not the gate**. If the gate itself is wrong, that is a
   decision: open one with `/decide`, do not change the gate on your own.

4. **Adversarial re-read**, mandatory on high-risk code (the anti-invention gates in
   `validate.py` and `resolve.py`, the publication boundary, anything that writes
   into a data root), recommended elsewhere. Prefer `/code-review`: it runs in a
   fresh context, so the reasoning that wrote the code is not the one judging it.
   Without it, re-read the diff looking for the defect, not for confirmation:
   invariants assumed but not enforced; edge cases (zero, empty, one, many,
   duplicates); malformed input rejected at the boundary or escaping as a technical
   error; encoding; errors swallowed by a wide `except`.

5. **Test completeness audit**: the gates say the tests *pass*, not that they are
   *sufficient*. Ask explicitly **what is not covered** and fill the real holes;
   keep `tests/README.md` honest about what is deliberately uncovered.

6. **Report**: gate results, what you fixed, what the re-read found, what remains
   to escalate. Problems outside the task's scope go into
   [DEVLOG.md](../../../DEVLOG.md), not into the code.

## Notes

- If `.claude/project.conf` is missing, copy it from `.claude/project.conf.example`.
- If the environment is broken (no `.venv`, missing dependencies), run
  `make install` and retry.
- `--quick` skips the tests (useful in a tight loop); `--tests-only` runs only the
  suite. Before calling a slice done, the full verification is still required.
- `/context` shows what is actually loaded in the session; `/doctor` checks the
  configuration; `/hooks` lists the active hooks.
