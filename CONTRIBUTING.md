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
make lint && make test
```

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
