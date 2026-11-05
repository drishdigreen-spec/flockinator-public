# Results: identity rotation vs reputation defence

Lab simulation, synthetic data only. Pre-registered in
[sybil-rotation-preregistration.md](sybil-rotation-preregistration.md).
Evidence: `validation/kulira/sybil-rotation-001.json`. One
colluding actor; fresh identity every R contacts.

## Rotation curve (second-half dangerous commits)

| Identity lifetime R | Dev E | Dev REP | Holdout E | Holdout REP |
|---|---|---|---|---|
| fixed identity | 20 | **11** | 13 | **2** |
| 20 contacts | 20 | 20 | 13 | 6 |
| 10 contacts | 20 | 26 | 13 | 14 |
| 5 contacts | 20 | 28 | 13 | 15 |

(E is identity-blind, so its column is the same scenario baseline
at every R; REP varies.)

## Verdicts

- **H-N1 confirmed:** with a fixed identity, reputation helps
  (11 vs 20 dev; 2 vs 13 holdout).
- **H-N2 confirmed, and stronger than registered:** at R=5 the
  advantage is not merely gone - on dev, REP is *worse* than
  doing nothing (28 vs 20). The boundary on dev is already at
  R=20 (20 vs 20); holdout keeps a shrinking benefit to R=20.

## Mechanism

Rotation does not just erase the colluder's bad history. It
gives the adversary a permanent clean record while honest nodes
accumulate discounted reputations from their ordinary 25%
error rate. Under rotation, reputation weighting systematically
favours the newest identity in the room - which is the attacker.
A defence that prices history must therefore price *absence* of
history too: new identities should start discounted, not at
full weight (the mirror image of the probationary idea, which
failed for a different reason - see reputation-probation).

## Boundary statement

Reputation defence is valid only where identity is expensive:
provisioned, hardware-bound, or otherwise hard to reissue. Where
identities are free, reputation inverts from defence to attack
surface. That is a deployment requirement, measurable as:
identity lifetime must exceed the learning window (~30 contacts
in these parameters) by a comfortable margin.

## Limits

Simulation only; one rotating actor, honest majority, fixed
participation rate. A Sybil majority is worse and unmodelled.
