"""kulira-disrupt: app-plane friction (drop/delay/duplicate) over an actuator.

Deterministic and seeded; delay is recorded, never slept, in this lab
actuator - timing enforcement belongs to the transport adapter that
wraps real delivery. Network jamming devices are never used.
"""
from __future__ import annotations
import random

class DisruptActuator:
    def __init__(self, inner, seed: int = 0, drop_rate: float = 0.0,
                 duplicate: bool = False, delay_s: float = 0.0):
        if not 0.0 <= drop_rate <= 1.0:
            raise ValueError("drop_rate out of range 0..1")
        self.inner = inner; self.plane = getattr(inner, "plane", "app")
        self._rng = random.Random(seed); self.drop_rate = drop_rate
        self.duplicate = duplicate; self.delay_s = float(delay_s)
        self._stats = {"dropped": 0, "delivered": 0, "delayed": 0, "total_delay_s": 0.0, "duplicated": 0}
    def arm(self, action): self.inner.arm(action)
    def fire(self, action):
        if self._rng.random() < self.drop_rate:
            self._stats["dropped"] += 1; return
        if self.delay_s > 0:
            self._stats["delayed"] += 1; self._stats["total_delay_s"] += self.delay_s
        self.inner.fire(action); self._stats["delivered"] += 1
        if self.duplicate:
            self.inner.fire(action); self._stats["duplicated"] += 1
    def stop(self, reason: str): self.inner.stop(reason)
    def stats(self) -> dict: return dict(self._stats)
