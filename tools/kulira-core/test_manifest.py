import json
from kulira_core.manifest import build_manifest, build_report
from kulira_core.scenario import parse_scenario
LABELS={f"{r}{c}" for r in "ABCD" for c in range(1,5)}
def test_manifest_and_report_shape():
    s=parse_scenario({"id":"x","seed":7,"plane":"app","targets":["lab"],"attacks":[{"module":"kulira-disrupt","action":"drop","at_s":0,"duration_s":1,"intensity":1}]}, labels=LABELS)
    m=build_manifest(s, run_id="x-7", dry_run=True, state="COMPLETED")
    assert m["baseline"]["before"] is None and m["dry_run"]
    r=build_report(s, state="COMPLETED", actions=[], log_verified=True, management_health_ok=True, dry_run=True)
    assert r["metrics"]["nodes_deceived"]==[] and r["metrics"]["time_to_detect_s"] is None
