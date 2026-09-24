"""Stage runs started from the browser: one thread each, progress as summarised events."""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from flask import Blueprint, render_template

from ..dataroot import DataRoot
from ..errors import CvacError
from ..runner import RunResult, find_claude, run_stage, summarise_event
from ..stages import load_stage, resolve_stage
from . import views
from .i18n import t
from .state import state

bp = Blueprint("runs", __name__)

StageStep = tuple[str, dict[str, str]]
CodeStep = tuple[str, str, Callable[[DataRoot], list[str]]]  # ("code", label, action)
Planner = Callable[[DataRoot], list["Step"]]
Step = StageStep | CodeStep | Planner


def label_of(steps: list[Step]) -> str:
    names = []
    for s in steps:
        if callable(s):
            continue
        names.append(s[1] if s[0] == "code" else s[0])
    return " → ".join(dict.fromkeys(names))


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
            return t("running")
        if self.error:
            return self.error
        r = self.result
        if r is None:
            return t("no result")
        if r.ok:
            return t("ok: {output} written and valid", output=r.output_rel)
        parts = []
        if r.engine_error:
            parts.append(t("engine: {error}", error=r.engine_error))
        if not r.written:
            parts.append(t("{output} was not written", output=r.output_rel))
        parts += r.errors
        return "; ".join(parts) or t("failed")


class RunManager:
    def __init__(self) -> None:
        self.runs: dict[str, Run] = {}
        self._lock = threading.Lock()

    def start(self, root: DataRoot, stage: str, params: dict[str, str], back_url: str) -> Run:
        return self.start_steps(root, [(stage, params)], back_url)

    def start_steps(self, root: DataRoot, steps: list[Step], back_url: str) -> Run:
        """One run of several steps in sequence: stages, code actions, or planners that add steps.

        A planner runs when reached and returns the steps to insert (what to extract is known
        only once the triage has written its index); a code action runs a library function.
        """
        first = steps[0]
        if not isinstance(first, tuple) or first[0] == "code":
            raise CvacError("a run starts with a stage")
        rs = resolve_stage(root, first[0], first[1])
        for template, path, optional in rs.inputs:
            if not rs.present(path, template) and not optional:
                raise CvacError(f"stage {first[0]}: input {root.rel(path)} is missing")
        needs_engine = any(
            isinstance(s, tuple)
            and s[0] != "code"
            and load_stage(s[0]).contract.get("engine") != "deterministic"
            for s in steps
        ) or any(callable(s) for s in steps)
        # Resolved here, in the request, so a missing engine is an immediate message and the
        # thread never looks the executable up under an environment that has moved on.
        binary = find_claude() if needs_engine else None
        run = Run(
            id=uuid.uuid4().hex[:10], stage=label_of(steps), params=rs.params, back_url=back_url
        )

        def work() -> None:
            queue: list[Step] = list(steps)
            order: list[Step] = list(steps)  # the steps in execution order, planners expanded
            ok = True
            try:
                while queue and ok:
                    step = queue.pop(0)
                    if callable(step):
                        added = step(root)
                        queue[0:0] = added
                        at = order.index(step)
                        order[at : at + 1] = added
                        run.stage = label_of(order)
                        continue
                    if step[0] == "code":
                        run.lines.append(f"── {step[1]}")
                        run.lines.extend(step[2](root))
                        continue
                    stage, params = step
                    resolved = resolve_stage(root, stage, params)
                    run.lines.append(f"── {stage}")
                    run.result = run_stage(
                        root, resolved, on_line=lambda line: self._collect(run, line), binary=binary
                    )
                    ok = run.result.ok
                run.status = "ok" if ok and run.result is not None else "failed"
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
