"""Scorer regression: must reproduce the cycle-00 coordinator headlines.

Ground truth for expectations is the bundled cycle-00 planner capture
(docs/results/sample-runs/cycle-00-planner-capture, run 1793752408891):
8/20 found, 6/41 mislabelled (2 Enemy->Friendly), 1 check, (7,10) x14,
16/16 landed.
"""
import json
import pathlib
import tempfile
import unittest

from score import score_run

REPO = pathlib.Path(__file__).resolve().parents[2]
RUN = REPO / "docs/results/sample-runs/cycle-00-planner-capture"


class Cycle00Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = score_run(RUN)

    def test_recall(self):
        self.assertEqual(self.s["contacts_total"], 20)
        self.assertEqual(self.s["contacts_found"], 8)

    def test_mislabels(self):
        self.assertEqual(self.s["discoveries"], 41)
        self.assertEqual(self.s["mislabelled"], 6)
        self.assertEqual(self.s["mislabelled_enemy_as_friendly"], 2)

    def test_duplication(self):
        self.assertEqual(self.s["max_units_per_contact"], 14)
        self.assertEqual(self.s["most_duplicated_tile"], [7, 10])

    def test_cooperation(self):
        self.assertEqual(self.s["messages_sent"], 1)
        self.assertEqual(self.s["checks_assigned"], 1)
        self.assertEqual(self.s["checks_completed_with_discovery"], 0)
        # A1 behaviourally completed the check by scanning [5,7] on
        # turn 4; it was a negative check (signals=0, no discovery).
        self.assertEqual(self.s["checks_completed_scan"], 1)
        self.assertEqual(self.s["checks_positive"], 0)
        self.assertEqual(self.s["checks_negative"], 1)
        self.assertEqual(self.s["high_checked_completed"], 1)
        self.assertEqual(self.s["high_checks_negative"], 1)

    def test_energy_and_landings(self):
        self.assertEqual(self.s["units_landed"], 16)
        self.assertEqual(self.s["units"], 16)
        self.assertGreaterEqual(self.s["min_landed_energy"], 4)

    def test_rates_and_priorities(self):
        self.assertEqual(self.s["recall_by_priority"]["High"], 0.5)
        self.assertEqual(self.s["recall_by_priority"]["Normal"], 0.3571)
        self.assertEqual(self.s["mislabel_rate"], 0.1463)
        self.assertEqual(self.s["duplicate_discovery_rate"], 0.8049)
        self.assertEqual(self.s["reserve_floor_violations"], 0)
        self.assertEqual(self.s["scorer_version"], 3)
        self.assertEqual(self.s["committed3_contacts"], 4)
        self.assertEqual(self.s["committed3_mislabelled"], 0)
        self.assertEqual(self.s["committed3_enemy_as_friendly"], 0)

    def test_ruleset_and_source(self):
        self.assertEqual(self.s["ruleset"], "search-board-1")
        self.assertEqual(self.s["source"], "planner_simulation")


class SyntheticRunTest(unittest.TestCase):
    def test_zero_contacts_and_abandoned_waypoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            (run_dir / "director.json").write_text(json.dumps({
                "run": "synthetic", "ruleset": "test", "source": "test",
                "ground_truth": [],
            }))
            events = [
                {"unit": "A1", "turn": 0, "event": "route_assigned",
                 "tile": [7, 11], "energy": 10, "reserve": 3,
                 "route": [[6, 11], [5, 11]]},
                {"unit": "A1", "turn": 1, "event": "scan",
                 "tile": [6, 11], "energy": 2, "footprint": [[6, 11]],
                 "signals": 0},
                {"unit": "A1", "turn": 2, "event": "landed",
                 "tile": [7, 11], "energy": 1},
            ]
            (run_dir / "A1.jsonl").write_text(
                "\n".join(json.dumps(e) for e in events))
            scores = score_run(run_dir)

        self.assertIsNone(scores["recall"])
        self.assertEqual(scores["abandoned_waypoints"], 1)
        self.assertEqual(scores["units_with_abandoned_waypoints"], 1)
        self.assertEqual(scores["reserve_floor_violations"], 1)


class AsymmetricCommitTest(unittest.TestCase):
    """Cycle-06 rule: Friendly needs unanimous >=3 or >=5 with <=1
    dissent; Enemy needs >=3 strict majority; else uncommitted."""

    def _run(self, truth_kinds, sightings):
        # sightings: {contact_idx0: [reported labels]}
        tmp = tempfile.TemporaryDirectory()
        run_dir = pathlib.Path(tmp.name)
        truth = [{"pos": [i, 0], "kind": k, "priority": "Normal"}
                 for i, k in enumerate(truth_kinds)]
        (run_dir / "director.json").write_text(json.dumps({
            "run": "asym", "ruleset": "test", "source": "test",
            "ground_truth": truth}))
        events = []
        turn = 0
        for idx, labels in sightings.items():
            for lab in labels:
                turn += 1
                events.append({
                    "unit": "A1", "turn": turn, "event": "discovery",
                    "contact": idx + 1, "tile": [idx, 0],
                    "reported_label": lab})
        (run_dir / "A1.jsonl").write_text(
            "\n".join(json.dumps(e) for e in events))
        scores = score_run(run_dir)
        tmp.cleanup()
        return scores

    def test_asymmetric_commit_rules(self):
        s = self._run(
            ["Enemy", "Friendly", "Friendly", "Enemy", "Friendly"],
            {0: ["Enemy", "Enemy", "Friendly"],        # Enemy majority3 -> commit Enemy (correct)
             1: ["Friendly", "Friendly", "Enemy"],     # Friendly 2-1 majority -> NO commit
             2: ["Friendly", "Friendly", "Friendly"],  # unanimous -> commit Friendly
             3: ["Friendly", "Friendly", "Friendly"],  # unanimous wrong -> dangerous commit counts
             4: ["Friendly"] * 4 + ["Enemy"]})         # 5 sightings, 1 dissent -> commit Friendly
        self.assertEqual(s["committed_asym_contacts"], 4)
        self.assertEqual(s["committed_asym_friendly_commits"], 3)
        self.assertEqual(s["committed_asym_mislabelled"], 1)
        self.assertEqual(s["committed_asym_enemy_as_friendly"], 1)
        # committed3 on same data commits the 2-1 Friendly too (5 contacts)
        self.assertEqual(s["committed3_contacts"], 5)


class Cycle00TrustKeysTest(unittest.TestCase):
    """Scorer v3 additions on the frozen legacy run: all discoveries are
    legacy (no auth fields) so the census is all-direct and every
    trust metric takes its honest-baseline value."""

    @classmethod
    def setUpClass(cls):
        cls.s = score_run(RUN)

    def test_auth_census_all_direct(self):
        self.assertEqual(self.s["reports_by_auth_status"], {
            "direct_verified": 41, "hearsay_relayed": 0,
            "unverified": 0, "forged_rejected": 0})

    def test_no_forgery_no_unverified_commits(self):
        self.assertEqual(self.s["forged_acceptance"], 0)
        self.assertEqual(self.s["committed_from_unverified"], 0)

    def test_commits_per_joule(self):
        # 2 asym commits over 170 total energy; pinned, not recomputed.
        self.assertEqual(self.s["total_energy_spent"], 170)
        self.assertEqual(self.s["committed_asym_contacts"], 2)
        self.assertEqual(self.s["commits_per_joule"], 0.0118)

    def test_stage2_stubs_null(self):
        # Attribution needs claimed_sender/l2_source + treated-unit
        # designation; detection latency needs a policy-visible signal
        # event. Neither exists in journals yet: null, never fabricated.
        self.assertIsNone(self.s["attribution_accuracy"])
        self.assertIsNone(self.s["detection_latency_turns"])


class AuthSegregationTest(unittest.TestCase):
    """Scorer v3 segregation: forged/unverifiable discoveries never vote
    and never reach contact_of (no crash on non-truth tiles)."""

    TRUTH = [
        {"pos": [0, 0], "kind": "Enemy", "priority": "Normal"},
        {"pos": [1, 0], "kind": "Friendly", "priority": "Normal"},
    ]

    def _score(self, events):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            (run_dir / "director.json").write_text(json.dumps({
                "run": "auth", "ruleset": "test", "source": "test",
                "ground_truth": self.TRUTH}))
            per_unit = {}
            for ev in events:
                per_unit.setdefault(ev["unit"], []).append(ev)
            for unit, evs in per_unit.items():
                (run_dir / (unit + ".jsonl")).write_text(
                    "\n".join(json.dumps(e) for e in evs))
            return score_run(run_dir)

    def _disc(self, unit, turn, contact, tile, label, auth=None):
        ev = {"unit": unit, "turn": turn, "event": "discovery",
              "contact": contact, "tile": tile, "reported_label": label}
        if auth is not None:
            ev["auth_status"] = auth
        return ev

    def _energy(self):
        return [
            {"unit": "A1", "turn": 0, "event": "route_assigned",
             "tile": [7, 11], "energy": 30, "reserve": 3, "route": []},
            {"unit": "A1", "turn": 9, "event": "landed",
             "tile": [7, 11], "energy": 25},
        ]

    def _honest_commit(self):
        # Contact 1 (Enemy): 3 direct Enemy -> asym Enemy commit.
        evs = [self._disc("A1", t, 1, [0, 0], "Enemy") for t in (1, 2, 3)]
        evs.append(self._disc("B1", 4, 2, [1, 0], "Friendly"))
        return evs + self._energy()

    def test_forged_malformed_excluded_no_crash(self):
        evs = self._honest_commit()
        evs.append(self._disc("X9", 5, 99, [9, 9], "Friendly",
                              "forged_rejected"))   # invalid contact
        evs.append(self._disc("X9", 6, 1, [5, 5], "Friendly",
                              "forged_rejected"))   # valid contact, wrong tile
        evs.append(self._disc("X9", 7, 1, [0, 0], "Enemy",
                              "bogus_status"))       # unrecognized status
        s = self._score(evs)
        self.assertEqual(s["discoveries"], 4)
        self.assertEqual(s["contacts_found"], 2)
        self.assertEqual(s["committed_asym_contacts"], 1)
        self.assertEqual(s["reports_by_auth_status"], {
            "direct_verified": 4, "hearsay_relayed": 0,
            "unverified": 0, "forged_rejected": 2,
            "bogus_status": 1})
        self.assertEqual(s["forged_acceptance"], 0)
        self.assertEqual(s["committed_from_unverified"], 0)

    def test_forged_acceptance_counts_naive_slip(self):
        # Well-formed forgery (valid contact, matching tile): a naive
        # scorer would vote it and commit contact 1 on 2E+1F; v3 excludes it.
        evs = [self._disc("A1", 1, 1, [0, 0], "Enemy"),
               self._disc("A1", 2, 1, [0, 0], "Enemy"),
               self._disc("X9", 3, 1, [0, 0], "Friendly",
                          "forged_rejected")]
        s = self._score(evs)
        self.assertEqual(s["forged_acceptance"], 1)
        self.assertEqual(s["discoveries"], 2)
        self.assertEqual(s["committed_asym_contacts"], 0)
        control = self._score(evs[:2])
        self.assertEqual(control["forged_acceptance"], 0)
        self.assertEqual(control["discoveries"], s["discoveries"])
        self.assertEqual(control["committed_asym_contacts"],
                         s["committed_asym_contacts"])

    def test_committed_from_unverified_counterfactual(self):
        # 1 direct + 2 unverified Enemy: direct-only cannot commit (total 1)
        # but the inclusive fusion reaches 3-unanimous -> cfu 1, asym 0.
        evs = [self._disc("A1", 1, 1, [0, 0], "Enemy", "direct_verified"),
               self._disc("B1", 2, 1, [0, 0], "Enemy", "unverified"),
               self._disc("C1", 3, 1, [0, 0], "Enemy", "hearsay_relayed")]
        s = self._score(evs)
        self.assertEqual(s["discoveries"], 1)
        self.assertEqual(s["committed_asym_contacts"], 0)
        self.assertEqual(s["committed_from_unverified"], 1)
        self.assertEqual(s["reports_by_auth_status"], {
            "direct_verified": 1, "hearsay_relayed": 1,
            "unverified": 1, "forged_rejected": 0})

    def test_legacy_default_and_commits_per_joule(self):
        s = self._score(self._honest_commit())
        self.assertEqual(s["reports_by_auth_status"], {
            "direct_verified": 4, "hearsay_relayed": 0,
            "unverified": 0, "forged_rejected": 0})
        self.assertEqual(s["forged_acceptance"], 0)
        self.assertEqual(s["committed_from_unverified"], 0)
        # 1 asym commit over 5 spent energy; attribution/detection null.
        self.assertEqual(s["commits_per_joule"], 0.2)
        self.assertIsNone(s["attribution_accuracy"])
        self.assertIsNone(s["detection_latency_turns"])


if __name__ == "__main__":
    unittest.main()
