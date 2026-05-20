"""
Deeptection — Flask application entry point.

Run locally:
    cd backend
    python app.py

Or via gunicorn (HuggingFace Spaces / production):
    gunicorn -w 1 -k gthread -t 180 -b 0.0.0.0:7860 app:app
"""

import logging
import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

import config
from routes.analyze import bp as analyze_bp
from routes.history import bp as history_bp
from routes.health import bp as health_bp
from models.model_loader import warm_up_models


# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("deeptection")


# ---------------- Flask ----------------
def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

    CORS(
        app,
        resources={r"/api/*": {"origins": config.CORS_ORIGINS}},
        supports_credentials=False,
    )

    # ---- Routes ----
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(analyze_bp, url_prefix="/api")
    app.register_blueprint(history_bp, url_prefix="/api")

    # ---- Error handlers ----
    @app.errorhandler(413)
    def too_large(_):
        return jsonify({
            "ok": False,
            "error": "file_too_large",
            "message": (
                f"File exceeds the maximum allowed size "
                f"({config.MAX_VIDEO_SIZE_MB} MB for video, "
                f"{config.MAX_AUDIO_SIZE_MB} MB for audio)."
            ),
        }), 413

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"ok": False, "error": "not_found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        log.exception("Unhandled server error: %s", e)
        return jsonify({"ok": False, "error": "internal_error",
                        "message": "Something went wrong on our side."}), 500

    # ---- Root ----
    @app.route("/")
    def root():
        # If we were built with a bundled frontend (Docker / HF Spaces),
        # serve the SPA index.html. Otherwise return JSON metadata.
        if _should_serve_static():
            return send_from_directory(_frontend_dir(), "index.html")
        return jsonify({
            "service": "Deeptection API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": [
                "GET  /api/health",
                "POST /api/analyze",
                "GET  /api/history",
                "DELETE /api/history",
            ],
        })

    # ---- SPA fallback — any non-API path falls through to index.html
    #       so React-Router URLs reload cleanly.
    if _should_serve_static():
        @app.route("/<path:path>")
        def spa(path: str):
            static_path = _frontend_dir() / path
            if static_path.is_file():
                return send_from_directory(_frontend_dir(), path)
            return send_from_directory(_frontend_dir(), "index.html")

    return app


def _frontend_dir() -> Path:
    """Location of the built React app (frontend/dist) when deployed."""
    candidates = [
        Path(__file__).resolve().parent.parent / "frontend" / "dist",
        Path("/app/frontend/dist"),
    ]
    for c in candidates:
        if (c / "index.html").exists():
            return c
    return candidates[0]


def _should_serve_static() -> bool:
    if os.getenv("DEEPTECTION_SERVE_STATIC", "0") != "1":
        return False
    return (_frontend_dir() / "index.html").exists()


app = create_app()


if __name__ == "__main__":
    # Pre-load models once at startup so the first request isn't slow.
    try:
        warm_up_models()
    except Exception as exc:    # noqa: BLE001
        log.warning("Model warm-up skipped: %s", exc)

    port = int(os.getenv("PORT", "5000"))
    # threaded=True so multiple requests can share a single worker.
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
