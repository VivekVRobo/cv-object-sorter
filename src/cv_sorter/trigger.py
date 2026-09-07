from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TriggerDecision:
    fire: bool
    label: str | None
    reason: str
    stable_frames: int
    latched: bool


@dataclass
class PassageTrigger:
    """Fire at most once for one object passage through the trigger band.

    The trigger only accumulates stability while the primary detection is inside
    the gate. Once fired, it remains latched until the object has been outside
    the gate (or absent) for ``reset_frames_required`` consecutive frames.

    This state machine is software behavior only. It does not prove conveyor
    timing, object tracking quality, or physical sort success.
    """

    stable_frames_required: int = 3
    reset_frames_required: int = 3
    _candidate_label: str | None = None
    _stable_frames: int = 0
    _clear_frames: int = 0
    _latched: bool = False

    def __post_init__(self) -> None:
        if self.stable_frames_required < 1:
            raise ValueError("stable_frames_required must be >= 1")
        if self.reset_frames_required < 1:
            raise ValueError("reset_frames_required must be >= 1")

    def reset(self) -> None:
        self._candidate_label = None
        self._stable_frames = 0
        self._clear_frames = 0
        self._latched = False

    def update(
        self,
        label: str | None,
        centroid_x: int | None,
        gate_left: int,
        gate_right: int,
    ) -> TriggerDecision:
        if gate_left > gate_right:
            raise ValueError("gate_left must be <= gate_right")

        inside_gate = (
            label is not None
            and centroid_x is not None
            and gate_left <= centroid_x <= gate_right
        )

        if not inside_gate:
            self._candidate_label = None
            self._stable_frames = 0
            self._clear_frames += 1
            if self._latched and self._clear_frames >= self.reset_frames_required:
                self._latched = False
                return TriggerDecision(False, None, "rearmed", 0, False)
            return TriggerDecision(
                False,
                None,
                "outside-gate" if label is not None else "no-detection",
                0,
                self._latched,
            )

        self._clear_frames = 0

        if self._latched:
            return TriggerDecision(False, label, "passage-latched", 0, True)

        if label == self._candidate_label:
            self._stable_frames += 1
        else:
            self._candidate_label = label
            self._stable_frames = 1

        if self._stable_frames >= self.stable_frames_required:
            self._latched = True
            return TriggerDecision(True, label, "stable-in-gate", self._stable_frames, True)

        return TriggerDecision(False, label, "stabilizing", self._stable_frames, False)
