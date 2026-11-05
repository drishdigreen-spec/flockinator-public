# Pre-registration: newcomer discount vs identity rotation

Registered before running. Follow-up to sybil-rotation, which
found reputation inverts when identities are free: the rotating
adversary always holds the newest, cleanest record. Suggested
mirror fix, tested here: price absence of history.

## Policy REP-N

As REP (sybil-rotation world), except an unseen reporter identity
starts at reputation 0.5 instead of 1.0, for honest and colluding
identities alike. Accrual unchanged (+0.05/-0.15, clamp [0.1,1.0]).
Commit rule unchanged (weighted survivor >=1.5, margin >=1.0).

## Pre-registered expectations and gate

- H-O1: at R=5, REP-N second-half dangerous commits are strictly
  below REP's at R=5, dev and holdout.
- H-O2: at fixed identity, REP-N second-half dangerous is no
  worse than REP's +2 (the discount must not break the case that
  already worked).
- H-O3: REP-N survivor recall at R=5 is no more than 0.10 below
  REP's at R=5 (honest newcomers also pay the discount).
- Gate: recommend REP-N over REP if all three hold.

## Limits

Same world/limits as sybil-rotation (one rotating actor, honest
majority). Starting value 0.5 is the registered parameter.
