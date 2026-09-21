---
paths:
  - "**/*.py"
---

# Python conventions

> Loaded only when Claude touches a `.py` file. The general principles live in
> [docs/02-engineering-conventions.md](../../docs/02-engineering-conventions.md);
> this file holds only what is specific to the language.

## Errors

- Raise the project's domain errors (`CvacError` and its subclasses in
  `src/cv_as_code/errors.py`), never a bare `Exception`.
- `except` is always specific. A broad `except Exception:` is allowed only at the
  outermost boundary of a process, and it must re-raise or report; never swallow.
- Expected outcomes (validation failed, resource absent) are results, not
  exceptions: the validator returns a `Report`, it does not raise per finding.

## Output

- The `cvac` command is a CLI: its output *is* the interface, so `print` is right
  there. Library modules return values and raise; they do not print.
- Every message is English. Never echo user data in a message beyond the ids and
  paths needed to locate a problem.

## Types and structure

- Annotations on every public function, parameters and return.
- `dataclass` instead of ad-hoc dicts and positional tuples for results
  (`ResolveResult`, `RenderResult`, `Report`).
- `from __future__ import annotations` at the top of every module.
- Soft caps as triggers, not limits: ~500 lines per module, ~60 per function.

## Paths

- Always `pathlib.Path`, never string concatenation with `/` or `\`.
- The data root is the only place user files are read from or written to; the
  package's own assets are looked up through `DataRoot` so that data-root
  overrides keep working.
- No machine-specific absolute paths in versioned files: they belong in
  `.claude/project.conf`, which is not versioned.

## Tests

- `test_*.py`, functions `test_*`. One assertion per concept, not per line.
- `pytest.raises(..., match=...)` to check *which* error, not just that there is one.
- `tmp_path` instead of real directories; no shared state between tests.
- Fixtures build invented data (see `tests/conftest.py`); never copy a real
  person's profile into a test.

## Do not

- Mutable default arguments; `import *`; `== None` / `== True`.
- Mid-file imports to break a cycle: extract the shared helper into a neutral
  module and import that from both sides.
