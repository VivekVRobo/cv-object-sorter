from collections.abc import Sequence
from dataclasses import dataclass
from numbers import Integral
from pathlib import Path

import yaml


_HSV_LIMITS = (179, 255, 255)


def _validated_hsv_triplet(values: object, name: str) -> tuple[int, int, int]:
    """Return a normalized OpenCV HSV triplet or fail with a useful error."""
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must contain exactly 3 integer channels")
    if len(values) != 3:
        raise ValueError(f"{name} must contain exactly 3 integer channels")

    normalized: list[int] = []
    for index, (value, maximum) in enumerate(zip(values, _HSV_LIMITS)):
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise ValueError(f"{name}[{index}] must be an integer")
        channel = int(value)
        if not 0 <= channel <= maximum:
            raise ValueError(f"{name}[{index}] must be between 0 and {maximum}")
        normalized.append(channel)

    return tuple(normalized)


@dataclass(frozen=True)
class HSVRange:
    lower: tuple[int, int, int]
    upper: tuple[int, int, int]

    def __post_init__(self) -> None:
        lower = _validated_hsv_triplet(self.lower, "lower")
        upper = _validated_hsv_triplet(self.upper, "upper")
        for index, (low, high) in enumerate(zip(lower, upper)):
            if low > high:
                raise ValueError(f"lower[{index}] must be <= upper[{index}]")
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)

    def contains(self, hsv: tuple[int, int, int]) -> bool:
        channels = _validated_hsv_triplet(hsv, "hsv")
        return all(lo <= value <= hi for value, lo, hi in zip(channels, self.lower, self.upper))


def load_color_ranges(path: str | Path) -> dict[str, list[HSVRange]]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("color config must be a YAML mapping")

    colors = raw.get("colors")
    if not isinstance(colors, dict) or not colors:
        raise ValueError("color config must contain a non-empty 'colors' mapping")

    result: dict[str, list[HSVRange]] = {}
    for name, ranges in colors.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("color names must be non-empty strings")
        if not isinstance(ranges, list) or not ranges:
            raise ValueError(f"colors.{name} must be a non-empty list of HSV ranges")

        parsed: list[HSVRange] = []
        for index, item in enumerate(ranges):
            if not isinstance(item, dict) or "lower" not in item or "upper" not in item:
                raise ValueError(f"colors.{name}[{index}] must define lower and upper channels")
            try:
                parsed.append(HSVRange(tuple(item["lower"]), tuple(item["upper"])))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid HSV range at colors.{name}[{index}]: {exc}") from exc
        result[name] = parsed

    return result


def classify_hsv(hsv: tuple[int, int, int], ranges: dict[str, list[HSVRange]]) -> str | None:
    for label, candidates in ranges.items():
        if any(candidate.contains(hsv) for candidate in candidates):
            return label
    return None
