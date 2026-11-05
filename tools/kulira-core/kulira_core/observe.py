"""kulira-observe (core scoring): who believed what, and how fast it healed."""
from __future__ import annotations

def score_run(events, attack_start_s: float, targets) -> dict:
    deceived = sorted({e["node"] for e in events if e["kind"] == "accepted_false"})
    detections = [e["t"] for e in events if e["kind"] in ("rejected_false", "detected")]
    recoveries = {e["node"]: e["t"] for e in events if e["kind"] == "recovered"}
    return {
        "targets": list(targets),
        "nodes_deceived": deceived,
        "time_to_detect_s": (min(detections) - attack_start_s) if detections else None,
        "propagation_depth": len(deceived),
        "recovery_time_s": (max(recoveries.values()) - attack_start_s) if recoveries else None,
    }
