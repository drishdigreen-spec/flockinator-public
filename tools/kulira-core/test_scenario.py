import json
import pytest
from kulira_core.scenario import ScenarioError, parse_scenario, load_scenario, expand_schedule

LABELS = {f"{r}{c}" for r in "ABCD" for c in range(1, 5)}

def base(**over):
    data = {
        "id": "false-beacon-001", "seed": 271828, "plane": "app",
        "targets": ["B2"], "authorised": False,
        "attacks": [{"module": "kulira-deceive", "action": "false-observation",
                     "at_s": 30, "duration_s": 60, "intensity": 1}],
        "limits": {"max_duration_s": 600, "intensity_cap": 3,
                   "require_management_health": True},
    }
    data.update(over)
    return data

def test_valid_scenario_parses_and_is_frozen():
    s = parse_scenario(base(), labels=LABELS)
    assert s.id == "false-beacon-001" and s.seed == 271828 and s.plane == "app"
    assert s.targets == ("B2",) and s.attacks[0].module == "kulira-deceive"
    with pytest.raises(Exception):
        s.seed = 1  # frozen

def test_missing_seed_rejected():
    d = base(); del d["seed"]
    with pytest.raises(ScenarioError, match="seed"): parse_scenario(d, labels=LABELS)

def test_unknown_module_rejected():
    d = base(attacks=[{"module": "kulira-nope", "action": "x", "at_s": 0, "duration_s": 1, "intensity": 1}])
    with pytest.raises(ScenarioError, match="unknown module"): parse_scenario(d, labels=LABELS)

def test_unknown_plane_rejected():
    with pytest.raises(ScenarioError, match="unknown plane"): parse_scenario(base(plane="magic"), labels=LABELS)

def test_bad_label_rejected():
    with pytest.raises(ScenarioError, match="unknown target label"): parse_scenario(base(targets=["Z9"]), labels=LABELS)

def test_lab_target_allowed():
    s = parse_scenario(base(targets=["lab"]), labels=LABELS)
    assert s.targets == ("lab",)

def test_rf_without_gadget_ref_rejected():
    with pytest.raises(ScenarioError, match="gadget"): parse_scenario(base(plane="rf"), labels=LABELS)

def test_rf_with_gadget_ref_allowed():
    s = parse_scenario(base(plane="rf", gadget_ref="docs/inventory/rf-gadgets.csv#hackrf-1"), labels=LABELS)
    assert s.gadget_ref.startswith("docs/inventory/")

def test_intensity_over_cap_rejected():
    d = base(attacks=[{"module": "kulira-disrupt", "action": "drop", "at_s": 0, "duration_s": 1, "intensity": 4}])
    with pytest.raises(ScenarioError, match="intensity"): parse_scenario(d, labels=LABELS)

def test_duration_over_limit_rejected():
    d = base(attacks=[{"module": "kulira-disrupt", "action": "drop", "at_s": 590, "duration_s": 20, "intensity": 1}])
    with pytest.raises(ScenarioError, match="duration"): parse_scenario(d, labels=LABELS)

def test_expand_schedule_deterministic_and_sorted():
    d = base(attacks=[
        {"module": "kulira-disrupt", "action": "drop", "at_s": 50, "duration_s": 5, "intensity": 1},
        {"module": "kulira-spoof", "action": "replay", "at_s": 10, "duration_s": 5, "intensity": 1}])
    s = parse_scenario(d, labels=LABELS)
    a, b = expand_schedule(s), expand_schedule(s)
    assert a == b and [x.at_s for x in a] == [10, 50]

def test_load_scenario_json(tmp_path):
    p = tmp_path / "s.json"; p.write_text(json.dumps(base()))
    assert load_scenario(p, labels=LABELS).id == "false-beacon-001"
