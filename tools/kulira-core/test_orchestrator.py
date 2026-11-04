import json
from kulira_core.orchestrator import Orchestrator
from kulira_core.health import FakeHealthProbe
from kulira_core.scenario import parse_scenario
LABELS={f"{r}{c}" for r in "ABCD" for c in range(1,5)}
def scen():
    return parse_scenario({"id":"false-beacon-001","seed":42,"plane":"app","targets":["lab"],"authorised":False,
      "attacks":[{"module":"kulira-deceive","action":"false-observation","at_s":30,"duration_s":60,"intensity":1},
                 {"module":"kulira-disrupt","action":"drop","at_s":10,"duration_s":5,"intensity":1}],
      "limits":{"max_duration_s":600,"intensity_cap":3}}, labels=LABELS)

def test_dry_run_end_to_end(tmp_path):
    r=Orchestrator().run(scen(), tmp_path/"run", dry_run=True, health=FakeHealthProbe([True,True,True]))
    assert r["state"]=="COMPLETED" and r["dry_run"]
    assert (tmp_path/"run"/"manifest.json").exists()
    assert json.loads((tmp_path/"run"/"report.json").read_text())["log_verified"]

def test_deterministic_schedule(tmp_path):
    r1=Orchestrator().run(scen(), tmp_path/"a", dry_run=True, health=FakeHealthProbe([True]*5))
    r2=Orchestrator().run(scen(), tmp_path/"b", dry_run=True, health=FakeHealthProbe([True]*5))
    assert [x["action"] for x in r1["actions"]]==[x["action"] for x in r2["actions"]]==["drop","false-observation"]

def test_health_failure_refuses_start(tmp_path):
    r=Orchestrator().run(scen(), tmp_path/"run", dry_run=True, health=FakeHealthProbe([False]))
    assert r["state"]=="ABORTED" and r["actions"]==[]

def test_health_failure_mid_run_aborts(tmp_path):
    r=Orchestrator().run(scen(), tmp_path/"run", dry_run=True, health=FakeHealthProbe([True,False]))
    assert r["state"]=="ABORTED"

def test_stop_file_aborts(tmp_path):
    out=tmp_path/"run"; out.mkdir(); (out/"STOP").write_text("x")
    r=Orchestrator().run(scen(), out, dry_run=True, health=FakeHealthProbe([True]*5))
    assert r["state"]=="ABORTED" and r["actions"]==[]
