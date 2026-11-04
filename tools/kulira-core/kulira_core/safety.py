"""SafetyGate: the only path to an actuator."""
from __future__ import annotations
import contextlib, threading

class SafetyError(RuntimeError): pass

class SafetyGate:
    def __init__(self, scenario, actuator, dry_run: bool = True):
        self.scenario = scenario; self.actuator = actuator; self.dry_run = dry_run
        self._stop = threading.Event(); self._lock = threading.Lock(); self.stop_reason = None
    @property
    def stopped(self): return self._stop.is_set()
    def request_stop(self, reason: str = "operator"):
        self.stop_reason = reason; self._stop.set()
        with contextlib.suppress(Exception): self.actuator.stop(f"kill-switch: {reason}")
    @contextlib.contextmanager
    def run_lock(self):
        if not self._lock.acquire(blocking=False): raise SafetyError("concurrent campaign rejected: one-attack lock held")
        try: yield
        finally: self._lock.release()
    def fire(self, action) -> None:
        if self._stop.is_set(): raise SafetyError(f"kill-switch active: {self.stop_reason}")
        if not self.dry_run and not self.scenario.authorised:
            raise SafetyError("live run not authorised: scenario authorised is false")
        if action.intensity > self.scenario.limits.intensity_cap: raise SafetyError("intensity over cap")
        self.actuator.arm(action)
        if self._stop.is_set(): raise SafetyError(f"kill-switch active: {self.stop_reason}")
        self.actuator.fire(action)
    def stop(self, reason: str): self.request_stop(reason)
