#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

from cv_sorter.colors import load_color_ranges
from cv_sorter.evaluation import LabeledPrediction, evaluate_predictions, predict_label


def hsv_to_bgr_pixel(hsv: tuple[int, int, int]) -> tuple[int, int, int]:
    pixel = np.array([[hsv]], dtype=np.uint8)
    bgr = cv2.cvtColor(pixel, cv2.COLOR_HSV2BGR)[0, 0]
    return int(bgr[0]), int(bgr[1]), int(bgr[2])


def make_frame(hsv: tuple[int, int, int], shape: str) -> np.ndarray:
    frame = np.full((240, 320, 3), 24, dtype=np.uint8)
    color = hsv_to_bgr_pixel(hsv)
    if shape == "rectangle":
        cv2.rectangle(frame, (100, 70), (220, 170), color, thickness=-1)
    elif shape == "circle":
        cv2.circle(frame, (160, 120), 58, color, thickness=-1)
    else:
        raise ValueError(f"unknown shape: {shape}")
    return frame


def cases() -> list[tuple[str, tuple[int, int, int]]]:
    rows: list[tuple[str, tuple[int, int, int]]] = []
    saturation_value_pairs = [(120, 120), (180, 210), (255, 255)]
    class_hues = {
        "red": [0, 5, 10, 170, 175, 179],
        "green": [35, 45, 60, 75, 85],
        "blue": [90, 100, 115, 130, 135],
    }
    for label, hues in class_hues.items():
        for hue in hues:
            for saturation, value in saturation_value_pairs:
                rows.append((label, (hue, saturation, value)))

    # High-saturation hues that intentionally sit outside the configured classes.
    for hue in [15, 20, 25, 30, 87, 88, 89, 136, 140, 145, 150, 160, 165]:
        rows.append(("unknown", (hue, 220, 220)))

    # Known-class hues with deliberately insufficient saturation/value should
    # also be rejected by the configured reference thresholds.
    for hsv in [(5, 50, 220), (60, 40, 220), (110, 50, 220), (5, 220, 40), (60, 220, 40), (110, 220, 40)]:
        rows.append(("unknown", hsv))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic software-only HSV pipeline evidence")
    parser.add_argument("--config", type=Path, default=Path("config/colors.yaml"))
    parser.add_argument("--min-area", type=float, default=900.0)
    parser.add_argument("--output", type=Path, default=Path("artifacts/synthetic-vision-evidence.json"))
    args = parser.parse_args()

    color_ranges = load_color_ranges(args.config)
    predictions: list[LabeledPrediction] = []
    case_records: list[dict] = []
    index = 0
    for expected, hsv in cases():
        for shape in ("rectangle", "circle"):
            index += 1
            frame = make_frame(hsv, shape)
            predicted, detection_count, primary_area = predict_label(frame, color_ranges, args.min_area)
            source = f"synthetic-{index:03d}:{shape}:hsv={hsv}"
            row = LabeledPrediction(source, expected, predicted, detection_count, primary_area)
            predictions.append(row)
            case_records.append({**asdict(row), "hsv": list(hsv), "shape": shape})

    summary = evaluate_predictions(predictions)
    report = {
        "schema_version": 1,
        "evidence_type": "synthetic_threshold_contract_validation",
        "hardware_evidence": False,
        "real_camera_dataset": False,
        "claim_boundary": (
            "This deterministic evidence checks the configured HSV threshold, morphology, contour, area, and "
            "primary-detection software path on synthetic shapes. It is not a real-world camera accuracy claim."
        ),
        "config": str(args.config),
        "min_area": args.min_area,
        "summary": summary,
        "cases": case_records,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0 if summary["accuracy"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
