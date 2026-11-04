"""kulira campaign validate|run|stop|report"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from .log import verify_log
from .orchestrator import Orchestrator
from .scenario import load_scenario, ScenarioError

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="kulira"); sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("campaign"); csub = c.add_subparsers(dest="sub", required=True)
    v = csub.add_parser("validate"); v.add_argument("scenario")
    r = csub.add_parser("run"); r.add_argument("scenario"); r.add_argument("--dry-run", action="store_true"); r.add_argument("--out")
    s = csub.add_parser("stop"); s.add_argument("--run", required=True)
    rp = csub.add_parser("report"); rp.add_argument("--run", required=True)
    args = p.parse_args(argv)
    try:
        if args.sub == "validate":
            s = load_scenario(args.scenario); print(f"OK {s.id} seed={s.seed} plane={s.plane} attacks={len(s.attacks)}"); return 0
        if args.sub == "run":
            s = load_scenario(args.scenario)
            out = Path(args.out) if args.out else Path("validation/kulira") / f"{s.id}-{s.seed}"
            report = Orchestrator().run(s, out, dry_run=args.dry_run or not s.authorised)
            print(json.dumps(report)); return 0 if report["state"] == "COMPLETED" else 2
        if args.sub == "stop":
            Path(args.run).mkdir(parents=True, exist_ok=True); (Path(args.run) / "STOP").write_text("stop\n"); print(f"STOP written {args.run}"); return 0
        if args.sub == "report":
            run = Path(args.run); entries = verify_log(run / "attacks.jsonl")
            report = json.loads((run / "report.json").read_text()); report["log_verified"] = True; report["log_entries"] = len(entries)
            print(json.dumps(report, indent=2)); return 0
    except (ScenarioError, Exception) as e:
        print(f"error: {e}", file=sys.stderr); return 1
    return 0

if __name__ == "__main__": raise SystemExit(main())
