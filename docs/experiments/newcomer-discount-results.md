# Results: newcomer discount - safety by strangulation

Lab simulation, synthetic data only. Pre-registered in
[newcomer-discount-preregistration.md](newcomer-discount-preregistration.md).
Evidence: `validation/kulira/newcomer-discount-001.json`.

## Results (second-half dangerous / survivor recall)

| World | REP dangerous | REP recall | REP-N dangerous | REP-N recall |
|---|---|---|---|---|
| dev, fixed identity | 11 | 0.309 | 1 | **0.035** |
| dev, R=20 | 20 | 0.342 | 2 | 0.046 |
| dev, R=5 | 28 | 0.367 | 4 | 0.056 |
| holdout, R=5 | 15 | 0.330 | 0 | 0.014 |

## Verdicts

- **H-O1 confirmed trivially:** REP-N dangerous collapses
  everywhere (rotation or not).
- **H-O2 confirmed trivially** for the same reason.
- **H-O3 falsified decisively:** survivor recall collapses to
  0.01-0.06. The discount does not selectively suppress the
  adversary; at a 0.5 start with REP's weighted thresholds
  (survivor sum >= 1.5) unchanged, almost no contact - honest
  or hostile - ever reaches the commit bar. REP-N is safe in
  the way a powered-down system is safe.

## Gate outcome

REP-N is **not recommended** as specified. The interesting
content is the failure mode: reputation weights and commit
thresholds live in the same units. Halving everyone's starting
weight without rescaling the bar does not price newcomer risk;
it raises the bar for the whole swarm. A serious version of
this idea needs thresholds defined relative to available trust
(for example, margin as a fraction of deciding weight) - a new
design, requiring its own pre-registration, not a tweak here.

## Relation to the probation result

Two natural fixes to reputation's edges have now failed in
opposite directions: probation (full weight early) prolongs
easy commits; newcomer discount (half weight early) prevents
almost all commits. The unmodified REP - immediate, symmetric
accrual from full weight - remains the measured best of the
three, cold-start caveat included.
