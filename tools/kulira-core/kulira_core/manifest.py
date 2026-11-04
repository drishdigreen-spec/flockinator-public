"""Run manifest and report builders."""
from __future__ import annotations

def build_manifest(scenario, run_id: str, dry_run: bool, state: str) -> dict:
    return {"run_id": run_id, "scenario_id": scenario.id, "seed": scenario.seed,
            "plane": scenario.plane, "targets": list(scenario.targets), "dry_run": dry_run,
            "state": state, "gadget_ref": scenario.gadget_ref,
            "baseline": {"before": None, "after": None,
                         "note": "dry-run" if dry_run else "pending live health proof"}}

def build_report(scenario, state: str, actions: list, log_verified: bool,
                 management_health_ok: bool, dry_run: bool) -> dict:
    return {"scenario_id": scenario.id, "seed": scenario.seed, "state": state, "dry_run": dry_run,
            "log_verified": log_verified, "management_health_ok": management_health_ok,
            "actions": actions,
            "metrics": {"time_to_detect_s": None, "nodes_deceived": [],
                        "propagation_depth": 0, "recovery_time_s": None}}
