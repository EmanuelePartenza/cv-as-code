"""Run a stage with an engine; the first engine is Claude Code in print mode (ADR-0015).

The prompt is the same bundle `cvac stage pack` writes, plus an engine note. The engine
runs as a subprocess inside the data root with an allow-list of tools; its event stream
is logged under the user's cache directory. A run succeeds only if the output file
exists afterwards and validates: the validator's verdict is the run's verdict.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .dataroot import DataRoot
from .errors import CvacError
from .stages import ResolvedStage, pack
from .validate import validate_files

CLAUDE_BIN_ENV = "CVAC_CLAUDE_BIN"
ENGINES = ("claude-code",)
ALLOWED_TOOLS = (
    "Read,Glob,Grep,LS,Write,Edit,MultiEdit,"
    "Bash(cvac validate:*),Bash(cvac stage:*),Bash(cvac profile:*)"
)
DISALLOWED_TOOLS = "Bash(git:*),Bash(rm:*),WebFetch,WebSearch"
ENGINE_NOTE = """

---

# Engine note

You are running non-interactively inside the data root `{root}`, which is your
working directory. The inputs above are also on disk; read more of the data root
with your tools if the instructions need it. Write the output to `{output}` with
your file tools, then run `cvac validate {output}` and fix the document until it
passes. Do not modify any other file. Never set `status: approved` or a fact to
`verified`: those are the person's acts. When the output validates, end with one
line: `DONE {output}`.
"""


@dataclass
class RunResult:
    stage: str
    output: Path
    output_rel: str
    log: Path
    exit_code: int
    written: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    session_id: str | None = None
    cost_usd: float | None = None
    engine_error: str | None = None

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and self.written and not self.errors and not self.engine_error


def cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "cvac"


def find_claude() -> Path:
    """CVAC_CLAUDE_BIN, then `claude` on PATH, then the VS Code extension's bundled binary."""
    explicit = os.environ.get(CLAUDE_BIN_ENV)
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise CvacError(f"{CLAUDE_BIN_ENV}={explicit} is not a file")
        return path
    on_path = shutil.which("claude")
    if on_path:
        return Path(on_path)
    bundled = sorted(
        Path.home().glob(
            ".vscode*/extensions/anthropic.claude-code-*/resources/native-binary/claude"
        )
    )
    if bundled:
        return bundled[-1]
    raise CvacError(
        "the `claude` executable was not found: install Claude Code "
        "(https://code.claude.com/docs/en/setup) or set "
        f"{CLAUDE_BIN_ENV}=/path/to/claude"
    )


def build_prompt(root: DataRoot, rs: ResolvedStage) -> str:
    return pack(root, rs) + ENGINE_NOTE.format(root=root.path, output=rs.output_rel)


def claude_command(
    binary: Path, root: DataRoot, max_turns: int, model: str | None, budget_usd: float | None
) -> list[str]:
    cmd = [
        str(binary),
        "-p",
        "--output-format",
        "stream-json",
        "--verbose",
        "--permission-mode",
        "acceptEdits",
        "--allowedTools",
        ALLOWED_TOOLS,
        "--disallowedTools",
        DISALLOWED_TOOLS,
        "--max-turns",
        str(max_turns),
        "--add-dir",
        str(root.path),
    ]
    if model:
        cmd += ["--model", model]
    if budget_usd is not None:
        cmd += ["--max-budget-usd", f"{budget_usd:.2f}"]
    return cmd


def summarise_event(line: str) -> str | None:
    """One readable line for a stream-json event, or None for noise."""
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return line.strip() or None
    kind = event.get("type")
    if kind == "assistant":
        parts = []
        for block in (event.get("message") or {}).get("content") or []:
            if block.get("type") == "text" and block.get("text", "").strip():
                parts.append(block["text"].strip())
            elif block.get("type") == "tool_use":
                inp = block.get("input") or {}
                target = inp.get("file_path") or inp.get("command") or inp.get("pattern") or ""
                parts.append(f"[{block.get('name')}] {target}".rstrip())
        return "\n".join(parts) or None
    if kind == "result":
        cost = event.get("total_cost_usd")
        tail = f" (cost {cost:.4f} USD)" if isinstance(cost, int | float) else ""
        state = "error" if event.get("is_error") else "done"
        return f"result: {state}{tail}"
    return None


def _log_path(stage: str) -> Path:
    runs = cache_dir() / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    return runs / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{stage}.jsonl"


def run_stage(
    root: DataRoot,
    rs: ResolvedStage,
    engine: str = "claude-code",
    max_turns: int = 40,
    model: str | None = None,
    budget_usd: float | None = None,
    timeout: float = 1800,
    on_line: Callable[[str], None] | None = None,
    log_path: Path | None = None,
) -> RunResult:
    """Run one resolved stage to completion; the log holds every engine event."""
    if engine not in ENGINES:
        raise CvacError(f"unknown engine `{engine}` (known: {', '.join(ENGINES)})")
    binary = find_claude()
    prompt = build_prompt(root, rs)
    log = log_path or _log_path(rs.stage.name)
    assert rs.output is not None
    cmd = claude_command(binary, root, max_turns, model, budget_usd)
    session_id: str | None = None
    cost: float | None = None
    engine_error: str | None = None
    with log.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"type": "cvac", "stage": rs.stage.name, "cmd": cmd}) + "\n")
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=root.path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
            )
        except OSError as e:
            raise CvacError(f"cannot start {binary}: {e}") from e
        assert proc.stdin is not None and proc.stdout is not None
        try:
            proc.stdin.write(prompt)
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass
        try:
            for line in proc.stdout:
                handle.write(line if line.endswith("\n") else line + "\n")
                handle.flush()
                if on_line:
                    on_line(line.rstrip("\n"))
                event = _event(line)
                if event.get("type") == "result":
                    session_id = event.get("session_id") or session_id
                    if isinstance(event.get("total_cost_usd"), int | float):
                        cost = float(event["total_cost_usd"])
                    if event.get("is_error"):
                        engine_error = str(event.get("result") or event.get("subtype") or "error")
            exit_code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            exit_code = proc.wait()
            engine_error = f"timed out after {timeout:.0f}s"
    written = rs.output.is_file()
    rep = validate_files(root, [rs.output]) if written else None
    result = RunResult(
        stage=rs.stage.name,
        output=rs.output,
        output_rel=rs.output_rel,
        log=log,
        exit_code=exit_code,
        written=written,
        errors=list(rep.errors) if rep else [],
        warnings=list(rep.warnings) if rep else [],
        session_id=session_id,
        cost_usd=cost,
        engine_error=engine_error,
    )
    if exit_code != 0 and not engine_error:
        result.engine_error = f"engine exited with code {exit_code}"
    return result


def _event(line: str) -> dict[str, Any]:
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return {}
    return obj if isinstance(obj, dict) else {}
