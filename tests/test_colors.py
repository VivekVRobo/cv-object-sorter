import pytest

from cv_sorter.colors import HSVRange, classify_hsv


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
    "lower, upper",
    [
        ((-1, 100, 80), (10, 255, 255)),
        ((0, 100, 80), (180, 255, 255)),
        ((0, 256, 80), (10, 255, 255)),
        ((0, 100, 256), (10, 255, 255)),
        ((10, 100, 80), (5, 255, 255)),
        ((0, 100), (10, 255, 255)),
        ((0, 100, 80), (10, 255)),
        ((0, 100, True), (10, 255, 255)),
    ],
)
def test_invalid_hsv_ranges_are_rejected(lower, upper):
    with pytest.raises(ValueError):
        HSVRange(lower, upper)


def test_valid_opencv_hsv_range_accepts_boundary_values():
    range_ = HSVRange((0, 0, 0), (179, 255, 255))
    assert range_.contains((0, 0, 0))
    assert range_.contains((179, 255, 255))
