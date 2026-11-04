"""Management-health probe interface (fake for tests, no live wiring without gate)."""
from __future__ import annotations
from typing import Protocol

class HealthProbe(Protocol):
    def check(self) -> bool: ...

class FakeHealthProbe:
    def __init__(self, results: list[bool]): self._results = list(results) or [True]
    def check(self) -> bool: return self._results.pop(0) if len(self._results) > 1 else self._results[0]

class AlwaysHealthyProbe:
    def check(self) -> bool: return True
