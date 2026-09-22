# Contributing

## What never enters this repository

This is a tool, not anyone's job search. The maintainer's own data lives in a
private data root elsewhere, and the boundary is enforced by
`tests/test_publication_boundary.py` on every commit (pre-commit hook) and in
CI, not by good intentions:

- no `users/` directory outside `example/`, and only the allow-listed example
  persona inside it;
- no PDF, DOCX or other office documents, anywhere (rendered examples are CI
  artefacts);
- no `interviews/`, `sources/` or `inbox/` directories outside `example/`;
- no e-mail address outside the `example.com/org/net` domains, no phone-shaped
  or date-of-birth-shaped string outside the example's reserved fake values;
- nothing from the maintainer's private denylist (contact details, employer,
  clients, project code names), matched through keyed HMAC digests in
  `tests/data/denylist.hmac` so the list itself is never published.

Examples describe the example persona's world, never a real person's. Do not
paraphrase a real profile into documentation or tests.

## Development setup

```bash
git clone https://github.com/EmanuelePartenza/cv-as-code && cd cv-as-code
make install                          # .venv with the package and dev tools
git config core.hooksPath .githooks   # publication boundary and commit checks
cp .claude/project.conf.example .claude/project.conf
make lint && make test                # or: bash .claude/scripts/verify.sh
```

The working method (interview before implementing, tests for every new part,
ADRs for non-obvious decisions, Conventional Commits) is in
[CLAUDE.md](CLAUDE.md) and [docs/03-development-process.md](docs/03-development-process.md).

## Adding a language

One YAML file: `i18n/labels.<lang>.yaml`, with `kind: labels` and every key of
[`labels.schema.json`](src/cv_as_code/schemas/labels.schema.json) — section
headings, `present`, `date_format`, the twelve month names, language names,
level names. Put it in your data root's `i18n/` to use it now, or in
`src/cv_as_code/i18n/` to contribute it. `cvac validate --all` tells you what
is missing; a spec in that language then renders with no code change.

## Adding a template

A directory exporting `cv(data)` in `template.typ` (and `letter(data)` in
`letter.typ` for cover letters). `data` is the resolved JSON whose shape is
[`cv-resolved.schema.json`](src/cv_as_code/schemas/cv-resolved.schema.json):
final display text, no ids, no refs, labels already resolved — a template
carries **zero language strings**. Shared primitives live in `templates/lib/`.
Put the directory in your data root's `templates/` to use it now
(`template: <name>` in a spec), or in `src/cv_as_code/templates/` to contribute
it. System fonts are ignored at render time: a template that needs another
font ships it.

## Adding a stage

A directory under `src/cv_as_code/pipeline/`: `INSTRUCTIONS.md` (the prompt —
inputs, outputs, rules; it never names an engine, never sets `approved`) and
`io.yaml` validated by [`stage-io.schema.json`](src/cv_as_code/schemas/stage-io.schema.json).
If it writes a new kind, add the schema and its validator checks with tests
that watch each rule fail. `tests/test_stages.py` picks the stage up; make it
work on the example user before claiming it in the docs.

## The denylist (maintainers)

The plain-text list and its key live outside any repository, in
`~/.config/cvac/denylist.txt` and `~/.config/cvac/denylist.key`; CI holds the
key as the `CVAC_DENYLIST_KEY` secret. Forks without the key skip that check
and still run the structural rules.

```bash
scripts/denylist.py seed --profile <path/to/profile.yaml> --add "Some Client"
scripts/denylist.py build          # refresh tests/data/denylist.hmac, commit it
scripts/denylist.py check          # every tracked text file
scripts/denylist.py check-history  # the whole history, before a repository goes public
```
