# Results: factorial isolation - learned trust is the active ingredient

Lab simulation, synthetic data only. Pre-registered in
[factorial-trust-preregistration.md](factorial-trust-preregistration.md)
(new seed ranges 200-219 / 300-309, first use). Evidence:
`validation/kulira/factorial-trust-001.json`. Required by the
composite correction: the earlier composite bundled learned
weights with looser thresholds.

## Factorial table (post-betrayal dangerous / mean recall)

| Cell | Dev (200-219) | Eval (300-309) |
|---|---|---|
| F-T0 fixed weights, strict rule (= E) | 14 / 0.236 | 10 / 0.221 |
| F-T1 fixed weights, loose rule | **46** / 0.388 | **23** / 0.377 |
| L-T0 learned trust, strict rule | **3** / 0.140 | **4** / 0.125 |
| L-T1 learned trust, loose rule (= COMP) | 14 / 0.314 | 7 / 0.294 |

## Attribution (primary contrast, declared in advance)

- **H-Q1 confirmed:** within the loose threshold scheme,
  learned trust cuts post-betrayal dangerous commits from
  46 to 14 (dev) and 23 to 7 (eval). Learned modality trust
  is an active ingredient, not decoration.
- **H-Q2 falsified, in the interesting direction:** the
  published composite gain was *not* mostly threshold. Loose
  thresholds alone are actively harmful (46 vs 14 against the
  strict rule at fixed weights): they let betrayed-modality
  labels commit hazards. The composite bundle worked because
  learned trust compensated for its own looser bar.
- Learned trust also dominates at strict thresholds (L-T0:
  3-4 dangerous, the safest cell measured in this world) at a
  steep recall cost (0.13-0.14).

## What this changes

The composite recommendation survives, now with attribution:
the trust-weighting layer earns its place; the loose commit
thresholds do not, except as a recall purchase whose price
learned trust happens to pay. A stricter composite (learned
trust + strict rule) is the safest measured configuration in
this world and the obvious candidate for any future
pre-registered policy revision.

## Limits

Simulation only; one world (composite), one betrayal onset,
registered trust/threshold parameters throughout.
