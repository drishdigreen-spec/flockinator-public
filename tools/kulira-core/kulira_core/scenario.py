"""Scenario schema, validation and deterministic schedule expansion."""
from __future__ import annotations
import json, random
from dataclasses import dataclass
from pathlib import Path

ALLOWED_MODULES = frozenset({"kulira-disrupt", "kulira-spoof", "kulira-deceive", "kulira-observe"})
# Structural guard: actions are allowlisted per module. A proposer
# (human or model) cannot invent an action name - renamed variants of
# protected-plane actions fail because they are not on the list, not
# because a substring matched.
ACTION_ALLOWLIST = {
    "kulira-disrupt": frozenset({"drop", "delay", "duplicate", "reorder", "partition", "contention", "cochannel-contention", "inject_latency_spike", "drop_ack_packets"}),
    "kulira-spoof": frozenset({"forge", "duplicate_heartbeat", "replay", "impersonate", "sybil", "duplicate_label"}),
    "kulira-deceive": frozenset({"false-observation", "false-observation-peer-reports", "false_observation", "contradictory-report", "false-beacon"}),
    "kulira-observe": frozenset({"score", "measure"}),
}
PLANES = frozenset({"app", "link", "rf"})
DEFAULT_LABELS = frozenset(f"{r}{c}" for r in "ABCD" for c in range(1, 5))

class ScenarioError(ValueError):
    pass

@dataclass(frozen=True)
class AttackAction:
    module: str
    action: str
    at_s: float
    duration_s: float
    intensity: int
    plane: str | None = None

@dataclass(frozen=True)
class Limits:
    max_duration_s: float = 600.0
    intensity_cap: int = 3
    require_management_health: bool = True

@dataclass(frozen=True)
class Scenario:
    id: str
    seed: int
    plane: str
    targets: tuple[str, ...]
    attacks: tuple[AttackAction, ...]
    limits: Limits = Limits()
    authorised: bool = False
    gadget_ref: str | None = None

def parse_scenario(data: dict, labels=DEFAULT_LABELS) -> Scenario:
    if not isinstance(data, dict):
        raise ScenarioError("scenario must be an object")
    sid = data.get("id")
    if not sid or not isinstance(sid, str):
        raise ScenarioError("missing scenario id")
    if "seed" not in data or isinstance(data.get("seed"), bool) or not isinstance(data.get("seed"), int):
        raise ScenarioError("missing or invalid seed")
    plane = data.get("plane")
    if plane not in PLANES:
        raise ScenarioError(f"unknown plane: {plane!r}")
    lim_raw = data.get("limits") or {}
    limits = Limits(
        max_duration_s=float(lim_raw.get("max_duration_s", 600)),
        intensity_cap=int(lim_raw.get("intensity_cap", 3)),
        require_management_health=bool(lim_raw.get("require_management_health", True)),
    )
    if not (1 <= limits.intensity_cap <= 3):
        raise ScenarioError("intensity_cap out of range 1..3")
    targets = data.get("targets")
    if not targets or not isinstance(targets, list):
        raise ScenarioError("missing targets")
    for t in targets:
        if t != "lab" and t not in labels:
            raise ScenarioError(f"unknown target label: {t}")
    attacks_raw = data.get("attacks")
    if not attacks_raw or not isinstance(attacks_raw, list):
        raise ScenarioError("missing attacks")
    attacks = []
    for raw in attacks_raw:
        module = raw.get("module")
        if module not in ALLOWED_MODULES:
            raise ScenarioError(f"unknown module: {module}")
        intensity = raw.get("intensity")
        if isinstance(intensity, bool) or not isinstance(intensity, int) or not (1 <= intensity <= limits.intensity_cap):
            raise ScenarioError(f"intensity over cap or invalid: {intensity!r}")
        at_s, dur = float(raw.get("at_s", -1)), float(raw.get("duration_s", -1))
        if at_s < 0 or dur <= 0 or at_s + dur > limits.max_duration_s:
            raise ScenarioError("attack duration exceeds max_duration_s limit")
        aplane = raw.get("plane", plane)
        if aplane not in PLANES:
            raise ScenarioError(f"unknown plane: {aplane!r}")
        action_name = str(raw.get("action", ""))
        if action_name not in ACTION_ALLOWLIST[module]:
            raise ScenarioError(f"action not allowlisted for {module}: {action_name} (structural guard; protected-plane actions have no allowlist entry)")
        attacks.append(AttackAction(module, action_name, at_s, dur, intensity, aplane))
    gadget_ref = data.get("gadget_ref")
    needs_gadget = plane == "rf" or any(a.plane == "rf" for a in attacks)
    if needs_gadget and not gadget_ref:
        raise ScenarioError("rf plane requires gadget inventory ref (gadget_ref)")
    return Scenario(sid, data["seed"], plane, tuple(targets), tuple(attacks),
                    limits, bool(data.get("authorised", False)), gadget_ref)

def expand_schedule(scenario: Scenario) -> tuple[AttackAction, ...]:
    """Deterministic schedule: sorted by time, ties broken stably; seed recorded, no wall-clock/RNG leakage."""
    rng = random.Random(scenario.seed)  # reserved for future seeded jitter; kept deterministic today
    _ = rng.random()
    return tuple(sorted(scenario.attacks, key=lambda a: (a.at_s, a.module, a.action)))

def load_scenario(path, labels=DEFAULT_LABELS) -> Scenario:
    return parse_scenario(json.loads(Path(path).read_text()), labels=labels)
