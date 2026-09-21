---
description: Close the session - update CHANGELOG and STATUS, propose grouped commits
disable-model-invocation: true
---

Close the current work session. Do not push.

> This skill **commits**: it runs only when you type it.

## 1. Reconnaissance

```bash
git status --short
git diff --stat
```

Read `.claude/edit-log.jsonl` if it exists: it is the exact list of files touched
in the session, recorded by the hook. Otherwise reconstruct it from `git status`.

If nothing changed, say so and stop.

## 2. Update the tracking files

Traceability without duplication: the **extended why** goes in the commit body,
not in three places. The four containers split the work like this:

| Where | What goes there | What does not |
|---|---|---|
| commit body | the extended why - the source of truth | - |
| [CHANGELOG.md](../../../CHANGELOG.md) | one slim entry per session, **at the top** | the extended why |
| [STATUS.md](../../../STATUS.md) | only "In progress" and "Blockers"; overwritten | history |
| [DEVLOG.md](../../../DEVLOG.md) | problems found and **not** fixed | what you already fixed |

- **CHANGELOG.md**: Conventional title + 3-5 bullets on what changes and where +
  a `Files:` line. A purely cosmetic session (renames, formatting) gets no entry.
- **STATUS.md**: manual sections only. If a block of work is closed, set "In
  progress" to `(no work in progress)` with 1-2 lines of summary and a candidate
  for the next block. Update "Blockers" and "Next steps". Do not touch the
  `AUTO:COMMITS` block (the hook regenerates it).
- **DEVLOG.md**: `grep` first; if the problem exists, update it instead of
  duplicating. Keep the index at the top current.
- A decision taken **and** implemented moves from
  [docs/05](../../../docs/05-decisions-open.md) to
  [docs/06](../../../docs/06-decisions-taken.md).

## 3. Verify before committing

```bash
bash .claude/scripts/verify.sh
```

If it is red, do not propose commits: fix first.

## 4. Propose the commits

Group by category - code / tests / docs / config - so unrelated work does not share
a commit. For the mechanical proposal:

```bash
python3 .claude/scripts/propose_commit.py
```

For each group write a Conventional Commits first line (**<= 72 characters**) and a
body with the **why**, citing `[closes DEVLOG X.Y]` or the work package where it
applies. **Show the proposed messages and ask for confirmation before committing.**

## 5. Commit

After confirmation: **selective staging** file by file (never `git add -A`, `--all`
or `.`), then commit. Never `--amend`. If a hook fails, fix the cause; never
`--no-verify`. These prohibitions are also `deny` rules in `.claude/settings.json`.

**Push, PRs and merges only on explicit request**, never on your own initiative.

## 6. Summary

Close with: what was done, what stays open, the resumption point (which must match
what you wrote in STATUS.md).
