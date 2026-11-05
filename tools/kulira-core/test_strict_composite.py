from kulira_core.composite import run_factorial

def test_strict_composite_gate_on_fresh_seeds():
    dev = run_factorial(range(400, 420)); ev = run_factorial(range(500, 510))
    for out in (dev, ev):
        s, c = out["L-T0"], out["L-T1"]
        assert s["dangerous_post"] < c["dangerous_post"]          # H-R1
        assert c["mean_recall"] - s["mean_recall"] <= 0.20        # H-R2
