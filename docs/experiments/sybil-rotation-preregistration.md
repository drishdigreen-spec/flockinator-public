# Pre-registration: identity rotation vs reputation defence

Registered before running. Follow-up to reputation-defence,
whose stated limit was: identity-rotating (Sybil) adversaries
defeat reputation accrual by construction. This measures how
much rotation is enough.

## Question

One colluding actor reports under a fresh identity every R
contacts (R in {infinity (fixed identity), 20, 10, 5}). Honest
nodes keep stable identities. At what R does reputation
weighting stop helping?

## Setup (reputation-defence world, changed as stated)

- 60 sequential contacts; 7 honest verified nodes with stable
  identities plus 1 colluding actor. Each contact sighted by
  2-3 reporters; the colluder participates with the same
  frequency as an honest node and labels every hazard it sights
  as survivor.
- The colluder's reporter ID rotates every R contacts; each new
  ID starts with reputation 1.0 and no history. Honest sightings
  label correctly with p=0.75. Outcomes revealed after each
  contact; reputation (+0.05/-0.15, clamp [0.1, 1.0]) accrues
  per reporter ID.
- Policies: E (unweighted margin rule) and REP (reputation
  weighted, as in reputation-defence).

## Pre-registered expectations

- H-N1 (sanity): at R=infinity, REP second-half dangerous
  commits are below E's (direction of the earlier result).
- H-N2: at R=5, REP's second-half advantage is gone: REP
  second-half dangerous >= 0.9 x E's on dev.
- Deliverable: the rotation curve R -> second-half dangerous
  for both policies, dev and holdout. No new recommendation;
  the deliverable is the measured boundary of the defence.

## Limits

Simulation only. One rotating actor; a Sybil *majority* is a
different (worse) problem and is not modelled here.
