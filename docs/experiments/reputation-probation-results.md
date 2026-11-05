# Results: probationary reputation - a falsified cold-start fix

Lab simulation, synthetic data only. Pre-registered in
[reputation-probation-preregistration.md](reputation-probation-preregistration.md).
Evidence: `validation/kulira/reputation-probation-001.json`.

## Results (dangerous commits)

| Policy | Dev first half | Dev second half | Dev recall | Holdout first | Holdout second |
|---|---|---|---|---|---|
| E unweighted | 37 | 36 | 0.487 | 15 | 30 |
| REP reputation | 39 | 19 | 0.413 | 20 | 10 |
| REP-P probationary | **81** | 23 | 0.534 | **39** | 14 |

## Verdicts

- **H-M1 falsified, decisively.** Probation does not remove the
  cold-start penalty; it more than doubles first-half dangerous
  commits (81 vs 37 dev, 39 vs 15 holdout).
- **H-M2 confirmed:** second-half suppression is retained
  (23 and 14, both below E).
- The mechanism, on inspection: early reputation drops in plain
  REP are not noise - a node that errs early is discounted early,
  and that discounting is already protective. Pinning every young
  node at full weight for its first 10 sightings prolongs the
  regime where any two survivor labels commit easily, and
  colluders spend exactly that window at full weight.

## Gate outcome

REP-P is **not recommended**. Plain REP stands, with its
cold-start caveat as originally measured (slightly worse than E
for ~30 contacts, then strongly better). The lesson generalises:
when a learning defence looks noisy early, check whether the
"noise" is already signal before smoothing it away.

## Limits

Same world and limits as reputation-defence.
