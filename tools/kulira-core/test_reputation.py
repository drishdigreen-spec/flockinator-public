from kulira_core.reputation import generate_sequence, run_reputation, score_sequence

def test_deterministic():
    assert score_sequence(generate_sequence(2), "REP") == score_sequence(generate_sequence(2), "REP")

def test_reputation_separates_colluders():
    out = run_reputation(range(20))
    assert out["REP"]["rep_colluders"] < out["REP"]["rep_honest"]

def test_second_half_dangerous_reduced():
    out = run_reputation(range(20))
    assert out["REP"]["dangerous_second"] < out["E"]["dangerous_second"]

def test_probation_worsens_cold_start_measured():
    # Pre-registered H-M1 was FALSIFIED: probationary full-weight
    # sightings prolong easy commits (81 vs 37 first-half dangerous
    # on dev). Pin the measured direction so this stays a result,
    # not a claim that probation helps.
    out = run_reputation(range(20))
    assert out["REP-P"]["dangerous_first"] > out["E"]["dangerous_first"]
    assert out["REP-P"]["dangerous_second"] < out["E"]["dangerous_second"]
