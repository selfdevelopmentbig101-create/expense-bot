from app.core.ratelimit import RateLimiter


def test_allows_up_to_the_limit_then_blocks():
    limiter = RateLimiter(limit=3, window=10)
    assert all(limiter.check(1, now).allowed for now in (0.0, 1.0, 2.0))
    assert limiter.check(1, 3.0).allowed is False


def test_the_user_is_told_once_and_then_left_alone_for_a_while():
    limiter = RateLimiter(limit=1, window=10, warn_every=10)
    limiter.check(1, 0.0)
    first = limiter.check(1, 1.0)
    assert (first.allowed, first.warn) == (False, True)
    second = limiter.check(1, 2.0)
    assert (second.allowed, second.warn) == (False, False)
    third = limiter.check(1, 11.5)  # the window is over, but let us block again to test the warning timer
    assert third.allowed is True


def test_the_warning_comes_again_after_the_warn_interval():
    limiter = RateLimiter(limit=1, window=100, warn_every=10)
    limiter.check(1, 0.0)
    assert limiter.check(1, 1.0).warn is True
    assert limiter.check(1, 5.0).warn is False
    assert limiter.check(1, 12.0).warn is True


def test_the_window_slides():
    limiter = RateLimiter(limit=2, window=10)
    assert limiter.check(1, 0.0).allowed and limiter.check(1, 5.0).allowed
    assert limiter.check(1, 9.9).allowed is False
    assert limiter.check(1, 10.0).allowed is True  # the first event left the window
    assert limiter.check(1, 10.1).allowed is False  # 5.0 and 10.0 are still inside


def test_refused_events_do_not_extend_the_block():
    limiter = RateLimiter(limit=1, window=10)
    limiter.check(1, 0.0)
    for now in (1.0, 3.0, 5.0, 9.0):
        assert limiter.check(1, now).allowed is False
    assert limiter.check(1, 10.0).allowed is True  # 10 seconds after the last ALLOWED event


def test_users_are_independent():
    limiter = RateLimiter(limit=1, window=10)
    assert limiter.check(1, 0.0).allowed
    assert limiter.check(2, 0.0).allowed
    assert limiter.check(1, 1.0).allowed is False


def test_memory_is_cleaned_up():
    limiter = RateLimiter(limit=1, window=10, max_keys=5)
    for user in range(20):
        limiter.check(user, 0.0)
    limiter.check(999, 100.0)  # far later: the old users are forgotten
    assert len(limiter._hits) <= 2
