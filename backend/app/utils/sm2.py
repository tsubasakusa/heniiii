"""SM-2 spaced-repetition scheduling (pure, HTTP-agnostic).

Reference: SuperMemo-2. Given a review quality 0-5, update the ease factor,
repetition count and interval (in days) for a card.
"""
from dataclasses import dataclass

DEFAULT_EASE_FACTOR = 2.5
MIN_EASE_FACTOR = 1.3


@dataclass
class Schedule:
    ease_factor: float
    interval_days: int
    repetitions: int


def review(
    ease_factor: float,
    interval_days: int,
    repetitions: int,
    quality: int,
) -> Schedule:
    """Return the updated SM-2 schedule after a review of the given quality.

    quality < 3 is treated as a lapse: repetitions reset and the card is due
    again the next day. quality >= 3 advances the interval.
    """
    q = max(0, min(5, quality))

    if q < 3:
        repetitions = 0
        interval = 1
    else:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval_days * ease_factor)
        repetitions += 1

    ease_factor = ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    ease_factor = max(MIN_EASE_FACTOR, ease_factor)

    return Schedule(
        ease_factor=round(ease_factor, 4),
        interval_days=interval,
        repetitions=repetitions,
    )
