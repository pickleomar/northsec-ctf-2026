from __future__ import annotations

from flask import Flask, jsonify, request, send_from_directory

from .architect import fetch_architect_lessons, save_architect_lesson
from .auth import require_auth
from .catalog import get_rank
from .config import load_settings
from .schema import ensure_runtime_schema
from .services import authenticate_user, buy_store_item, create_user, feed_inventory_item, fetch_user_bundle
from .validation import compute_loss, issue_challenge, read_fake_flag, sanitize_payload


def _error_response(error: Exception):
    # Services raise plain Python exceptions; the Flask layer is responsible
    # for turning them into the small JSON API used by the frontend.
    if isinstance(error, PermissionError):
        return jsonify({"error": str(error)}), 401
    if isinstance(error, ValueError):
        status = 409 if str(error) == "Username already taken" else 400
        return jsonify({"error": str(error)}), status
    raise error


def create_app() -> Flask:
    settings = load_settings()
    ensure_runtime_schema()
    app = Flask(__name__, static_folder=None)

    @app.post("/api/auth/register")
    def register():
        payload = request.get_json(silent=True) or {}
        username = str(payload.get("username", "")).strip()
        password = str(payload.get("password", ""))
        try:
            token, user = create_user(username, password)
        except Exception as error:
            return _error_response(error)
        return jsonify({"token": token, "user": user}), 201

    @app.post("/api/auth/login")
    def login():
        payload = request.get_json(silent=True) or {}
        username = str(payload.get("username", "")).strip()
        password = str(payload.get("password", ""))
        try:
            token, user = authenticate_user(username, password)
        except Exception as error:
            return _error_response(error)
        return jsonify({"token": token, "user": user})

    @app.get("/api/me")
    @require_auth
    def me():
        user = fetch_user_bundle(request.user_id)  # type: ignore[attr-defined]
        if user is None:
            return jsonify({"error": "Unauthorized"}), 401
        return jsonify(user)

    @app.post("/api/store/buy")
    @require_auth
    def buy_item():
        payload = request.get_json(silent=True) or {}
        item_id = payload.get("item_id")
        try:
            result = buy_store_item(request.user_id, item_id)  # type: ignore[attr-defined]
        except Exception as error:
            return _error_response(error)
        return jsonify(result)

    @app.post("/api/feed")
    @require_auth
    def feed():
        payload = request.get_json(silent=True) or {}
        item_id = payload.get("item_id")
        try:
            result = feed_inventory_item(request.user_id, item_id)  # type: ignore[attr-defined]
        except Exception as error:
            return _error_response(error)
        return jsonify(result)

    @app.get("/api/architect/lessons")
    @require_auth
    def architect_lessons():
        try:
            result = fetch_architect_lessons(request.user_id)  # type: ignore[attr-defined]
        except Exception as error:
            return _error_response(error)
        return jsonify(result)

    @app.post("/api/architect/lessons")
    @require_auth
    def architect_save_lesson():
        payload = request.get_json(silent=True) or {}
        try:
            result = save_architect_lesson(
                request.user_id,  # type: ignore[attr-defined]
                int(payload.get("npc_index")),
                str(payload.get("trigger", "")),
                str(payload.get("phrase", "")),
            )
        except Exception as error:
            return _error_response(error)
        return jsonify(result)

    @app.get("/api/challenge")
    def challenge():
        seed_raw = request.args.get("seed")
        if seed_raw is None:
            return jsonify({"message": "missing seed"}), 400

        try:
            seed = int(seed_raw)
        except Exception:
            return jsonify({"message": "bad seed"}), 400

        return jsonify(issue_challenge(seed))

    @app.post("/api/validate")
    def validate():
        cleaned = sanitize_payload(request.get_json(silent=True))
        if cleaned is None:
            return jsonify({"success": False, "score": 1.0, "message": "bad payload"}), 400

        loss = compute_loss(cleaned["positions"])
        if loss < 1800.0:
            return jsonify({"success": True, "score": loss, "flag": read_fake_flag()})
        return jsonify({"success": False, "score": loss})

    @app.get("/")
    def index():
        if not settings.static_dir.exists():
            return "dist/ not found. Build frontend first (npm run build).", 500
        return send_from_directory(settings.static_dir, "index.html")

    @app.get("/<path:path>")
    def static_proxy(path: str):
        target = settings.static_dir / path
        # This keeps direct /game and /store visits working as SPA routes while
        # still serving built assets directly from the same backend.
        if target.exists():
            return send_from_directory(settings.static_dir, path)
        return send_from_directory(settings.static_dir, "index.html")

    return app


app = create_app()


if __name__ == "__main__":
    settings = load_settings()
    app.run(host="127.0.0.1", port=settings.port, debug=False, threaded=True)
