# Pre-registration: normalised thresholds + newcomer discount (REP-T)

Registered before running. Follow-up to newcomer-discount, whose
failure was unit mismatch: halving starting weights while keeping
absolute weighted thresholds (sum >= 1.5) strangled all commits.

## Policy REP-T

Sybil-rotation world, unchanged. Reputation as REP-N (unseen ID
starts 0.5; +0.05/-0.15, clamp [0.1, 1.0]). Commit rule is
scale-free: commit survivor if weighted survivor sum >= 1.0 AND
survivor share of deciding weight ws/(ws+wh) >= 0.67 (a 2:1
weighted margin), instead of absolute sum/margin bars.

## Pre-registered expectations and gate

- H-P1: at R=5, REP-T second-half dangerous is strictly below
  REP's at R=5, dev and holdout.
- H-P2: at R=5, REP-T survivor recall is no more than 0.10 below
  REP's at R=5 (the strangle is gone).
- H-P3: at fixed identity, REP-T second-half dangerous is no
  more than REP's + 2 on dev.
- Gate: recommend REP-T over REP if all three hold.

## Limits

Same world/limits as sybil-rotation. Threshold constants above
(1.0, 0.67, start 0.5) are registered here, not tuned later.
