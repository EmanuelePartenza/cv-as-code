# cv-as-code

Fact-grounded CV generation: verified career facts, an LLM-drafted content spec whose every line cites its source facts, a human approval gate, and a deterministic Python + Typst tail that turns the approved spec into a PDF.

**Status: pre-release (v0.1.0 in progress).** This README is a stub; the full one lands with the first release. What exists today: the `cvac` command (`init`, `validate`, `resolve`, `render`, `cv`, `letter`), the data schemas, the `classic` Typst template with vendored fonts, and the publication-boundary test.

## Install

```bash
uv tool install git+https://github.com/EmanuelePartenza/cv-as-code    # or: pipx install git+…
```

No external binary is needed: the Typst compiler comes from PyPI.

## Use

```bash
cvac init ~/my-cv            # a data root: cvac.yaml, users/, jobs/
cd ~/my-cv && cvac validate --all
cvac cv users/<slug>/masters/<name> --mode draft     # DRAFT-watermarked preview
cvac cv users/<slug>/masters/<name> --mode final     # only an approved spec citing verified facts
```

## Licence

MIT. Fonts: Lato, SIL Open Font License 1.1 (see `src/cv_as_code/templates/fonts/OFL.txt`).
