from kulira_core.rescue import run_rescue_cycle

def test_real_survivor_reaches_dig_with_two_modalities():
    r=run_rescue_cycle(seed=1, fabricated=False)
    assert r["dig"] is True and r["strength"]=="strong"

def test_fabricated_heat_plus_copies_never_digs():
    r=run_rescue_cycle(seed=1, fabricated=True)
    assert r["dig"] is False and r["independent_modalities"]<2

def test_cycle_deterministic():
    assert run_rescue_cycle(seed=7, fabricated=True)==run_rescue_cycle(seed=7, fabricated=True)
