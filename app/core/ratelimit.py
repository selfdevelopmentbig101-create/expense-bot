"""Sliding-window rate limiter. Pure logic; the clock is passed in, so it is easy to test."""
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    warn: bool = False  # tell the user to slow down (at most once per warn_every seconds)


class RateLimiter:
    """At most `limit` events per `window` seconds for each key (a Telegram user id).

    Refused events are not counted, so a user is free again `window` seconds after the
    last ALLOWED event.
    """

    def __init__(self, limit: int, window: float, warn_every: float = 10.0, max_keys: int = 5000) -> None:
        self.limit, self.window, self.warn_every, self.max_keys = limit, window, warn_every, max_keys
        self._hits: dict[int, deque[float]] = {}
        self._warned: dict[int, float] = {}

    def check(self, key: int, now: float) -> Decision:
        if len(self._hits) > self.max_keys:
            self.cleanup(now)
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] >= self.window:
            hits.popleft()
        if len(hits) < self.limit:
            hits.append(now)
            return Decision(True)

        warn = key not in self._warned or now - self._warned[key] >= self.warn_every
        if warn:
            self._warned[key] = now
        return Decision(False, warn)

    def cleanup(self, now: float) -> None:
        """Forget users who have been quiet, so memory does not grow forever."""
        for key in [k for k, hits in self._hits.items() if not hits or now - hits[-1] >= self.window]:
            del self._hits[key]
        for key in [k for k, at in self._warned.items() if now - at >= self.warn_every]:
            del self._warned[key]
