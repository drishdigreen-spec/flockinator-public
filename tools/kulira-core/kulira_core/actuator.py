"""Actuator contract; core never transmits, fakes record calls."""
from __future__ import annotations
from typing import Protocol

class Actuator(Protocol):
    plane: str
    def arm(self, action) -> None: ...
    def fire(self, action) -> None: ...
    def stop(self, reason: str) -> None: ...

class FakeActuator:
    def __init__(self, plane: str = "app"):
        self.plane = plane; self.calls: list[tuple] = []; self.stopped = False
    def arm(self, action): self.calls.append(("arm", action.action))
    def fire(self, action): self.calls.append(("fire", action.action))
    def stop(self, reason: str): self.calls.append(("stop", reason)); self.stopped = True
