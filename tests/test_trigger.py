import pytest

from cv_sorter.trigger import PassageTrigger


def test_fires_once_for_one_passage_and_rearms_after_clear_frames():
    trigger = PassageTrigger(stable_frames_required=3, reset_frames_required=2)

    assert not trigger.update("red", 100, 90, 110).fire
    assert not trigger.update("red", 100, 90, 110).fire
    third = trigger.update("red", 100, 90, 110)
    assert third.fire
    assert third.label == "red"
    assert third.reason == "stable-in-gate"
    assert third.latched

    for _ in range(10):
        decision = trigger.update("red", 100, 90, 110)
        assert not decision.fire
        assert decision.reason == "passage-latched"

    assert trigger.update("red", 130, 90, 110).latched
    rearmed = trigger.update(None, None, 90, 110)
    assert not rearmed.latched
    assert rearmed.reason == "rearmed"

    assert not trigger.update("green", 100, 90, 110).fire
    assert not trigger.update("green", 100, 90, 110).fire
    assert trigger.update("green", 100, 90, 110).fire


def test_label_change_resets_stability_before_fire():
    trigger = PassageTrigger(stable_frames_required=3, reset_frames_required=2)

    assert trigger.update("red", 100, 90, 110).stable_frames == 1
    assert trigger.update("red", 100, 90, 110).stable_frames == 2
    changed = trigger.update("blue", 100, 90, 110)
    assert not changed.fire
    assert changed.stable_frames == 1
    assert trigger.update("blue", 100, 90, 110).stable_frames == 2
    assert trigger.update("blue", 100, 90, 110).fire


def test_outside_gate_does_not_accumulate_stability():
    trigger = PassageTrigger(stable_frames_required=2, reset_frames_required=2)

    outside = trigger.update("red", 50, 90, 110)
    assert outside.reason == "outside-gate"
    assert outside.stable_frames == 0
    assert not outside.fire

    first_inside = trigger.update("red", 100, 90, 110)
    assert first_inside.stable_frames == 1
    assert not first_inside.fire


def test_configuration_validation():
    with pytest.raises(ValueError):
        PassageTrigger(stable_frames_required=0)
    with pytest.raises(ValueError):
        PassageTrigger(reset_frames_required=0)
