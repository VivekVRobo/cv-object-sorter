import pytest

from cv_sorter.colors import HSVRange, classify_hsv, load_color_ranges


def test_range_contains():
    r = HSVRange((0, 100, 80), (10, 255, 255))
    assert r.contains((5, 150, 120))
    assert not r.contains((20, 150, 120))


def test_classification_with_split_red_ranges():
    ranges = {
        "red": [HSVRange((0, 100, 80), (10, 255, 255)), HSVRange((170, 100, 80), (179, 255, 255))],
        "green": [HSVRange((35, 70, 60), (85, 255, 255))],
    }
    assert classify_hsv((5, 200, 200), ranges) == "red"
    assert classify_hsv((175, 200, 200), ranges) == "red"
    assert classify_hsv((60, 200, 200), ranges) == "green"
    assert classify_hsv((100, 20, 20), ranges) is None


@pytest.mark.parametrize(
    ("lower", "upper"),
    [
        ((0, 100), (10, 255, 255)),
        ((-1, 100, 80), (10, 255, 255)),
        ((0, 100, 80), (180, 255, 255)),
        ((10, 100, 80), (9, 255, 255)),
        ((0, 100, 80), (10, 256, 255)),
        ((0, 100.5, 80), (10, 255, 255)),
        ((True, 100, 80), (10, 255, 255)),
    ],
)
def test_invalid_hsv_ranges_are_rejected(lower, upper):
    with pytest.raises(ValueError):
        HSVRange(lower, upper)


def test_contains_rejects_malformed_hsv_triplet():
    color_range = HSVRange((0, 100, 80), (10, 255, 255))
    with pytest.raises(ValueError, match="hsv must contain exactly 3 integer channels"):
        color_range.contains((5, 150))


def test_loader_reports_malformed_config_range(tmp_path):
    config = tmp_path / "colors.yaml"
    config.write_text(
        "colors:\n  red:\n    - lower: [0, 100]\n      upper: [10, 255, 255]\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"colors\.red\[0\]"):
        load_color_ranges(config)
