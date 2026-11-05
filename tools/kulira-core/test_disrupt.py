from kulira_core.actuator import FakeActuator
from kulira_core.disrupt import DisruptActuator
from kulira_core.scenario import AttackAction

def act(action="drop", intensity=1):
    return AttackAction("kulira-disrupt", action, 0, 5, intensity, "app")

def test_drop_suppresses_fire_deterministically():
    inner=FakeActuator("app"); d=DisruptActuator(inner, seed=7, drop_rate=1.0)
    d.arm(act()); d.fire(act())
    assert [c[0] for c in inner.calls]==["arm"] and d.stats()["dropped"]==1

def test_no_drop_passes_through():
    inner=FakeActuator("app"); d=DisruptActuator(inner, seed=7, drop_rate=0.0)
    d.fire(act()); assert [c[0] for c in inner.calls]==["fire"] and d.stats()["delivered"]==1

def test_duplicate_fires_twice():
    inner=FakeActuator("app"); d=DisruptActuator(inner, seed=1, drop_rate=0.0, duplicate=True)
    d.fire(act("duplicate")); assert [c[0] for c in inner.calls]==["fire","fire"]

def test_delay_records_without_sleeping():
    inner=FakeActuator("app"); d=DisruptActuator(inner, seed=1, drop_rate=0.0, delay_s=2.5)
    d.fire(act("delay")); assert d.stats()["delayed"]==1 and d.stats()["total_delay_s"]==2.5

def test_seeded_drop_sequence_reproducible():
    def seq():
        inner=FakeActuator("app"); d=DisruptActuator(inner, seed=42, drop_rate=0.5)
        for _ in range(10): d.fire(act())
        return d.stats()
    assert seq()==seq()
