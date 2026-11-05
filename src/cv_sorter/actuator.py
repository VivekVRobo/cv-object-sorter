import time
from dataclasses import dataclass
from typing import Optional

COMMANDS = {"red": "R", "green": "G", "blue": "B", "neutral": "N"}


def encode_sort_command(label: str) -> bytes:
    if label not in COMMANDS:
        raise ValueError(f"unsupported sort label: {label}")
    return f"{COMMANDS[label]}\n".encode("ascii")


@dataclass
class SortActuator:
    serial_port: Optional[object] = None
    cooldown_s: float = 1.0
    _last_fire: float = -1e9

    def __post_init__(self) -> None:
        if self.cooldown_s < 0:
            raise ValueError("cooldown_s must be >= 0")

    def ready(self) -> bool:
        return time.monotonic() - self._last_fire >= self.cooldown_s

    def sort(self, label: str) -> bool:
        if not self.ready():
            return False
        payload = encode_sort_command(label)
        if self.serial_port is None:
            print(f"DRY-RUN sort={label} command={payload.decode().strip()}")
        else:
            self.serial_port.write(payload)
        self._last_fire = time.monotonic()
        return True
