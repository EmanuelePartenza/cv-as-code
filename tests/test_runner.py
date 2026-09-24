"""The stage runner: a fake `claude` executable stands in for the engine (ADR-0015)."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest
from conftest import JOB_ID, MATCH, write_job

from cv_as_code.cli import main
from cv_as_code.dataroot import DataRoot
from cv_as_code.errors import CvacError
from cv_as_code.runner import (
    ALLOWED_TOOLS,
    build_prompt,
    claude_command,
    find_claude,
    run_stage,
    summarise_event,
)
from cv_as_code.stages import resolve_stage

FAKE = '''#!/usr/bin/env python3
"""A stand-in for `claude -p`: echoes events, writes what FAKE_OUTPUT says, exits FAKE_EXIT."""
import json, os, re, sys
prompt = sys.stdin.read()
m = re.search(r"end with one\\nline: `DONE (.+?)`", prompt)
out = m.group(1) if m else None
print(json.dumps({"type": "system", "subtype": "init", "session_id": "s-1"}))
print(json.dumps({"type": "assistant", "message": {"content": [
    {"type": "text", "text": "Reading the inputs."},
    {"type": "tool_use", "name": "Write", "input": {"file_path": out}}]}}))
content = os.environ.get("FAKE_OUTPUT")
if content is not None and out:
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as h:
        h.write(open(content, encoding="utf-8").read())
is_error = os.environ.get("FAKE_IS_ERROR") == "1"
denials = []
if os.environ.get("FAKE_DENY"):
    denials = [{"tool_name": "Bash", "tool_input": {"command": "find / -name x"}}]
print(json.dumps({"type": "result", "subtype": "success", "is_error": is_error,
                  "result": "DONE " + str(out), "session_id": "s-1", "total_cost_usd": 0.0123,
                  "permission_denials": denials}))
sys.exit(int(os.environ.get("FAKE_EXIT", "0")))
'''


@pytest.fixture
def fake_claude(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    script = tmp_path / "fake-claude"
    script.write_text(FAKE, "utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("CVAC_CLAUDE_BIN", str(script))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.delenv("FAKE_OUTPUT", raising=False)
    monkeypatch.delenv("FAKE_EXIT", raising=False)
    monkeypatch.delenv("FAKE_IS_ERROR", raising=False)
    monkeypatch.delenv("FAKE_DENY", raising=False)
    return script


def match_file(tmp_path: Path, **overrides: object) -> Path:
    import yaml

    p = tmp_path / "match.yaml"
    p.write_text(yaml.safe_dump({**MATCH, **overrides}, sort_keys=False), "utf-8")
    return p


def test_find_claude_precedence_and_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_claude: Path
) -> None:
    assert find_claude() == fake_claude
    monkeypatch.setenv("CVAC_CLAUDE_BIN", str(tmp_path / "missing"))
    with pytest.raises(CvacError, match="is not a file"):
        find_claude()
    monkeypatch.delenv("CVAC_CLAUDE_BIN")
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    with pytest.raises(CvacError, match="install Claude Code"):
        find_claude()


def test_prompt_is_the_pack_plus_the_engine_note(data_root: DataRoot) -> None:
    write_job(data_root)
    rs = resolve_stage(data_root, "20_match", {"job_id": JOB_ID})
    prompt = build_prompt(data_root, rs)
    assert prompt.startswith("# Stage 20_match")
    assert "# Engine note" in prompt and f"DONE users/test/matches/{JOB_ID}.yaml" in prompt
    assert "Never set `status: approved`" in prompt


def test_command_confines_the_engine(data_root: DataRoot, tmp_path: Path) -> None:
    cmd = claude_command(tmp_path / "claude", data_root, 12, "sonnet", 1.5)
    assert cmd[1:4] == ["-p", "--output-format", "stream-json"]
    assert (
        "acceptEdits" in cmd
        and ALLOWED_TOOLS in cmd
        and "Bash(git:*),Bash(rm:*),WebFetch,WebSearch" in cmd
    )
    assert cmd[cmd.index("--max-turns") + 1] == "12"
    assert cmd[cmd.index("--add-dir") + 1] == str(data_root.path)
    assert cmd[cmd.index("--model") + 1] == "sonnet" and cmd[-1] == "1.50"
    assert "--dangerously-skip-permissions" not in cmd


def test_run_succeeds_when_the_output_is_written_and_valid(
    data_root: DataRoot, fake_claude: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_job(data_root)
    monkeypatch.setenv("FAKE_OUTPUT", str(match_file(tmp_path)))
    rs = resolve_stage(data_root, "20_match", {"job_id": JOB_ID})
    lines: list[str] = []
    result = run_stage(data_root, rs, on_line=lines.append)
    assert result.ok and result.written and result.errors == []
    assert result.session_id == "s-1" and result.cost_usd == pytest.approx(0.0123)
    assert result.output == data_root.path / "users" / "test" / "matches" / f"{JOB_ID}.yaml"
    assert result.log.is_file() and str(tmp_path / "cache") in str(result.log)
    events = [json.loads(line) for line in result.log.read_text("utf-8").splitlines()]
    assert events[0]["type"] == "cvac" and events[-1]["type"] == "result"
    assert any('"tool_use"' in line for line in lines)


def test_run_fails_when_the_output_does_not_validate(
    data_root: DataRoot, fake_claude: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_job(data_root)
    bad = match_file(tmp_path, strengths=[{"text": "x", "source_facts": ["exp-acme.f99"]}])
    monkeypatch.setenv("FAKE_OUTPUT", str(bad))
    result = run_stage(data_root, resolve_stage(data_root, "20_match", {"job_id": JOB_ID}))
    assert result.written and not result.ok
    assert any("cites unknown fact `exp-acme.f99`" in e for e in result.errors)


def test_run_reports_engine_errors_and_missing_output(
    data_root: DataRoot, fake_claude: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_job(data_root)
    rs = resolve_stage(data_root, "20_match", {"job_id": JOB_ID})
    result = run_stage(data_root, rs)
    assert not result.written and not result.ok and result.engine_error is None
    monkeypatch.setenv("FAKE_EXIT", "3")
    result = run_stage(data_root, rs)
    assert result.exit_code == 3 and result.engine_error == "engine exited with code 3"
    monkeypatch.setenv("FAKE_EXIT", "0")
    monkeypatch.setenv("FAKE_IS_ERROR", "1")
    result = run_stage(data_root, rs)
    assert result.engine_error and "DONE" in result.engine_error and not result.ok
    with pytest.raises(CvacError, match="unknown engine `gpt`"):
        run_stage(data_root, rs, engine="gpt")


def test_run_lists_the_tool_calls_the_engine_was_denied(
    data_root: DataRoot, fake_claude: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_job(data_root)
    monkeypatch.setenv("FAKE_OUTPUT", str(match_file(tmp_path)))
    monkeypatch.setenv("FAKE_DENY", "1")
    result = run_stage(data_root, resolve_stage(data_root, "20_match", {"job_id": JOB_ID}))
    assert result.ok and result.denied == ["Bash: find / -name x"]


def test_summarise_event_reads_assistant_and_result_lines() -> None:
    assistant = json.dumps(
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "text", "text": "Hello"},
                    {"type": "tool_use", "name": "Bash", "input": {"command": "cvac validate x"}},
                ]
            },
        }
    )
    assert summarise_event(assistant) == "Hello\n[Bash] cvac validate x"
    assert summarise_event(json.dumps({"type": "result", "total_cost_usd": 0.5})) == (
        "result: done (cost 0.5000 USD)"
    )
    assert summarise_event(json.dumps({"type": "result", "is_error": True})) == "result: error"
    denied = {"type": "result", "permission_denials": [{"tool_name": "Bash"}]}
    assert summarise_event(json.dumps(denied)) == "result: done (1 tool call(s) denied)"
    assert summarise_event(json.dumps({"type": "user"})) is None
    assert summarise_event("plain text") == "plain text"


def test_cli_stage_run_exit_codes(
    data_root: DataRoot,
    fake_claude: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_job(data_root)
    root = str(data_root.path)
    assert main(["stage", "run", "20_match", "--job", JOB_ID, "--data-root", root]) == 1
    out = capsys.readouterr().out
    assert "did not write" in out and "log:" in out
    monkeypatch.setenv("FAKE_OUTPUT", str(match_file(tmp_path)))
    assert main(["stage", "run", "20_match", "--job", JOB_ID, "--data-root", root]) == 0
    out = capsys.readouterr().out
    assert "ok: users/test/matches" in out and "[Write]" in out and "result: done" in out
    assert os.environ["CVAC_CLAUDE_BIN"] == str(fake_claude)
