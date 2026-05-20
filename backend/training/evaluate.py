"""
backend/training/evaluate.py

Deeptection model evaluation script.

Purpose:
- Evaluate the fine-tuned local video model on the held-out video dataset.
- Evaluate the fine-tuned local audio model on the held-out audio dataset.
- Optionally evaluate synthetic fusion pairings when both video and audio results are available.
- Save a JSON report for Chapter 5 evidence.

Run from:
    D:\APU\deeptection\deeptection\backend

Examples:
    py -3.11 -m training.evaluate --video-data ../datasets/video --split test
    py -3.11 -m training.evaluate --audio-data ../datasets/audio --split test
    py -3.11 -m training.evaluate --video-data ../datasets/video --audio-data ../datasets/audio --split test
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Force local checkpoints before importing backend model-loading modules.
# This ensures the evaluation measures the fine-tuned local models used in the system.
os.environ.setdefault("DEEPTECTION_USE_LOCAL", "1")
os.environ.setdefault("DEEPTECTION_VIDEO_MODEL", "local/ignore")
os.environ.setdefault("DEEPTECTION_AUDIO_MODEL", "local/ignore")

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)

import config
from inference.fusion import fuse_and_decide
from preprocessing.audio_preprocessor import preprocess_audio, logmel_to_tensor


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("deeptection.evaluate")


@dataclass
class ModalityScores:
    y_true: List[int] = field(default_factory=list)          # 0 = real, 1 = fake
    y_pred_proba: List[float] = field(default_factory=list)  # probability of fake
    filenames: List[str] = field(default_factory=list)


@dataclass
class Metrics:
    accuracy: float
    precision: float
    recall: float
    f1: float
    auc: Optional[float]
    confusion: Dict[str, int]
    threshold: float
    support: Dict[str, int]


def _as_float_list(values: Any) -> List[float]:
    """Convert tensor / numpy array / list / scalar into a flat Python float list."""
    if isinstance(values, torch.Tensor):
        values = values.detach().cpu().numpy()
    arr = np.asarray(values, dtype=np.float32).reshape(-1)
    return [float(x) for x in arr.tolist()]


def compute_metrics(y_true: List[int], y_proba: List[float], threshold: float = 0.5) -> Metrics:
    if len(y_true) != len(y_proba):
        raise ValueError(
            f"Label/prediction length mismatch: labels={len(y_true)}, predictions={len(y_proba)}. "
            "Evaluation must produce one prediction score per sample."
        )

    y_true_arr = np.asarray(y_true, dtype=np.int64)
    y_proba_arr = np.asarray(y_proba, dtype=np.float32)
    y_pred = (y_proba_arr >= threshold).astype(np.int64)

    accuracy = float(accuracy_score(y_true_arr, y_pred))
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true_arr,
        y_pred,
        average="binary",
        pos_label=1,
        zero_division=0,
    )

    try:
        auc = float(roc_auc_score(y_true_arr, y_proba_arr)) if len(set(y_true)) == 2 else None
    except ValueError:
        auc = None

    tn, fp, fn, tp = confusion_matrix(y_true_arr, y_pred, labels=[0, 1]).ravel()

    return Metrics(
        accuracy=accuracy,
        precision=float(precision),
        recall=float(recall),
        f1=float(f1),
        auc=auc,
        confusion={"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)},
        threshold=float(threshold),
        support={
            "real": int((y_true_arr == 0).sum()),
            "fake": int((y_true_arr == 1).sum()),
        },
    )


def find_best_threshold(
    y_true: List[int],
    y_proba: List[float],
    grid: Tuple[float, float, float] = (0.30, 0.80, 0.02),
) -> Tuple[float, float]:
    best_threshold = 0.5
    best_f1 = -1.0
    low, high, step = grid
    t = low

    while t <= high + 1e-9:
        metrics = compute_metrics(y_true, y_proba, threshold=t)
        if metrics.f1 > best_f1:
            best_f1 = metrics.f1
            best_threshold = t
        t += step

    return round(float(best_threshold), 3), round(float(best_f1), 4)


def print_metrics(title: str, metrics: Metrics) -> None:
    log.info("============================================================")
    log.info("%s", title)
    log.info("============================================================")
    log.info("Threshold : %.3f", metrics.threshold)
    log.info("Accuracy  : %.4f", metrics.accuracy)
    log.info("Precision : %.4f", metrics.precision)
    log.info("Recall    : %.4f", metrics.recall)
    log.info("F1-score  : %.4f", metrics.f1)
    if metrics.auc is not None:
        log.info("AUC-ROC   : %.4f", metrics.auc)
    else:
        log.info("AUC-ROC   : N/A")
    log.info(
        "Confusion : TN=%d, FP=%d, FN=%d, TP=%d",
        metrics.confusion["TN"],
        metrics.confusion["FP"],
        metrics.confusion["FN"],
        metrics.confusion["TP"],
    )
    log.info("Support   : real=%d, fake=%d", metrics.support["real"], metrics.support["fake"])


def _load_local_video_model() -> torch.nn.Module:
    """Load the fine-tuned local MobileNetV3-Small checkpoint."""
    from models.video_model import load_local_video_model

    device = getattr(config, "DEVICE", "cpu")
    model = load_local_video_model(device=device)

    ckpt_path = config.STORAGE_DIR / "video_finetuned.pt"
    if ckpt_path.exists():
        state = torch.load(str(ckpt_path), map_location=device)
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        model.load_state_dict(state, strict=False)
        log.info("Loaded video checkpoint: %s", ckpt_path)
    else:
        log.warning("Video checkpoint not found at %s. Evaluating model without this checkpoint.", ckpt_path)

    model.to(device)
    model.eval()
    return model


def _video_logits_to_fake_probability(logits: torch.Tensor) -> torch.Tensor:
    """Return one P(fake) score per sample."""
    if logits.ndim == 2 and logits.shape[1] >= 2:
        return F.softmax(logits, dim=1)[:, 1]
    if logits.ndim == 2 and logits.shape[1] == 1:
        return torch.sigmoid(logits[:, 0])
    return torch.sigmoid(logits.reshape(-1))


def evaluate_video(data_root: Path, split: str = "test", batch_size: int = 32) -> ModalityScores:
    """
    Evaluate local MobileNetV3-Small on:
        data_root/split/real
        data_root/split/fake

    Important fix:
    This function produces one prediction score per image, not one score per batch.
    """
    split_root = data_root / split
    if not split_root.exists():
        raise SystemExit(f"Video split folder not found: {split_root}")

    transform = transforms.Compose(
        [
            transforms.Resize((256, 256)),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
        ]
    )

    dataset = datasets.ImageFolder(str(split_root), transform=transform)

    if "real" not in dataset.class_to_idx or "fake" not in dataset.class_to_idx:
        raise SystemExit(f"Expected folders 'real' and 'fake' inside {split_root}")

    fake_idx = dataset.class_to_idx["fake"]
    remapped_samples = []
    for file_path, original_label in dataset.samples:
        remapped_samples.append((file_path, 1 if original_label == fake_idx else 0))

    dataset.samples = remapped_samples
    dataset.targets = [label for _, label in remapped_samples]

    log.info("============================================================")
    log.info("Deeptection — Video Model Evaluation")
    log.info("============================================================")
    log.info("Loading test images from %s", split_root)
    log.info("real: %d images", int(sum(1 for _, y in dataset.samples if y == 0)))
    log.info("fake: %d images", int(sum(1 for _, y in dataset.samples if y == 1)))
    log.info("Total samples: %d", len(dataset.samples))

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    model = _load_local_video_model()
    device = getattr(config, "DEVICE", "cpu")

    scores = ModalityScores()

    with torch.inference_mode():
        for batch_index, (xb, yb) in enumerate(loader, start=1):
            xb = xb.to(device)
            logits = model(xb)
            probs = _video_logits_to_fake_probability(logits)

            batch_scores = _as_float_list(probs)
            batch_labels = [int(y) for y in yb.detach().cpu().numpy().reshape(-1).tolist()]

            scores.y_pred_proba.extend(batch_scores)
            scores.y_true.extend(batch_labels)

            if batch_index % 10 == 0:
                log.info("Video progress: %d / %d samples", len(scores.y_true), len(dataset.samples))

    scores.filenames = [str(path) for path, _ in dataset.samples]

    if len(scores.y_true) != len(scores.y_pred_proba):
        raise RuntimeError(
            f"Video evaluation mismatch: labels={len(scores.y_true)}, "
            f"predictions={len(scores.y_pred_proba)}"
        )

    log.info("Video scored samples: %d", len(scores.y_true))
    return scores


def evaluate_audio(data_root: Path, split: str = "test") -> ModalityScores:
    """
    Evaluate local MelCNN on:
        data_root/split/real
        data_root/split/fake
    """
    from models.model_loader import get_model_for

    split_root = data_root / split
    if not split_root.exists():
        raise SystemExit(f"Audio split folder not found: {split_root}")

    exts = (".wav", ".flac", ".mp3", ".m4a", ".ogg")
    items: List[Tuple[Path, int]] = []

    for label, cls in enumerate(("real", "fake")):
        class_root = split_root / cls
        if not class_root.exists():
            continue
        for path in class_root.rglob("*"):
            if path.suffix.lower() in exts:
                items.append((path, label))

    if not items:
        raise SystemExit(f"No supported audio files found in {split_root}")

    log.info("============================================================")
    log.info("Deeptection — Audio Model Evaluation")
    log.info("============================================================")
    log.info("Loading test audio from %s", split_root)
    log.info("real: %d files", int(sum(1 for _, y in items if y == 0)))
    log.info("fake: %d files", int(sum(1 for _, y in items if y == 1)))
    log.info("Total samples: %d", len(items))

    # Force evaluation to use the local fine-tuned MelCNN checkpoint.
    # This matches Daily Message mode/local audio evaluation and avoids loading a Hugging Face repo accidentally.
    bundle = get_model_for("audio", "local")
    log.info("Audio model: %s (kind=%s)", bundle.name, bundle.kind)

    scores = ModalityScores()

    for index, (path, label) in enumerate(items, start=1):
        preprocessed = preprocess_audio(path)

        if not preprocessed or not preprocessed.get("ok"):
            log.warning("Skipping %s because preprocessing failed: %s", path.name, (preprocessed or {}).get("error"))
            continue

        try:
            if bundle.kind == "hf_audio":
                score = float(bundle.predict(preprocessed["waveform"]))
            else:
                score = float(bundle.predict(logmel_to_tensor(preprocessed["logmel"])))
        except Exception as exc:
            log.warning("Skipping %s because inference failed: %s", path.name, exc)
            continue

        scores.y_pred_proba.append(max(0.0, min(1.0, score)))
        scores.y_true.append(int(label))
        scores.filenames.append(str(path))

        if index % 100 == 0:
            log.info("Audio progress: %d / %d files", index, len(items))

    if len(scores.y_true) != len(scores.y_pred_proba):
        raise RuntimeError(
            f"Audio evaluation mismatch: labels={len(scores.y_true)}, "
            f"predictions={len(scores.y_pred_proba)}"
        )

    log.info("Audio scored samples: %d", len(scores.y_true))
    return scores


def evaluate_fusion_paired(
    video_scores: ModalityScores,
    audio_scores: ModalityScores,
    max_pairs: int = 600,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Synthetic paired fusion evaluation.

    The video and audio test datasets are not naturally aligned. Therefore, this function pairs
    available video and audio samples into controlled scenarios:
    - real video + real audio = real
    - fake video + fake audio = fake
    - fake video + real audio = fake
    - real video + fake audio = fake

    This is useful for checking the fusion rules, not for claiming dataset-level benchmark accuracy.
    """
    rng = random.Random(seed)

    def idx_by_label(scores: ModalityScores, label: int) -> List[int]:
        return [i for i, y in enumerate(scores.y_true) if y == label]

    v_real = idx_by_label(video_scores, 0)
    v_fake = idx_by_label(video_scores, 1)
    a_real = idx_by_label(audio_scores, 0)
    a_fake = idx_by_label(audio_scores, 1)

    for group in (v_real, v_fake, a_real, a_fake):
        rng.shuffle(group)

    per_group = max(1, max_pairs // 4)

    pairings = [
        ("real_video+real_audio", v_real[:per_group], a_real[:per_group], 0),
        ("fake_video+fake_audio", v_fake[:per_group], a_fake[:per_group], 1),
        ("fake_video+real_audio", v_fake[:per_group], a_real[:per_group], 1),
        ("real_video+fake_audio", v_real[:per_group], a_fake[:per_group], 1),
    ]

    result: Dict[str, Any] = {}
    all_true: List[int] = []
    all_scores: List[float] = []
    verdict_counts: Dict[str, int] = {"real": 0, "fake": 0, "uncertain": 0}
    fusion_mode_counts: Dict[str, int] = {}

    for name, video_indices, audio_indices, label in pairings:
        y_true: List[int] = []
        y_proba: List[float] = []

        for video_index, audio_index in zip(video_indices, audio_indices):
            video = {
                "available": True,
                "score": video_scores.y_pred_proba[video_index],
                "quality": {},
                "ensemble": None,
            }
            audio = {
                "available": True,
                "score": audio_scores.y_pred_proba[audio_index],
                "quality": {},
            }

            fused = fuse_and_decide(video, audio)
            y_true.append(label)
            y_proba.append(float(fused.get("final_score", 0.5)))

            verdict = str(fused.get("verdict", "uncertain"))
            verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1

            mode = str(fused.get("fusion_mode", "unknown"))
            fusion_mode_counts[mode] = fusion_mode_counts.get(mode, 0) + 1

        if y_true:
            metrics = compute_metrics(y_true, y_proba, threshold=0.5)
            print_metrics(f"FUSION PAIRING — {name}", metrics)
            result[name] = asdict(metrics)
            all_true.extend(y_true)
            all_scores.extend(y_proba)

    if all_true:
        default_metrics = compute_metrics(all_true, all_scores, threshold=0.5)
        best_t, best_f1 = find_best_threshold(all_true, all_scores)
        tuned_metrics = compute_metrics(all_true, all_scores, threshold=best_t)

        print_metrics("FUSION OVERALL — threshold=0.5", default_metrics)
        print_metrics(f"FUSION OVERALL — tuned threshold={best_t}", tuned_metrics)

        result["overall_default"] = asdict(default_metrics)
        result["overall_tuned"] = asdict(tuned_metrics)
        result["best_threshold"] = best_t
        result["best_f1"] = best_f1

    result["verdict_counts"] = verdict_counts
    result["fusion_mode_counts"] = fusion_mode_counts

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Deeptection video, audio and fusion models.")
    parser.add_argument("--video-data", type=str, default=None, help="Root video dataset folder. Example: ../datasets/video")
    parser.add_argument("--audio-data", type=str, default=None, help="Root audio dataset folder. Example: ../datasets/audio")
    parser.add_argument("--split", type=str, default="test", help="Dataset split to evaluate, for example test or val.")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for video evaluation.")
    parser.add_argument("--out", type=str, default="./storage/eval_report.json", help="Output JSON report path.")
    parser.add_argument("--fusion-max-pairs", type=int, default=600, help="Maximum synthetic fusion pairs to evaluate.")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if not args.video_data and not args.audio_data:
        raise SystemExit("Please provide --video-data and/or --audio-data.")

    report: Dict[str, Any] = {
        "split": args.split,
        "device": str(getattr(config, "DEVICE", "cpu")),
        "thresholds": {
            "fake": getattr(config, "DECISION_FAKE_THRESHOLD", None),
            "real": getattr(config, "DECISION_REAL_THRESHOLD", None),
            "confidence_min": getattr(config, "DECISION_CONFIDENCE_MIN", None),
        },
    }

    video_scores: Optional[ModalityScores] = None
    audio_scores: Optional[ModalityScores] = None

    if args.video_data:
        video_scores = evaluate_video(Path(args.video_data), split=args.split, batch_size=args.batch_size)
        video_default = compute_metrics(video_scores.y_true, video_scores.y_pred_proba, threshold=0.5)
        best_t, best_f1 = find_best_threshold(video_scores.y_true, video_scores.y_pred_proba)
        video_tuned = compute_metrics(video_scores.y_true, video_scores.y_pred_proba, threshold=best_t)

        print_metrics("VIDEO — threshold=0.5", video_default)
        print_metrics(f"VIDEO — tuned threshold={best_t}", video_tuned)

        report["video"] = {
            "model": "Fine-tuned MobileNetV3-Small",
            "dataset": f"{args.video_data}/{args.split}",
            "n_samples": len(video_scores.y_true),
            "metrics_default": asdict(video_default),
            "metrics_tuned": asdict(video_tuned),
            "best_threshold": best_t,
            "best_f1": best_f1,
        }

    if args.audio_data:
        audio_scores = evaluate_audio(Path(args.audio_data), split=args.split)
        audio_default = compute_metrics(audio_scores.y_true, audio_scores.y_pred_proba, threshold=0.5)
        best_t, best_f1 = find_best_threshold(audio_scores.y_true, audio_scores.y_pred_proba)
        audio_tuned = compute_metrics(audio_scores.y_true, audio_scores.y_pred_proba, threshold=best_t)

        print_metrics("AUDIO — threshold=0.5", audio_default)
        print_metrics(f"AUDIO — tuned threshold={best_t}", audio_tuned)

        report["audio"] = {
            "model": "Fine-tuned MelCNN",
            "dataset": f"{args.audio_data}/{args.split}",
            "n_samples": len(audio_scores.y_true),
            "metrics_default": asdict(audio_default),
            "metrics_tuned": asdict(audio_tuned),
            "best_threshold": best_t,
            "best_f1": best_f1,
        }

    if video_scores is not None and audio_scores is not None:
        report["fusion"] = evaluate_fusion_paired(video_scores, audio_scores, max_pairs=args.fusion_max_pairs)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    log.info("============================================================")
    log.info("Evaluation report saved to: %s", out_path)
    log.info("Use this terminal output and JSON report as Chapter 5 evidence.")
    log.info("============================================================")


if __name__ == "__main__":
    main()
