# Results: normalised thresholds (REP-T) - the middle that misses

Lab simulation, synthetic data only. Pre-registered in
[reputation-normalised-preregistration.md](reputation-normalised-preregistration.md).
Evidence: `validation/kulira/reputation-normalised-001.json`.

## Results (second-half dangerous / survivor recall)

| World | REP | REP-N (strangled) | REP-T (normalised) |
|---|---|---|---|
| dev fixed | 11 / 0.309 | 1 / 0.035 | 13 / 0.229 |
| dev R=5 | 28 / 0.367 | 4 / 0.056 | 23 / 0.272 |
| holdout fixed | 2 / 0.235 | 0 / 0.007 | 1 / 0.142 |
| holdout R=5 | 15 / 0.330 | 0 / 0.014 | 12 / 0.209 |

## Verdicts

- **H-P1 confirmed:** under rotation, normalised thresholds beat
  plain REP on dangerous commits (23 < 28 dev; 12 < 15 holdout)
  while actually committing - the strangle is gone.
- **H-P2 falsified on holdout:** recall cost vs REP at R=5 is
  0.095 on dev (inside bound) but 0.121 on holdout (bound 0.10).
  Newcomer discount is a real tax on honest new nodes, and it
  does not shrink on unseen seeds.
- **H-P3 confirmed:** fixed-identity dangerous stays within
  REP + 2 (13 vs 11 dev; better on holdout).

## Gate outcome

REP-T **misses its gate** (H-P2 holdout) and is not recommended
over REP where identities are stable - which remains the
deployment condition this whole sub-series keeps pointing at.
Where identity rotation is genuinely expected, REP-T is the
least-bad measured option: dangerous below both E and REP,
at an honest ~0.10-0.12 recall tax.

## Series reading (reputation trilogy)

Plain REP (immediate symmetric accrual) for expensive
identities; REP-T if identities must rotate; REP-N never.
Three designs, three pre-registered gates, two failures kept -
the boundary map is the deliverable.

## Limits

Same world/limits as sybil-rotation.
