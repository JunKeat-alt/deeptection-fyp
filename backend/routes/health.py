"""
Health / status route.
Reports the active model-source policy and which backend is serving each modality.
"""

from flask import Blueprint, jsonify

import config
from models.model_loader import get_video_model, get_audio_model

bp = Blueprint("health", __name__)


@bp.route("/health", methods=["GET"])
def health():
    try:
        v = get_video_model()
        a = get_audio_model()
        ready = True
        models_info = {
            "video": {"name": v.name, "kind": v.kind, "trained": v.meta.get("trained")},
            "audio": {"name": a.name, "kind": a.kind, "trained": a.meta.get("trained")},
        }
    except Exception as exc:  # noqa: BLE001
        ready = False
        models_info = {"error": str(exc)}

    return jsonify({
        "ok": True,
        "ready": ready,
        "service": "Deeptection",
        "model_source": config.MODEL_SOURCE,
        "checkpoints": {
            "video": {
                "path": str(config.VIDEO_CHECKPOINT_PATH),
                "exists": config.VIDEO_CHECKPOINT_PATH.is_file(),
            },
            "audio": {
                "path": str(config.AUDIO_CHECKPOINT_PATH),
                "exists": config.AUDIO_CHECKPOINT_PATH.is_file(),
            },
        },
        "models": models_info,
    })