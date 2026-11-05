# Attacks against the swarm: types, impact, and the tiny-model asymmetry

Catalogue of attacks on Flockinator's agent-to-agent (A2A) surface.
Theorised attacks come from the design; **surprising attacks** - the
ones of most research interest - are marked and were observed in
experiments or in the Glimmer proposal loop. Impact is rated for a
swarm whose agents learn from peer messages: the worst outcome is
rarely a crashed node, it is a swarm that *learns the wrong thing
confidently*.

## Taxonomy

| # | Attack | Plane | Mechanism | Impact if undefended | Defence / measurement |
|---|---|---|---|---|---|
| 1 | Drop / delay / duplicate | L1-L3 | Lab-controlled path withholds, delays, or repeats experiment traffic | Stale beliefs, duplicated sightings counted twice, timeouts mistaken for absence | Seeded drop rates; consumed-vs-delivered accounting; duplicate suppression by sighting id |
| 2 | Partition | L3 | Swarm split into groups that cannot hear each other | Divergent world models; contradictory "consensus" in each half | Partition scenarios; cross-partition disagreement at scoring |
| 3 | Co-channel contention | L1 | Legitimate lab radios contend on the experiment channel | Bursty loss that correlates with activity, not random loss | Graded contention; loss-vs-load curves |
| 4 | Impersonation (forged identity) | L2 | Frames/messages claiming another node's label without its key | False reports attributed to an honest node; reputation damage to the victim | HMAC tag + sender binding (measured: forged -> `rejected:bad_tag`) |
| 5 | Replay | L2/L3 | Re-send a previously valid message later | Old positions believed current; freshness attacks on "first to report" | Nonce/sequence replay cache (measured: `rejected:replay`) |
| 6 | Wrong-target / label confusion | L2 | Valid message delivered to or claimed by the wrong label | Cross-node state contamination | Recipient binding (measured: `rejected:wrong_target`); duplicate-label = conflict, never merged |
| 7 | Sybil / duplicate identity | L2 | One actor presents as many nodes | Manufactured majority; quorum capture | Identity provisioning cost; duplicate-MAC/label conflict detection |
| 8 | Authenticated-but-false report (insider liar) | App | A credentialed node (or scenario-granted key) signs a false observation | The hardest class: authentication passes, payload is wrong | Independent corroboration thresholds; dangerous-direction metrics (Enemy->Friendly) |
| 9 | Forged corroboration | App | Forwarded copies of one sighting presented as independent sightings | One liar amplifies into swarm-wide false belief | Corroboration counts distinct sighting ids, never reporters (implemented in `kulira-deceive`) |
| 10 | Contradiction / flip-flopping | App | Alternating contradictory claims from one or more sources | Belief oscillation; learning instability; energy spent re-checking | Belief hysteresis, abstention, per-source consistency history |
| 11 | Timing / freshness manipulation | L2/L3 | Delay only the messages that would correct a false belief | False belief wins the decision window even though truth arrives | Decision deadlines with provenance timestamps; late-truth accounting |
| 12 | Energy / attention exhaustion | L1/App | Flood of plausible reports forcing verification work | Nodes spend energy/radio time checking instead of sensing; graded-sensing budgets drained | Rate budgets, cheap-first verification, abstention under load |
| 13 | Management-plane mimicry | App | Adversary proposes or imitates management/OTA-style actions | If honoured: total compromise class - deployment and identity authority | Never granted to experiment actors; scenario guard rejects management/OTA/firmware actions by name (observed, below) |
| 14 | Learning poisoning | App | Slow drip of subtly biased examples during training windows | Model improves on the poisoned distribution, fails held-out truth | Same-seed controls, held-out frozen evaluation, clean-vs-impaired training crosses |
| 15 | Selective silence (lying by omission) | App | Honest messages withheld only when they would help | Swarm underperforms with no false message to detect | Private-cue baselines expose the missing cooperative gain |

## Surprising attacks and failures (observed)

These are why the catalogue exists - none was the headline threat
model when first seen:

1. **The adversary model aimed at management.** Glimmer's first
   proposed scenario (5 Nov) included `mimic_management_ping` -
   the tiny attacker model independently chose the highest-authority
   target class. The (new) scenario guard rejected it by name; the
   model revised to experiment-plane deception. Lesson: an adaptive
   adversary optimises for authority, not for the attacker's
   intended test plan.
2. **Unanimous-wrong consensus.** In cycle-06, seed 10 produced a
   unanimous swarm belief that was wrong (Enemy committed as
   Friendly). Majority vote amplified a correlated error instead of
   cancelling it - consensus is not evidence when sightings are
   correlated.
3. **Copies that look like corroboration.** Forwarded sightings are
   the natural swarm behaviour and the natural forgery: one false
   sighting, relayed helpfully, presents as many independent
   confirmations. Counting reporters instead of sighting ids makes
   the swarm *more* vulnerable the better it communicates.
4. **Associated-but-deaf (availability without a crash).** The live
   controller wedge: associated to WiFi, outbound mostly alive,
   inbound deaf, for hours, with partial watchdog recovery. No
   node failed; the *system* silently degraded. Detection needed
   end-to-end probes, not link state.
5. **Honest insider error outranks forgery.** Scorer v3 analysis:
   at measured identify accuracies, a credentialed node that is
   merely wrong contributes more dangerous (Enemy->Friendly) error
   than an outsider forging without keys, who is simply rejected.
   Defence priority inverts: verify insiders' *claims*, not just
   outsiders' *identities*.
6. **Abstention beats voting.** Four gated commit policies were
   rejected in a row; no vote rule reached zero dangerous error at
   current sensing accuracy. The productive direction was not a
   cleverer aggregation but the right to not commit, and to buy
   more sensing. Aggregation research has diminishing returns below
   a sensing floor.

## The tiny-model asymmetry (research note)

The frontier models in this project - Muse Wonder/Spark tiers -
design the firmware, write the security controls, and judge the
evidence. The adversary is Muse Glimmer: a 30B-class local model,
abliterated, running on a bench host through Hermes. By capability
it is not close. By *impact* the asymmetry runs the other way:

- **Cost:** the attacker needs one plausible false report at the
  right moment; the defence needs identity, freshness,
  corroboration, and recovery to be right every time, on 20 mW-class
  radios, forever.
- **Search:** the attacker searches for *any* seam (Glimmer found
  the management-plane seam in its first scenario); the defender
  must enumerate and close seams systematically, because the seam
  it misses is the one that will be used.
- **Adaptation:** a tiny adaptive adversary co-evolving against a
  fixed defence turns a passing test suite into a training set for
  the attacker. Defence must therefore evolve too - which is the
  evolutionary loop this platform exists to run.

We believe this is a new and critical research field for agent-to-
agent systems: **asymmetric A2A risk**, where small, cheap, possibly
abliterated models attack swarms of larger ones, and where the
defensible surface is not a smarter model but a measured interaction
layer - authentication that binds identity, corroboration that
counts independence, abstention that respects sensing limits, and
pre-registered gates that refuse promotion when the dangerous
direction is not zero. Flockinator's contribution is an instrument:
embodied agents, sealed ground truth, a bounded adaptive adversary,
and scoring that can falsify a defence - so claims about A2A safety
can be measured rather than asserted.

Open questions we cannot yet answer: how attack success scales with
adversary model size at fixed defence; whether trust policies
learned under one adversary transfer to a different one; where the
sensing floor sits for a given dangerous-error tolerance; and
whether extra-node trust norms, once evolved, persist when the
adversary is removed - or decay.
