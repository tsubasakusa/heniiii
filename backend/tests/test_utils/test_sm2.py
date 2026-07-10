from app.utils.sm2 import DEFAULT_EASE_FACTOR, MIN_EASE_FACTOR, review


def test_first_good_review_interval_1():
    s = review(DEFAULT_EASE_FACTOR, 0, 0, quality=4)
    assert s.interval_days == 1
    assert s.repetitions == 1


def test_second_good_review_interval_6():
    s = review(DEFAULT_EASE_FACTOR, 1, 1, quality=4)
    assert s.interval_days == 6
    assert s.repetitions == 2


def test_third_review_multiplies_by_ease():
    # repetitions>=2 -> interval = round(interval * ease_factor)
    s = review(2.5, 6, 2, quality=5)
    assert s.interval_days == 15  # round(6 * 2.5)
    assert s.repetitions == 3


def test_lapse_resets_repetitions_and_interval():
    s = review(2.5, 30, 5, quality=1)
    assert s.repetitions == 0
    assert s.interval_days == 1


def test_ease_factor_never_below_min():
    ef = 1.3
    for _ in range(10):
        ef = review(ef, 1, 0, quality=0).ease_factor
    assert ef >= MIN_EASE_FACTOR


def test_higher_quality_raises_ease_more_than_low():
    high = review(2.5, 1, 1, quality=5).ease_factor
    low = review(2.5, 1, 1, quality=3).ease_factor
    assert high > low
