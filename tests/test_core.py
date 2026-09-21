import unittest

from resource_token_bucket import TokenBucket


class FakeClock:
    """A deterministic, manually advanced clock."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TokenBucketInitTests(unittest.TestCase):
    def test_positive_capacity_and_rate(self) -> None:
        bucket = TokenBucket(2.0, 1.0)
        self.assertEqual(bucket.capacity, 2.0)
        self.assertEqual(bucket.refill_rate, 1.0)

    def test_zero_capacity_raises(self) -> None:
        with self.assertRaises(ValueError):
            TokenBucket(0.0, 1.0)

    def test_negative_capacity_raises(self) -> None:
        with self.assertRaises(ValueError):
            TokenBucket(-1.0, 1.0)

    def test_zero_refill_rate_raises(self) -> None:
        with self.assertRaises(ValueError):
            TokenBucket(1.0, 0.0)

    def test_negative_refill_rate_raises(self) -> None:
        with self.assertRaises(ValueError):
            TokenBucket(1.0, -1.0)

    def test_non_callable_clock_raises(self) -> None:
        with self.assertRaises(ValueError):
            TokenBucket(1.0, 1.0, clock=42)  # type: ignore[arg-type]


class TokenBucketConsumeTests(unittest.TestCase):
    def test_starts_full(self) -> None:
        clock = FakeClock()
        bucket = TokenBucket(3.0, 1.0, clock=clock)
        self.assertEqual(bucket.available_tokens(), 3.0)

    def test_consume_from_full_bucket(self) -> None:
        clock = FakeClock()
        bucket = TokenBucket(2.0, 1.0, clock=clock)
        self.assertTrue(bucket.try_consume())
        self.assertTrue(bucket.try_consume())

    def test_consume_when_empty_fails(self) -> None:
        clock = FakeClock()
        bucket = TokenBucket(1.0, 1.0, clock=clock)
        self.assertTrue(bucket.try_consume())
        self.assertFalse(bucket.try_consume())

    def test_refill_over_time(self) -> None:
        clock = FakeClock()
        bucket = TokenBucket(2.0, 1.0, clock=clock)

        # Drain the bucket.
        self.assertTrue(bucket.try_consume())
        self.assertTrue(bucket.try_consume())
        self.assertFalse(bucket.try_consume())

        # Advance one second and consume one refilled token.
        clock.advance(1.0)
        self.assertTrue(bucket.try_consume())
        self.assertFalse(bucket.try_consume())

    def test_capacity_is_capped(self) -> None:
        clock = FakeClock()
        bucket = TokenBucket(1.0, 10.0, clock=clock)

        # Advance well beyond one capacity worth of refill time.
        clock.advance(5.0)
        self.assertEqual(bucket.available_tokens(), 1.0)

    def test_partial_token_does_not_allow_consume(self) -> None:
        clock = FakeClock()
        bucket = TokenBucket(1.0, 1.0, clock=clock)

        # Drain the bucket.
        self.assertTrue(bucket.try_consume())

        # Only half a token has refilled.
        clock.advance(0.5)
        self.assertFalse(bucket.try_consume())
        # No token consumed, so the half token remains.
        self.assertAlmostEqual(bucket.available_tokens(), 0.5)

    def test_non_monotonic_clock_does_not_refill(self) -> None:
        clock = FakeClock(10.0)
        bucket = TokenBucket(1.0, 1.0, clock=clock)

        self.assertTrue(bucket.try_consume())

        # Move clock backwards.
        clock.now = 5.0
        self.assertFalse(bucket.try_consume())

    def test_available_tokens_does_not_consume(self) -> None:
        clock = FakeClock()
        bucket = TokenBucket(2.0, 1.0, clock=clock)

        self.assertEqual(bucket.available_tokens(), 2.0)
        self.assertEqual(bucket.available_tokens(), 2.0)


if __name__ == "__main__":
    unittest.main()
