from collections import deque
from typing import Deque, Iterable, Optional, Tuple

import numpy as np


Point = Tuple[float, float]


def calculate_angle(a: Point, b: Point, c: Point) -> float:
    """Return the smaller angle ABC in degrees using only NumPy math."""
    pa = np.array(a, dtype=np.float32)
    pb = np.array(b, dtype=np.float32)
    pc = np.array(c, dtype=np.float32)

    ba = pa - pb
    bc = pc - pb

    norm_product = np.linalg.norm(ba) * np.linalg.norm(bc)
    if norm_product == 0:
        return 0.0

    cosine = np.dot(ba, bc) / norm_product
    angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
    return float(angle)


def midpoint(a: Point, b: Point) -> Point:
    return ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5)


class MovingAverage:
    """Tiny fixed-window smoother for reducing pose angle jitter."""

    def __init__(self, window_size: int = 5) -> None:
        self.values: Deque[float] = deque(maxlen=max(1, window_size))

    def update(self, value: Optional[float]) -> Optional[float]:
        if value is None:
            return self.current

        self.values.append(float(value))
        return self.current

    @property
    def current(self) -> Optional[float]:
        if not self.values:
            return None
        return float(np.mean(np.array(self.values, dtype=np.float32)))


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def first_message(messages: Iterable[str]) -> str:
    return next(iter(messages), "")