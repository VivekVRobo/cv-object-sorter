from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2

from .colors import HSVRange
from .detector import detect_colored_objects

SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


@dataclass(frozen=True)
class LabeledPrediction:
    source: str
    expected: str
    predicted: str
    detection_count: int
    primary_area: float | None


def predict_label(frame, color_ranges: dict[str, list[HSVRange]], min_area: float) -> tuple[str, int, float | None]:
    detections = detect_colored_objects(frame, color_ranges, min_area=min_area)
    if not detections:
        return "unknown", 0, None
    primary = detections[0]
    return primary.label, len(detections), primary.area


def evaluate_predictions(predictions: Iterable[LabeledPrediction]) -> dict:
    rows = list(predictions)
    if not rows:
        raise ValueError("at least one prediction is required")

    labels = sorted({item.expected for item in rows} | {item.predicted for item in rows})
    confusion: dict[str, dict[str, int]] = {
        expected: {predicted: 0 for predicted in labels} for expected in labels
    }
    per_class_total: Counter[str] = Counter()
    per_class_correct: Counter[str] = Counter()

    for item in rows:
        confusion[item.expected][item.predicted] += 1
        per_class_total[item.expected] += 1
        if item.expected == item.predicted:
            per_class_correct[item.expected] += 1

    correct = sum(1 for item in rows if item.expected == item.predicted)
    per_class = {}
    for label in sorted(per_class_total):
        total = per_class_total[label]
        per_class[label] = {
            "samples": total,
            "correct": per_class_correct[label],
            "accuracy": per_class_correct[label] / total if total else None,
        }

    return {
        "samples": len(rows),
        "correct": correct,
        "accuracy": correct / len(rows),
        "labels": labels,
        "confusion_matrix": confusion,
        "per_class": per_class,
    }


def evaluate_dataset(
    dataset_dir: Path,
    color_ranges: dict[str, list[HSVRange]],
    *,
    min_area: float = 900.0,
) -> tuple[dict, list[LabeledPrediction]]:
    """Evaluate ``dataset_dir/<label>/*.{png,jpg,...}`` without training.

    The directory names are the ground-truth labels. This function is suitable
    for a real, user-captured test set later, but the repository does not ship or
    claim such a physical dataset by default.
    """
    if not dataset_dir.exists():
        raise FileNotFoundError(dataset_dir)

    rows: list[LabeledPrediction] = []
    found_by_label: dict[str, int] = defaultdict(int)

    for label_dir in sorted(path for path in dataset_dir.iterdir() if path.is_dir()):
        expected = label_dir.name
        for image_path in sorted(label_dir.iterdir()):
            if image_path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
                continue
            frame = cv2.imread(str(image_path))
            if frame is None:
                raise ValueError(f"could not decode image: {image_path}")
            predicted, detection_count, primary_area = predict_label(frame, color_ranges, min_area)
            rows.append(
                LabeledPrediction(
                    source=str(image_path),
                    expected=expected,
                    predicted=predicted,
                    detection_count=detection_count,
                    primary_area=primary_area,
                )
            )
            found_by_label[expected] += 1

    if not rows:
        raise ValueError(f"no supported images found under {dataset_dir}")

    summary = evaluate_predictions(rows)
    summary["dataset_directory"] = str(dataset_dir)
    summary["samples_by_ground_truth"] = dict(sorted(found_by_label.items()))
    return summary, rows
