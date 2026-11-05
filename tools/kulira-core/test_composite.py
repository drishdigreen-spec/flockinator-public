from kulira_core.composite import generate_world, run_composite, score_world

def test_deterministic():
    assert score_world(generate_world(3), "COMP") == score_world(generate_world(3), "COMP")

def test_forged_origin_stays_zero_under_both():
    out = run_composite(range(20))
    assert out["E"]["forged_dangerous"] == 0 and out["COMP"]["forged_dangerous"] == 0

def test_composite_reduces_post_betrayal_dangerous():
    out = run_composite(range(20))
    assert out["COMP"]["dangerous_post"] < out["E"]["dangerous_post"]

def test_bundled_policies_differ_at_unit_trust():
    # Correction regression (composite-defence-correction.md):
    # 2 survivor + 1 hazard at unit trust commits under COMP's
    # thresholds but abstains under E's. The policies are bundles;
    # the published comparison does not isolate learned weights.
    world = [{"contact": 0, "truth": "hazard", "forged_id": None,
              "reports": [("s1", "A1", "ir", "survivor", False),
                          ("s2", "A2", "co2", "survivor", False),
                          ("s3", "A3", "sound", "hazard", False)]}]
    world2 = [dict(world[0], truth="survivor")]
    assert score_world(world2, "E")["committed"] == 0
    assert score_world(world2, "COMP")["committed"] == 1
