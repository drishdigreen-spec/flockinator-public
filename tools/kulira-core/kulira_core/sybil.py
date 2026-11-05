"""Identity rotation vs reputation: one colluder, fresh IDs.

The colluding actor reports under a new identity every R contacts;
each new ID starts at reputation 1.0. Honest nodes are stable.
E ignores identity; REP weights by per-ID reputation.
"""
from __future__ import annotations
import random
from .relay_attack import MODALITIES, NODES

HONEST = NODES[:7]

def generate_sybil(seed, rotation, contacts=60):
    rng = random.Random(seed)
    seq = []
    for i in range(contacts):
        truth = "survivor" if rng.random() < 0.5 else "hazard"
        reporters = rng.sample(HONEST, rng.choice((1, 2)))
        colluder_in = rng.random() < 0.35  # ~one reporter in three is the actor
        reports = []
        for j, node in enumerate(reporters):
            label = truth if rng.random() < 0.75 else (
                "hazard" if truth == "survivor" else "survivor")
            reports.append((f"s{i}-{j}", node, rng.choice(MODALITIES), label, False))
        if colluder_in:
            cid = "K-fixed" if rotation is None else f"K-{i // rotation}"
            label = "survivor" if truth == "hazard" else (
                truth if rng.random() < 0.75 else "hazard")
            reports.append((f"s{i}-c", cid, rng.choice(MODALITIES), label, False))
        seq.append({"contact": i, "truth": truth, "reports": reports})
    return seq

def score_sybil(seq, policy):
    rep = {}
    start = 0.5 if policy == "REP-N" else 1.0  # newcomer discount
    second = first = survivors = committed = 0
    for c in seq:
        pool = {}
        for r in c["reports"]:
            pool.setdefault(r[0], r)
        pool = list(pool.values())
        surv = [r for r in pool if r[3] == "survivor"]
        haz = [r for r in pool if r[3] == "hazard"]
        if policy == "E":
            ok = len(surv) >= 2 and len(surv) - len(haz) >= 2
        else:
            ws = sum(rep.get(r[1], start) for r in surv); wh = sum(rep.get(r[1], start) for r in haz)
            ok = ws >= 1.5 and (ws - wh) >= 1.0
        if c["truth"] == "survivor":
            survivors += 1; committed += bool(ok)
        elif ok:
            if c["contact"] < 30: first += 1
            else: second += 1
        for r in pool:
            good = (r[3] == c["truth"])
            rep[r[1]] = min(1.0, max(0.1, rep.get(r[1], start) + (0.05 if good else -0.15)))
    return {"dangerous_first": first, "dangerous_second": second,
            "recall": round(committed / survivors, 4) if survivors else None}

def run_sybil(seeds, rotations=(None, 20, 10, 5)):
    out = {}
    for rot in rotations:
        key = "fixed" if rot is None else str(rot)
        out[key] = {}
        for pol in ("E", "REP", "REP-N"):
            per = [score_sybil(generate_sybil(s, rot), pol) for s in seeds]
            out[key][pol] = {"dangerous_second": sum(p["dangerous_second"] for p in per),
                             "mean_recall": round(sum(p["recall"] or 0 for p in per) / len(per), 4)}
    return out
