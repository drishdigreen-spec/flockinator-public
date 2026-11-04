"""Seeded campaign orchestrator (dry-run executes schedule with no real delay)."""
from __future__ import annotations
import json
from pathlib import Path
from .actuator import FakeActuator
from .health import AlwaysHealthyProbe
from .log import AttackLog, verify_log
from .manifest import build_manifest, build_report
from .safety import SafetyGate, SafetyError
from .scenario import expand_schedule

class Orchestrator:
    def run(self, scenario, out_dir, dry_run: bool = True, health=None) -> dict:
        out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
        health = health or AlwaysHealthyProbe()
        actuator = FakeActuator(scenario.plane); gate = SafetyGate(scenario, actuator, dry_run=dry_run)
        log = AttackLog(out / "attacks.jsonl")
        run_id = f"{scenario.id}-{scenario.seed}"
        actions, state = [], "COMPLETED"
        def healthy():
            try: return bool(health.check())
            except Exception: return False
        health_ok = healthy()
        if scenario.limits.require_management_health and not health_ok:
            state = "ABORTED"; log.append("abort", {"reason": "management health check failed before start"})
        elif (out / "STOP").exists():
            state = "ABORTED"; log.append("abort", {"reason": "stop file present before start"})
        else:
            log.append("start", {"scenario_id": scenario.id, "seed": scenario.seed, "dry_run": dry_run})
            with gate.run_lock():
                for action in expand_schedule(scenario):
                    if (out / "STOP").exists(): gate.request_stop("stop file"); state = "ABORTED"; break
                    if scenario.limits.require_management_health and not healthy():
                        health_ok = False; state = "ABORTED"
                        log.append("abort", {"reason": "management health check failed mid-run"}); break
                    try: gate.fire(action)
                    except SafetyError as e:
                        state = "ABORTED"; log.append("abort", {"reason": str(e)}); break
                    rec = {"module": action.module, "action": action.action, "at_s": action.at_s,
                           "duration_s": action.duration_s, "intensity": action.intensity, "plane": action.plane}
                    actions.append(rec); log.append("fire", rec)
            log.append("end", {"state": state})
        try: verified = bool(verify_log(out / "attacks.jsonl")) or state == "ABORTED"
        except Exception: verified = False
        manifest = build_manifest(scenario, run_id, dry_run, state)
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        report = build_report(scenario, state, actions, verified, health_ok, dry_run)
        (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        return report
