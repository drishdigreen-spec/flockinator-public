from kulira_core.observe import score_run
def test_score_run_counts_deception():
    events=[{"node":"C1","kind":"accepted_false","t":70},{"node":"D1","kind":"rejected_false","t":12},{"node":"C1","kind":"recovered","t":130}]
    s=score_run(events, attack_start_s=10, targets=["C1","D1"])
    assert s["nodes_deceived"]==["C1"] and s["time_to_detect_s"]==2 and s["recovery_time_s"]==60
