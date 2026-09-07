#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from cv_sorter.colors import load_color_ranges
from cv_sorter.evaluation import evaluate_dataset


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a labeled image dataset stored as DATASET/<label>/*"
    )
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--config", type=Path, default=Path("config/colors.yaml"))
    parser.add_argument("--min-area", type=float, default=900.0)
    parser.add_argument("--output", type=Path, default=Path("artifacts/dataset-evaluation.json"))
    parser.add_argument("--predictions-csv", type=Path, default=Path("artifacts/dataset-predictions.csv"))
    args = parser.parse_args()

    color_ranges = load_color_ranges(args.config)
    summary, rows = evaluate_dataset(args.dataset, color_ranges, min_area=args.min_area)
    report = {
        "evidence_type": "labeled_image_dataset_evaluation",
        "physical_sort_evidence": False,
        "claim_boundary": (
            "This report evaluates image classification/detection only. It does not prove conveyor timing, "
            "actuator timing, or physical sorting success. Real-world accuracy is meaningful only when the "
            "dataset itself was captured and documented under representative camera/lighting conditions."
        ),
        "config": str(args.config),
        "min_area": args.min_area,
        "summary": summary,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    args.predictions_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.predictions_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source", "expected", "predicted", "detection_count", "primary_area"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "source": row.source,
                    "expected": row.expected,
                    "predicted": row.predicted,
                    "detection_count": row.detection_count,
                    "primary_area": row.primary_area,
                }
            )

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
