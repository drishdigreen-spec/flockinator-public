# Pre-registration: strict composite (learned trust + strict rule)

Registered before running. From factorial-trust: L-T0 (learned
modality trust, strict thresholds) was the safest cell measured
(3-4 post-betrayal dangerous), at steep recall cost. This
evaluates it as a candidate revision of the recommended
composite on fresh seeds.

## Policies (composite world, unchanged)

- **COMP** (current recommendation): learned trust, loose rule
  (weighted survivor >= 1.5, margin >= 1.0).
- **S (strict composite):** learned trust, strict rule
  (weighted survivor >= 2, margin >= 2). Identical to factorial
  cell L-T0; this run is its policy evaluation, not a re-tune.

## Seeds

Fresh ranges, first use in this series: dev 400-419,
evaluation 500-509 (see seed-use ledger).

## Pre-registered expectations and gate

- H-R1: S post-betrayal dangerous commits < COMP's on both
  splits.
- H-R2: S survivor recall drop vs COMP <= 0.20 on both splits.
- Gate: if both hold, S replaces COMP as the recommended
  composite for commits where the dangerous direction matters;
  COMP remains the recall-leaning variant. If H-R2 fails, the
  pair is reported as a safety/recall frontier, no replacement.

## Limits

Simulation only; composite world and parameters unchanged.
