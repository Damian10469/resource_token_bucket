"""Core implementation of the Resource Token Bucket.

The bucket has a capacity and a refill rate. Tokens are added at a
constant rate, and a request consumes one token. A request succeeds
only if a token is available at that instant.

A clock function is injected so tests can be deterministic.
"""

from __future__ import annotations

from typing import Callable


class TokenBucket:
    """A fixed-capacity token bucket with a linear refill rate.

    The bucket is initialised full. ``try_consume`` removes one token if
    available and returns ``True``; otherwise it returns ``False`` and
    leaves the bucket unchanged.

    Time is obtained from ``clock``, which must return a monotonically
    non-decreasing number of seconds. The default is ``time.monotonic``.

    Refills are calculated lazily: on every call to ``try_consume`` the
    bucket first credits itself with the tokens that would have arrived
    since the last update, capped at capacity.
    """

    def __init__(
        self,
        capacity: float,
        refill_rate: float,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        """Initialise the bucket.

        Args:
            capacity: Maximum number of tokens the bucket can hold.
                Must be positive.
            refill_rate: Tokens added per second. Must be positive.
            clock: Optional callable returning the current time in
                seconds. Defaults to ``time.monotonic``.

        Raises:
            ValueError: if ``capacity`` or ``refill_rate`` is not
                positive, or if ``clock`` is not callable.
        """
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_rate <= 0:
            raise ValueError("refill_rate must be positive")

        if clock is None:
            import time

            clock = time.monotonic
        elif not callable(clock):
            raise ValueError("clock must be callable")

        self._capacity = float(capacity)
        self._refill_rate = float(refill_rate)
        self._clock = clock

        # Start full.
        self._tokens = self._capacity
        self._last_update = self._clock()

    def _refill(self, now: float) -> None:
        """Credit tokens for elapsed time, capped at capacity.

        The calculation is done with floats. The monotonic clock and the
        lazy refill design keep the bucket stable over long periods.
        """
        elapsed = now - self._last_update
        if elapsed <= 0:
            # Non-monotonic or frozen clock: no refill.
            self._last_update = now
            return

        self._tokens = min(
            self._capacity,
            self._tokens + elapsed * self._refill_rate,
        )
        self._last_update = now

    def try_consume(self) -> bool:
        """Attempt to consume one token.

        Returns:
            ``True`` if a token was available and has been consumed,
            ``False`` otherwise.
        """
        now = self._clock()
        self._refill(now)

        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True

        return False

    @property
    def capacity(self) -> float:
        """The maximum number of tokens the bucket can hold."""
        return self._capacity

    @property
    def refill_rate(self) -> float:
        """The number of tokens added per second."""
        return self._refill_rate

    def available_tokens(self) -> float:
        """Return the current token count, after crediting refills.

        This method is useful for inspection but does not consume tokens.
        """
        now = self._clock()
        self._refill(now)
        return self._tokens
