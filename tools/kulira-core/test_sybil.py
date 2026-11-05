from kulira_core.sybil import generate_sybil, run_sybil, score_sybil

def test_deterministic():
    assert score_sybil(generate_sybil(1, 5), "REP") == score_sybil(generate_sybil(1, 5), "REP")

def test_rotation_erases_reputation_advantage():
    out = run_sybil(range(20), rotations=(None, 5))
    assert out["fixed"]["REP"]["dangerous_second"] < out["fixed"]["E"]["dangerous_second"]
    assert out["5"]["REP"]["dangerous_second"] >= 0.9 * out["5"]["E"]["dangerous_second"]

def test_newcomer_discount_counters_rotation():
    out = run_sybil(range(20), rotations=(5,))
    assert out["5"]["REP-N"]["dangerous_second"] < out["5"]["REP"]["dangerous_second"]

def test_newcomer_discount_strangles_recall_measured():
    # H-O3 FALSIFIED: at start=0.5 with REP thresholds unchanged,
    # almost nothing reaches the weighted commit bar. Pin it.
    out = run_sybil(range(20), rotations=(5,))
    assert out["5"]["REP-N"]["mean_recall"] < 0.1
