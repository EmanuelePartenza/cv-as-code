#!/usr/bin/env bash
# PostToolUse(Edit|Write|NotebookEdit) hook: appends a JSONL line to
# .claude/edit-log.jsonl with the file touched. /wrap reads this log to know
# exactly what changed during the session.
#
# Receives the hook's JSON payload on stdin. No python: it must be fast and work
# before the project's environment exists. Never fails: a broken hook must not
# hold a session hostage.

set -u

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
LOG="$ROOT/.claude/edit-log.jsonl"

PAYLOAD="$(cat 2>/dev/null || true)"

# Extract "file_path" and "tool_name" without depending on jq.
FILE="$(printf '%s' "$PAYLOAD" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
TOOL="$(printf '%s' "$PAYLOAD" | sed -n 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"

[ -z "$FILE" ] && exit 0
[ -z "$TOOL" ] && TOOL="Edit"

case "$FILE" in
  "$ROOT"/*) FILE="${FILE#"$ROOT"/}" ;;
esac

mkdir -p "$(dirname "$LOG")" 2>/dev/null || exit 0
printf '{"t":"%s","tool":"%s","file":"%s"}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$TOOL" "$FILE" >> "$LOG" 2>/dev/null

exit 0
