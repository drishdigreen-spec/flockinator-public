# Pre-registration: probationary reputation (cold-start fix)

Registered before running. Follow-up to reputation-defence,
which measured a cold-start penalty: reputation weighting is
slightly worse than unweighted E for the first ~30 contacts,
before track records exist.

## Policy REP-P

As REP (per-node reputation from revealed outcomes), except a
node's reputation weight is only *applied* after that node has
10 revealed sightings. Before probation completes, the node's
sightings count at weight 1.0 (as in E). Reputation still accrues
from contact 0; it is simply not trusted until it has evidence.

## Pre-registered expectations and gate

- H-M1: first-half (contacts 0-29) dangerous commits under REP-P
  are <= E's on dev and holdout (the cold-start penalty is gone,
  not merely reduced - if it is only reduced, that is reported).
- H-M2: second-half (30-59) dangerous under REP-P remains
  strictly below E's on both splits (the learned suppression is
  retained).
- H-M3: REP-P whole-run recall within 0.15 of E's on both splits.
- Gate: recommend REP-P over REP if all three hold.

## Limits

Same world and limits as reputation-defence; probation length
10 is the registered parameter, not tuned after results.
