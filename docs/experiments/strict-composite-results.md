# Results: strict composite replaces loose composite for dangerous commits

Lab simulation, synthetic data only. Pre-registered in
[strict-composite-preregistration.md](strict-composite-preregistration.md)
(fresh seeds 400-419 / 500-509). Evidence:
`validation/kulira/strict-composite-001.json`.

## Results (post-betrayal dangerous / mean recall)

| Policy | Dev 400-419 | Eval 500-509 |
|---|---|---|
| COMP learned trust, loose rule | 13 / 0.321 | 10 / 0.297 |
| **S learned trust, strict rule** | **4** / 0.150 | **6** / 0.162 |

## Verdicts

- **H-R1 confirmed:** strict thresholds under learned trust cut
  post-betrayal dangerous commits roughly threefold on dev
  (13 -> 4) and by 40% on eval (10 -> 6).
- **H-R2 confirmed:** recall cost is 0.170 (dev) and 0.135
  (eval), inside the pre-registered 0.20 bound - real, and
  worth stating as the price.

## Gate outcome

Policy S **replaces COMP as the recommended composite** where
the dangerous direction matters (hazard committed as survivor).
COMP remains the recall-leaning variant for reversible,
low-stakes commits - which is precisely the priority-split
division measured earlier (policy F): strict where it is
irreversible, loose where it is cheap. The series has now
arrived at the same answer from three independent directions.

## Updated recommended stack

1. Admission by provenance (D): direct_verified only decide.
2. Learned modality-trust weighting (factorial-attributed).
3. Strict commit rule (S) for irreversible commits; loose
   rule + bought second looks only where reversible (F).
4. Behavioural reputation over expensive identities as the
   collusion layer, cold-start caveat attached.

## Limits

Simulation only; fresh-seed evaluation of an existing cell,
not a new mechanism. Recall levels in the composite world are
low in absolute terms (betrayal world); the comparison, not
the level, is the result.
