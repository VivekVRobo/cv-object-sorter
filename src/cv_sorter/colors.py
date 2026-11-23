from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HSVRange:
    lower: tuple[int, int, int]
    upper: tuple[int, int, int]

    def __post_init__(self) -> None:
        if len(self.lower) != 3 or len(self.upper) != 3:
            raise ValueError("HSV bounds must contain exactly three channels")
        if any(not isinstance(value, int) or isinstance(value, bool) for value in (*self.lower, *self.upper)):
            raise ValueError("HSV bounds must contain integers")
        if any(value < 0 or value > 179 for value in (self.lower[0], self.upper[0])):
            raise ValueError("HSV hue must be in the OpenCV range 0..179")
        if any(value < 0 or value > 255 for value in (*self.lower[1:], *self.upper[1:])):
            raise ValueError("HSV saturation/value must be in the OpenCV range 0..255")
        if any(lo > hi for lo, hi in zip(self.lower, self.upper)):
            raise ValueError("HSV lower bounds must not exceed upper bounds")

    def contains(self, hsv: tuple[int, int, int]) -> bool:
        return all(lo <= value <= hi for value, lo, hi in zip(hsv, self.lower, self.upper))


def load_color_ranges(path: str | Path) -> dict[str, list[HSVRange]]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    result: dict[str, list[HSVRange]] = {}
    for name, ranges in raw["colors"].items():
        result[name] = [HSVRange(tuple(item["lower"]), tuple(item["upper"])) for item in ranges]
    return result


def classify_hsv(hsv: tuple[int, int, int], ranges: dict[str, list[HSVRange]]) -> str | None:
    for label, candidates in ranges.items():
        if any(candidate.contains(hsv) for candidate in candidates):
            return label
    return None
