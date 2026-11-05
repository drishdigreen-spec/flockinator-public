from kulira_core.sybil import generate_sybil, run_sybil, score_sybil

def test_deterministic():
    assert score_sybil(generate_sybil(1, 5), "REP") == score_sybil(generate_sybil(1, 5), "REP")

def test_rotation_erases_reputation_advantage():
    out = run_sybil(range(20), rotations=(None, 5))
    assert out["fixed"]["REP"]["dangerous_second"] < out["fixed"]["E"]["dangerous_second"]
    assert out["5"]["REP"]["dangerous_second"] >= 0.9 * out["5"]["E"]["dangerous_second"]
