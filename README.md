# Resource Token Bucket

A token bucket that refills at a fixed rate and consumes tokens on demand, returning booleans for flow control under load.

```python
from resource_token_bucket import TokenBucket

bucket = TokenBucket(capacity=5.0, refill_rate=2.0)

if bucket.try_consume():
    print("Request handled")
else:
    print("Request rejected")
```

## Why this exists

The token bucket is a simple algorithm for rate limiting or admission control. It answers the question: "can I process this request right now, without exceeding a sustainable rate?" The bucket starts full, so short bursts are allowed, but the long-run rate cannot exceed the configured refill rate.

This library intentionally keeps the API minimal. There is no blocking wait, no burst-size parameter beyond capacity, and no token reservation. The trade-off is simplicity and predictability: callers that need to wait should implement that themselves using the boolean result.

## Edge cases

- The bucket starts full, so the first `capacity` calls to `try_consume` succeed immediately even if no time has passed.
- A partial token (for example, 0.5 tokens after half a second at rate 1.0) is not enough to consume; the call returns `False` and the partial token remains.
- If the clock moves backwards or freezes, no refill is credited for that interval. The bucket keeps its last known state.
- The clock is injected via a `clock` constructor argument so tests can be deterministic. By default, `time.monotonic` is used.

## Exports

- `TokenBucket` (class)
  - `__init__(capacity, refill_rate, *, clock=None)`
  - `try_consume() -> bool`
  - `available_tokens() -> float`
  - `capacity` (property)
  - `refill_rate` (property)
