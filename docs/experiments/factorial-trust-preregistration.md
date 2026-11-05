# Pre-registration: factorial isolation of learned trust vs thresholds

Registered before running. Required by the composite correction:
the published composite comparison bundled two changes (learned
modality-trust weights + looser commit thresholds) and cannot
attribute its effect to either.

## Design

World: composite-defence world, unchanged (forgeries + relays
from contact 0; ir betrayal from contact 20; outcomes revealed
after each contact; identical report streams for all cells).

Factorial cells, crossing weights x thresholds:

| Cell | Weights | Commit rule (on weighted sums ws, wh) |
|---|---|---|
| F-T0 | fixed 1.0 | ws >= 2 and ws - wh >= 2 (= policy E) |
| F-T1 | fixed 1.0 | ws >= 1.5 and ws - wh >= 1.0 (= COMP thresholds) |
| L-T0 | learned modality trust | ws >= 2 and ws - wh >= 2 |
| L-T1 | learned modality trust | ws >= 1.5 and ws - wh >= 1.0 (= policy COMP) |

Learned trust as in composite (init 1.0, +0.05/-0.10 from
revealed outcomes, clamp [0.1, 1.0]). Admission: policy-D pool
(direct, deduped) in all cells.

**Primary contrast (declared):** learned vs fixed weights
within T1 (L-T1 vs F-T1), post-betrayal dangerous commits.
Secondary: within T0; and threshold effect within fixed weights
(F-T1 vs F-T0).

## Pre-registered expectations and gate

- H-Q1: if learned trust is an active ingredient, L-T1
  post-betrayal dangerous < F-T1 on dev and holdout.
- H-Q2: if the published composite gain was mostly threshold,
  F-T1 will sit close to L-T1 (within 3 dangerous commits on
  dev) - in which case that is the reported conclusion.
- No policy recommendation from this experiment; its
  deliverable is attribution. The composite recommendation
  stands or falls as a bundle regardless.

## Seeds and limits

New evaluation seeds 200-219 (dev) and 300-309 (holdout-style,
first use in this series - see seed ledger) to avoid reusing
design-exposed seed sets for a confirmatory contrast.
Simulation only; same world limits as composite-defence.
