"""The questionnaire as a form: sections, questions and answers, saved back as the same markdown.

The file stays the contract (stage 05 writes it, stage 03 extracts it): questions are
`- A1. …` bullets, answers the `  > ` block-quote lines under them, positions and projects
repeat under `### …` headings. Parsing and rendering round-trip a file the stage wrote.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..dataroot import DataRoot, package_dir
from ..documents import parse_front_matter
from ..errors import CvacError
from ..validate import write_validated
from . import views
from .i18n import t
from .state import current_root

bp = Blueprint("questionnaire", __name__)

QUESTION_RE = re.compile(r"^- ([A-H]\d+)\. (.*)$")
ANSWER_RE = re.compile(r"^  >(?: ?(.*))?$")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
REPEATABLE = {"C": "Position", "D": "Project"}


@dataclass
class Item:
    code: str | None  # None for a free line kept verbatim
    text: str
    answer: str = ""


@dataclass
class Block:
    title: str | None
    items: list[Item] = field(default_factory=list)

    @property
    def questions(self) -> list[Item]:
        return [i for i in self.items if i.code]


@dataclass
class Section:
    heading: str
    blocks: list[Block] = field(default_factory=list)

    @property
    def letter(self) -> str:
        m = re.match(r"^([A-H])\b", self.heading)
        return m.group(1) if m else ""


@dataclass
class Questionnaire:
    front: dict
    intro: list[str]
    sections: list[Section]

    @property
    def status(self) -> str:
        return str(self.front.get("status") or "to-fill")

    @property
    def answered(self) -> tuple[int, int]:
        qs = [i for s in self.sections for b in s.blocks for i in b.questions]
        return sum(1 for q in qs if q.answer.strip()), len(qs)


def parse(text: str, where: str) -> Questionnaire:
    front, body = parse_front_matter(text, where)
    sections: list[Section] = []
    intro: list[str] = []
    section: Section | None = None
    block: Block | None = None
    for line in body.splitlines():
        if line.startswith("## "):
            section = Section(line[3:].strip())
            block = Block(None)
            section.blocks.append(block)
            sections.append(section)
            continue
        if section is None:
            intro.append(line)
            continue
        assert block is not None
        if line.startswith("### "):
            block = Block(line[4:].strip())
            section.blocks.append(block)
            continue
        m = QUESTION_RE.match(line)
        if m:
            block.items.append(Item(m.group(1), m.group(2)))
            continue
        a = ANSWER_RE.match(line)
        if a and block.items and block.items[-1].code:
            item = block.items[-1]
            item.answer = (
                (item.answer + "\n" + (a.group(1) or "")).strip("\n")
                if item.answer or a.group(1)
                else item.answer
            )
            continue
        block.items.append(Item(None, line))
    return Questionnaire(front, intro, sections)


def render_body(q: Questionnaire) -> str:
    out = list(q.intro)
    for section in q.sections:
        out.append(f"## {section.heading}")
        for block in section.blocks:
            if block.title is not None:
                out.append(f"### {block.title}")
            for item in block.items:
                if item.code is None:
                    out.append(item.text)
                    continue
                out.append(f"- {item.code}. {item.text}")
                for line in item.answer.splitlines():
                    out.append(f"  > {line}" if line else "  >")
    return "\n".join(out).rstrip("\n") + "\n"


def render(q: Questionnaire, front_text: str) -> str:
    """The file: the frontmatter text as it was (statuses edited textually), then the body."""
    return front_text + render_body(q)


def split_front(text: str) -> str:
    """The frontmatter with the blank lines that follow it, so a render reproduces the file."""
    end = text.index("\n---\n", 4) + len("\n---\n")
    while end < len(text) and text[end] == "\n":
        end += 1
    return text[:end]


def set_status(front_text: str, status: str) -> str:
    return re.sub(r"^status:\s*\S+", f"status: {status}", front_text, count=1, flags=re.M)


def skeleton_text(user: str, language: str) -> str:
    """The shipped English skeleton instantiated for a user, for a start without an engine."""
    text = (package_dir() / "pipeline" / "05_interview" / "questionnaire.skeleton.md").read_text(
        "utf-8"
    )
    text = text.replace("user: <slug>", f"user: {user}", 1)
    text = text.replace("language: <pivot language, ISO 639-1>", f"language: {language}", 1)
    return text.replace("created: <YYYY-MM-DD>", f"created: {date.today().isoformat()}", 1)


def add_block(q: Questionnaire, letter: str) -> None:
    """Another position (C) or project (D): the first question set, blank, under a new heading."""
    section = next((s for s in q.sections if s.letter == letter), None)
    if section is None or letter not in REPEATABLE:
        raise CvacError(f"section {letter} is not repeatable")
    template = next((b for b in section.blocks if b.questions), None)
    if template is None:
        raise CvacError(f"section {letter} has no questions to repeat")
    n = sum(1 for b in section.blocks if b.questions) + 1
    section.blocks.append(
        Block(f"{REPEATABLE[letter]} {n}", [Item(i.code, i.text) for i in template.questions])
    )


def _path(root: DataRoot, user: str, name: str) -> Path:
    udir = views.user_dir_of(root, user)
    if not NAME_RE.match(name):
        raise views.NotFound(f"no questionnaire `{name}`")
    return udir / "interviews" / f"{name}.md"


@bp.route("/u/<user>/questionnaire/<name>", methods=["GET", "POST"])
def form(user: str, name: str):
    root = current_root()
    path = _path(root, user, name)
    if not path.is_file():
        raise views.NotFound(f"no questionnaire `{name}`")
    text = path.read_text("utf-8")
    q = parse(text, root.rel(path))
    if request.method == "POST":
        front = split_front(text)
        for section in q.sections:
            for bi, block in enumerate(section.blocks):
                for item in block.questions:
                    key = f"a:{section.letter}:{bi}:{item.code}"
                    if key in request.form:
                        item.answer = request.form[key].replace("\r\n", "\n").strip("\n")
        action = request.form.get("action", "save")
        if action.startswith("add:"):
            try:
                add_block(q, action[4:])
            except CvacError as e:
                flash(str(e), "error")
        elif action in ("filled", "to-fill"):
            front = set_status(front, action)
        rep = write_validated(root, path, render(q, front))
        if rep.errors:
            for e in rep.errors:
                flash(e, "error")
        else:
            flash(
                t(
                    "saved: {answered} of {total} questions answered",
                    answered=q.answered[0],
                    total=q.answered[1],
                ),
                "ok",
            )
        return redirect(url_for("questionnaire.form", user=user, name=name))
    return render_template("questionnaire.html", user=user, name=name, q=q, repeatable=REPEATABLE)


@bp.post("/u/<user>/questionnaire/new")
def new(user: str):
    root = current_root()
    udir = views.user_dir_of(root, user)
    name = request.form.get("name", "").strip()
    if not NAME_RE.match(name):
        flash(
            t(
                "`{name}` is not a questionnaire name (lowercase letters, digits and dashes)",
                name=name,
            ),
            "error",
        )
        return redirect(url_for("data.documents", user=user))
    path = udir / "interviews" / f"{name}.md"
    if path.exists():
        flash(t("interviews/{name}.md already exists", name=name), "error")
        return redirect(url_for("data.documents", user=user))
    language = request.form.get("language") or "en"
    path.parent.mkdir(parents=True, exist_ok=True)
    rep = write_validated(root, path, skeleton_text(user, language))
    if rep.errors:
        for e in rep.errors:
            flash(e, "error")
        return redirect(url_for("data.documents", user=user))
    flash(t("questionnaire {name} created from the standard skeleton", name=name), "ok")
    return redirect(url_for("questionnaire.form", user=user, name=name))
