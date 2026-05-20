"""
History routes.

GET    /api/history        → list recent analyses
DELETE /api/history        → clear history
"""

from flask import Blueprint, jsonify, request

from utils.history_store import clear_entries, list_entries

bp = Blueprint("history", __name__)


@bp.route("/history", methods=["GET"])
def get_history():
    try:
        limit = int(request.args.get("limit", 50))
    except ValueError:
        limit = 50
    entries = list_entries(limit=limit)
    return jsonify({"ok": True, "count": len(entries), "entries": entries})


@bp.route("/history", methods=["DELETE"])
def delete_history():
    n = clear_entries()
    return jsonify({"ok": True, "cleared": n})
