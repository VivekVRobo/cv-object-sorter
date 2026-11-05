import pytest

from cv_sorter.actuator import SortActuator, encode_sort_command


def test_command_encoding():
    assert encode_sort_command("red") == b"R\n"
    assert encode_sort_command("green") == b"G\n"
    assert encode_sort_command("blue") == b"B\n"


def test_unknown_label():
    with pytest.raises(ValueError):
        encode_sort_command("orange")


def test_negative_cooldown_is_rejected():
    with pytest.raises(ValueError, match="cooldown_s must be >= 0"):
        SortActuator(cooldown_s=-0.1)


def test_zero_cooldown_is_allowed():
    actuator = SortActuator(cooldown_s=0)
    assert actuator.ready()
