import pytest
from kulira_core.actuator import FakeActuator
from kulira_core.safety import SafetyGate, SafetyError
from kulira_core.scenario import parse_scenario
LABELS={f"{r}{c}" for r in "ABCD" for c in range(1,5)}
def scen(**o):
    d={"id":"t","seed":1,"plane":"app","targets":["B2"],"authorised":False,
       "attacks":[{"module":"kulira-disrupt","action":"drop","at_s":0,"duration_s":5,"intensity":1}],
       "limits":{"max_duration_s":600,"intensity_cap":3}}
    d.update(o); return parse_scenario(d, labels=LABELS)

def test_gate_fires_through_actuator():
    a=FakeActuator("app"); g=SafetyGate(scen(), a, dry_run=True)
    g.fire(scen().attacks[0]); assert [c[0] for c in a.calls]==["arm","fire"]

def test_unauthorised_live_rejected():
    a=FakeActuator("app"); g=SafetyGate(scen(), a, dry_run=False)
    with pytest.raises(SafetyError, match="authorised"): g.fire(scen().attacks[0])
    assert a.calls==[]

def test_kill_switch_stops_and_blocks():
    a=FakeActuator("app"); g=SafetyGate(scen(), a, dry_run=True)
    g.request_stop("operator")
    with pytest.raises(SafetyError, match="kill-switch"): g.fire(scen().attacks[0])
    assert a.stopped and g.stopped

def test_second_concurrent_run_rejected():
    a=FakeActuator("app"); g=SafetyGate(scen(), a, dry_run=True)
    with g.run_lock():
        with pytest.raises(SafetyError, match="concurrent"): 
            with g.run_lock(): pass
