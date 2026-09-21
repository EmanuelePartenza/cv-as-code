#!/usr/bin/env bash
# Verification engine: runs every deterministic gate declared in .claude/project.conf
# in one go and prints GREEN or RED.
#
#   bash .claude/scripts/verify.sh               # all gates
#   bash .claude/scripts/verify.sh --tests-only  # only the test suite
#   bash .claude/scripts/verify.sh --quick       # skip the tests (fast pre-commit)
#
# A gate that is not configured is skipped, not failed. Exit code: 0 green, 1 red.

set -u

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
CONF="$ROOT/.claude/project.conf"

cd "$ROOT" || exit 1

TESTS_ONLY=0
QUICK=0
for arg in "$@"; do
  case "$arg" in
    --tests-only) TESTS_ONLY=1 ;;
    --quick)      QUICK=1 ;;
    -h|--help)    sed -n '2,9p' "${BASH_SOURCE[0]}"; exit 0 ;;
  esac
done

if [ ! -f "$CONF" ]; then
  echo "verify: missing .claude/project.conf"
  echo "        copy .claude/project.conf.example and fill in the project's commands."
  exit 1
fi

# shellcheck disable=SC1090
. "$CONF"

FAILED=""
SKIPPED=""
EXCLUDED=""
PASSED=""

run_gate() {
  name="$1"
  cmd="$2"
  if [ -z "$cmd" ]; then
    SKIPPED="$SKIPPED $name"
    return 0
  fi
  printf '\n--- %s ---\n' "$name"
  if eval "$cmd"; then
    PASSED="$PASSED $name"
  else
    FAILED="$FAILED $name"
  fi
}

if [ "$TESTS_ONLY" -eq 1 ]; then
  run_gate "tests" "${CMD_TEST:-}"
else
  run_gate "format" "${CMD_FORMAT:-}"
  run_gate "lint"   "${CMD_LINT:-}"
  run_gate "types"  "${CMD_TYPES:-}"

  i=1
  while [ "$i" -le 3 ]; do
    eval "cmd=\${CMD_EXTRA_${i}:-}"
    eval "nm=\${CMD_EXTRA_${i}_NAME:-}"
    [ -z "$nm" ] && nm="extra-$i"
    [ -n "$cmd" ] && run_gate "$nm" "$cmd"
    i=$((i + 1))
  done

  # Documentation drift is advisory: it never turns the result red. Skipped with
  # --quick because the pre-commit hook already runs it on the staged files.
  if [ "$QUICK" -eq 0 ] \
     && command -v python3 >/dev/null 2>&1 \
     && [ -f "$ROOT/.claude/scripts/check_doc_drift.py" ]; then
    printf '\n--- documentation (advisory) ---\n'
    python3 "$ROOT/.claude/scripts/check_doc_drift.py" || true
  fi

  if [ "$QUICK" -eq 0 ]; then
    run_gate "tests" "${CMD_TEST:-}"
  else
    EXCLUDED="$EXCLUDED tests documentation"
  fi
fi

printf '\n========================================\n'
[ -n "$PASSED" ] && echo "passed:      $PASSED"
[ -n "$SKIPPED" ] && echo "not configured in project.conf: $SKIPPED"
[ -n "$EXCLUDED" ] && echo "excluded by --quick:$EXCLUDED"
if [ -n "$FAILED" ]; then
  echo "FAILED: $FAILED"
  echo "RESULT: RED"
  echo "Fix the code, do not bypass the gate."
  exit 1
fi
if [ -z "$PASSED" ]; then
  echo "RESULT: NO GATE CONFIGURED - fill in .claude/project.conf"
  exit 1
fi
echo "RESULT: GREEN"
exit 0
