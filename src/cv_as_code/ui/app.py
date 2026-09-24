"""The Flask application: every route is a thin handler over the library (ADR-0014).

Local by design: bound to the loopback interface, one user, no authentication. The
gate handlers (verify, reject, approve) run only on a POST from a button and call the
same functions the CLI calls, with the same refusals. The UI never commits to git.
"""

from __future__ import annotations

import secrets
import threading
import webbrowser
from collections.abc import Callable
from urllib.parse import urlsplit

from flask import (
    Flask,
    Response,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from ..dataroot import DataRoot
from ..errors import CvacError
from ..facts import set_status
from ..letter import render_letter
from ..render import render
from ..report import evidence_quote, profile_data
from ..resolve import resolve
from ..specs import approve
from ..validate import discover_all, validate_files
from . import curriculum, data, jobs, questionnaire, review, runs, start, views
from .i18n import LANGUAGES, negotiate, t
from .runs import RunManager
from .state import (
    UiState,
    browse,
    current_root,
    new_folder,
    recent_roots,
    save_language,
    saved_language,
    state,
)

FACT_ACTIONS = {"verify": "verified", "reject": "rejected"}
MODES = ("draft", "final")
OPEN_ENDPOINTS = {"open_root", "static"}


def _flash_outcome(action: Callable[[], str]) -> None:
    """Run a gate or render action and report it as a flash, never as a traceback."""
    try:
        flash(action(), "ok")
    except CvacError as e:
        flash(str(e), "error")


def _mode() -> str:
    mode = request.form.get("mode", "draft")
    if mode not in MODES:
        raise views.NotFound(f"no mode `{mode}`")
    return mode


def _render_message(out_name: str, pages: int, warnings: list[str]) -> str:
    for w in warnings:
        flash(w, "warn")
    return t("rendered {name}: {pages} page(s)", name=out_name, pages=pages)


def _register_pages(app: Flask) -> None:
    @app.route("/open", methods=["GET", "POST"])
    def open_root():
        if request.method == "POST":
            action = request.form.get("action", "open")
            where = request.form.get("dir") or request.form.get("path") or ""
            try:
                if action == "new-folder":
                    target = new_folder(where, request.form.get("name", ""))
                    root = state().open(str(target), create=True)
                else:
                    create = action == "create" or request.form.get("create") == "on"
                    root = state().open(request.form.get("path", ""), create)
            except CvacError as e:
                flash(str(e), "error")
                return redirect(url_for("open_root", dir=where or None))
            flash(t("data root: {path}", path=root.path), "ok")
            return redirect(url_for("index"))
        try:
            listing = browse(request.args.get("dir"))
        except CvacError as e:
            flash(str(e), "error")
            listing = browse(None)
        return render_template("open.html", recent=recent_roots(), listing=listing)

    @app.post("/language")
    def language() -> Response:
        lang = request.form.get("lang", "")
        if lang in LANGUAGES:
            save_language(lang)
        back = request.form.get("next") or url_for("index")
        safe = back.startswith("/") and not back.startswith("//")
        return redirect(back if safe else url_for("index"))

    @app.get("/")
    def index() -> str:
        root = current_root()
        return render_template("index.html", users=views.users(root), git=views.git_status(root))

    @app.get("/validate")
    def validate() -> str:
        root = current_root()
        files = discover_all(root)
        rep = validate_files(root, files)
        return render_template(
            "validate.html", count=len(files), errors=rep.errors, warnings=rep.warnings
        )

    @app.get("/u/<user>")
    def profile(user: str) -> str:
        root = current_root()
        user_dir = views.user_dir_of(root, user)
        pdata = profile_data(root, user)
        for entry in pdata["entries"]:
            for fact in entry["facts"]:
                for ev in fact["evidence"]:
                    ev["quote"] = evidence_quote(user_dir, ev["ref"]) if ev["exists"] else None
        return render_template("profile.html", p=pdata)

    @app.get("/u/<user>/cvs")
    def cvs(user: str) -> str:
        return render_template("cvs.html", user=user, specs=views.specs(current_root(), user))

    @app.get("/u/<user>/<kind>/<name>")
    def spec(user: str, kind: str, name: str) -> str:
        return render_template("spec.html", s=views.spec_detail(current_root(), user, kind, name))

    @app.get("/u/<user>/<kind>/<name>/pdf/<which>")
    def pdf(user: str, kind: str, name: str, which: str) -> Response:
        s = views.spec_detail(current_root(), user, kind, name)
        letter, _, variant = which.rpartition("-") if "-" in which else ("", "", which)
        pdfs = (s["letter"] or {}).get("pdf", {}) if letter == "letter" else s["pdf"]
        path = pdfs.get(variant)
        if path is None:
            raise views.NotFound(f"no {which} PDF for {kind} `{name}`")
        return send_file(path, mimetype="application/pdf", as_attachment=False, max_age=0)


def _register_gates(app: Flask) -> None:
    """POST handlers: the person's acts, each bound to one button."""

    def back_to_spec(user: str, kind: str, name: str) -> Response:
        return redirect(url_for("spec", user=user, kind=kind, name=name))

    @app.post("/u/<user>/fact/<fact_id>/<action>")
    def fact_action(user: str, fact_id: str, action: str) -> Response:
        root = current_root()
        views.user_dir_of(root, user)
        if action not in FACT_ACTIONS:
            raise views.NotFound(f"no action `{action}`")

        def act() -> str:
            c = set_status(root, user, [fact_id], FACT_ACTIONS[action])[0]
            return f"{c.fact_id}: {c.old_status} → {c.new_status}"

        _flash_outcome(act)
        return redirect(url_for("profile", user=user) + f"#{fact_id}")

    @app.post("/u/<user>/<kind>/<name>/render")
    def render_spec(user: str, kind: str, name: str) -> Response:
        root = current_root()
        d = views.spec_dir_of(root, user, kind, name)
        mode = _mode()

        def act() -> str:
            resolve(root, d, mode)
            r = render(root, d)
            return _render_message(r.out_path.name, r.pages, r.warnings)

        _flash_outcome(act)
        return back_to_spec(user, kind, name)

    @app.post("/u/<user>/<kind>/<name>/approve")
    def approve_spec(user: str, kind: str, name: str) -> Response:
        root = current_root()
        d = views.spec_dir_of(root, user, kind, name)
        _flash_outcome(
            lambda: t(
                "approved on {date}; render the final when ready",
                date=approve(root, d / "cv-spec.yaml"),
            )
        )
        return back_to_spec(user, kind, name)

    @app.post("/u/<user>/<kind>/<name>/letter/render")
    def render_letter_of(user: str, kind: str, name: str) -> Response:
        root = current_root()
        d = views.spec_dir_of(root, user, kind, name)
        mode = _mode()

        def act() -> str:
            r = render_letter(root, d, mode)
            return _render_message(r.out_path.name, r.pages, r.warnings)

        _flash_outcome(act)
        return back_to_spec(user, kind, name)

    @app.post("/u/<user>/<kind>/<name>/letter/approve")
    def approve_letter_of(user: str, kind: str, name: str) -> Response:
        root = current_root()
        d = views.spec_dir_of(root, user, kind, name)
        _flash_outcome(
            lambda: t(
                "letter approved on {date}; render the final when ready",
                date=approve(root, d / "letter.md"),
            ),
        )
        return back_to_spec(user, kind, name)


def create_app(root: DataRoot | None = None) -> Flask:
    """The application on a data root, or on none: then every page leads to the chooser."""
    app = Flask(__name__)
    # Flashes are the only session content; a fresh key per process is right for a local tool.
    app.config["SECRET_KEY"] = secrets.token_hex(16)
    app.extensions["cvac"] = UiState(root, RunManager())

    @app.before_request
    def _same_origin_posts() -> None:
        # No authentication on a loopback server means any web page open in the same
        # browser could POST here; browsers send Origin (or Referer) on such posts, so a
        # gate request from elsewhere is refused. A client sending neither (curl) is local.
        if request.method != "POST":
            return
        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if origin and urlsplit(origin).netloc != request.host:
            abort(403)

    @app.before_request
    def _need_a_root():
        if state().root is None and request.endpoint not in OPEN_ENDPOINTS:
            return redirect(url_for("open_root"))
        return None

    @app.before_request
    def _language() -> None:
        g.lang = negotiate(saved_language())

    @app.context_processor
    def _globals() -> dict[str, object]:
        root = state().root
        return {
            "root_path": str(root.path) if root else None,
            "default_user": root.default_user if root else None,
            "t": t,
            "languages": LANGUAGES,
            "lang": g.lang,
        }

    @app.errorhandler(views.NotFound)
    def _not_found(e: views.NotFound) -> tuple[str, int]:
        return render_template("error.html", title=t("Not found"), message=str(e)), 404

    @app.errorhandler(CvacError)
    def _cvac_error(e: CvacError) -> tuple[str, int]:
        return render_template("error.html", title=t("Error"), message=str(e)), 400

    _register_pages(app)
    _register_gates(app)
    app.register_blueprint(runs.bp)
    app.register_blueprint(jobs.bp)
    app.register_blueprint(data.bp)
    app.register_blueprint(questionnaire.bp)
    app.register_blueprint(review.bp)
    app.register_blueprint(start.bp)
    app.register_blueprint(curriculum.bp)
    return app


def serve(
    root: DataRoot | None, host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True
) -> None:
    """Run the UI until interrupted; the browser opens once the server is up."""
    app = create_app(root)
    url = f"http://{host}:{port}/"
    if open_browser:
        threading.Timer(0.8, webbrowser.open, args=(url,)).start()
    where = f"data root: {root.path}" if root else "no data root yet: the browser asks for one"
    print(f"cvac ui at {url}  ({where}) - Ctrl-C to stop")
    app.run(host=host, port=port, debug=False, use_reloader=False)
