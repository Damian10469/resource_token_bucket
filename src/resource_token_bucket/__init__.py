"""Resource Token Bucket.

A token bucket that refills at a fixed rate and consumes tokens on
demand, returning booleans for flow control under load.
"""

from .core import TokenBucket

__all__ = ["TokenBucket"]
