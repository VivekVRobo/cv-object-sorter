from cv_sorter.evaluation import LabeledPrediction, evaluate_predictions


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
