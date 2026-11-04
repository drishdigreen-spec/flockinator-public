from kulira_core.actuator import FakeActuator
from kulira_core.scenario import AttackAction

def test_fake_records_and_stop_idempotent():
    a=FakeActuator("app"); act=AttackAction("kulira-disrupt","drop",0,5,1,"app")
    a.arm(act); a.fire(act); a.stop("done"); a.stop("done")
    assert [c[0] for c in a.calls]==["arm","fire","stop","stop"] and a.stopped
