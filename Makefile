# Developer shortcuts. The gates that count are run by `make verify` (see .claude/scripts/verify.sh).
PY ?= .venv/bin/python

install:            ## editable install with dev tools into .venv
	uv venv .venv --allow-existing
	uv pip install --python $(PY) -e ".[dev]"

lint:               ## formatting and lint checks, no changes
	$(PY) -m ruff format --check .
	$(PY) -m ruff check .

format:             ## apply formatting and safe lint fixes
	$(PY) -m ruff format .
	$(PY) -m ruff check --fix .

test:               ## run the test suite
	$(PY) -m pytest

clean:              ## remove build products (rendered PDFs are kept)
	find . -name build -type d -path '*/users/*' -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache dist

.PHONY: install lint format test clean
