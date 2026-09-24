"""Stage runs started from the browser: one thread each, progress as summarised events."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from flask import Blueprint, render_template

from ..dataroot import DataRoot
from ..errors import CvacError
from ..runner import RunResult, find_claude, run_stage, summarise_event
from ..stages import resolve_stage
from . import views
from .state import state

bp = Blueprint("runs", __name__)


@dataclass
class Run:
    id: str
    stage: str
    params: dict[str, str]
    back_url: str
    started: datetime = field(default_factory=datetime.now)
    status: str = "running"
    lines: list[str] = field(default_factory=list)
    result: RunResult | None = None
    error: str | None = None
    thread: threading.Thread | None = None

    @property
    def summary(self) -> str:
        if self.status == "running":
            return "running"
        if self.error:
            return self.error
        r = self.result
        if r is None:
            return "no result"
        if r.ok:
            return f"ok: {r.output_rel} written and valid"
        parts = []
        if r.engine_error:
            parts.append(f"engine: {r.engine_error}")
        if not r.written:
            parts.append(f"{r.output_rel} was not written")
        parts += r.errors
        return "; ".join(parts) or "failed"


class RunManager:
    def __init__(self) -> None:
        self.runs: dict[str, Run] = {}
        self._lock = threading.Lock()

    def start(self, root: DataRoot, stage: str, params: dict[str, str], back_url: str) -> Run:
        rs = resolve_stage(root, stage, params)
        for _, path, optional in rs.inputs:
            if not path.is_file() and not optional:
                raise CvacError(f"stage {stage}: input {root.rel(path)} is missing")
        # Resolved here, in the request, so a missing engine is an immediate message and the
        # thread never looks the executable up under an environment that has moved on.
        binary = find_claude()
        run = Run(id=uuid.uuid4().hex[:10], stage=stage, params=rs.params, back_url=back_url)

        def work() -> None:
            try:
                run.result = run_stage(
                    root, rs, on_line=lambda line: self._collect(run, line), binary=binary
                )
                run.status = "ok" if run.result.ok else "failed"
            except CvacError as e:
                run.error = str(e)
                run.status = "failed"

        run.thread = threading.Thread(target=work, name=f"cvac-run-{run.id}", daemon=True)
        with self._lock:
            self.runs[run.id] = run
        run.thread.start()
        return run

    def _collect(self, run: Run, line: str) -> None:
        text = summarise_event(line)
        if text:
            run.lines.append(text)

    def get(self, run_id: str) -> Run:
        run = self.runs.get(run_id)
        if run is None:
            raise views.NotFound(f"no run `{run_id}`")
        return run

    def wait(self, run_id: str, timeout: float = 60) -> Run:
        run = self.get(run_id)
        if run.thread is not None:
            run.thread.join(timeout)
        return run

    def listing(self) -> list[Run]:
        return sorted(self.runs.values(), key=lambda r: r.started, reverse=True)


@bp.get("/runs")
def runs() -> str:
    return render_template("runs.html", runs=state().runs.listing())


@bp.get("/runs/<run_id>")
def run(run_id: str) -> str:
    return render_template("run.html", run=state().runs.get(run_id))
