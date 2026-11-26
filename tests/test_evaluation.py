from pathlib import Path

from cv_sorter.evaluation import (
    LabeledPrediction,
    dataset_manifest_sha256,
    evaluate_predictions,
    sha256_file,
)


def test_evaluate_predictions_builds_confusion_and_per_class_accuracy():
    rows = [
        LabeledPrediction("a", "red", "red", 1, 1000.0),
        LabeledPrediction("b", "red", "green", 1, 1000.0),
        LabeledPrediction("c", "green", "green", 1, 1000.0),
        LabeledPrediction("d", "unknown", "unknown", 0, None),
    ]

    report = evaluate_predictions(rows)

    assert report["samples"] == 4
    assert report["correct"] == 3
    assert report["accuracy"] == 0.75
    assert report["confusion_matrix"]["red"]["red"] == 1
    assert report["confusion_matrix"]["red"]["green"] == 1
    assert report["per_class"]["red"]["accuracy"] == 0.5
    assert report["per_class"]["green"]["accuracy"] == 1.0
    assert report["per_class"]["unknown"]["accuracy"] == 1.0
    assert len(report["dataset_manifest_sha256"]) == 64


def test_dataset_manifest_changes_when_image_identity_changes(tmp_path: Path):
    first = tmp_path / "first.bin"
    second = tmp_path / "second.bin"
    first.write_bytes(b"image-a")
    second.write_bytes(b"image-b")

    first_hash = sha256_file(first)
    second_hash = sha256_file(second)

    rows = [
        LabeledPrediction("first.png", "red", "red", 1, 10.0, first_hash),
        LabeledPrediction("second.png", "green", "green", 1, 20.0, second_hash),
    ]
    original = dataset_manifest_sha256(rows)

    first.write_bytes(b"image-a-changed")
    changed_hash = sha256_file(first)
    changed_rows = [
        LabeledPrediction("first.png", "red", "red", 1, 10.0, changed_hash),
        LabeledPrediction("second.png", "green", "green", 1, 20.0, second_hash),
    ]

    assert original != dataset_manifest_sha256(changed_rows)
