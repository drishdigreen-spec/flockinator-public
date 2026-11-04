# Capability Map: Kulira Chaos / Noise (Offensive)

Status: **draft for owner review — gate before any module spec or code**
Date: 4 November 2026. Host: `lab-host.example.internal` (192.168.1.10).
Fleet baseline: sixteen nodes A1–D4 on 0.10.2-journal; Korvo 0.9.0 at
192.168.1.10 hosts planner/lab/learning centrally. See
[CAPABILITY-MAP.md](CAPABILITY-MAP.md) and [HANDOVER.md](HANDOVER.md).

## Framing — a controlled experiment, not an attack showcase

This is a **controlled experiment** about learning under adverse
conditions. The drone scenario is a conceptual visualisation for
humans: an intelligent agent swarm that must keep learning while its
world pushes back — the same selective pressure seen in nature, from
animals to viruses to DNA, where optimisation is never a smooth
descent. Billions of years of hardship and struggle, compressed into
seeded, measurable runs.

The principles are those of reinforcement learning applied differently:
train and improve **small models in isolation** (one per node, plus
models external to the node), then let fitness be decided by the
environment — including a hostile one. Kulira *is* that environment's
adversarial part. Three loci of intelligence are made visible:
**in the node** (local model/policy), **external to the node** (Korvo/
host learning, presenter), and **between nodes** (inter-node trust,
corroboration, and communication norms that evolve under pressure).

## Objective (reframed)

Kulira is the adversary, not another optimiser. While the fleet tries to
learn to do its job better, Kulira injects **reproducible, bounded,
reversible friction** — disruption, impersonation, and lying — so that
naïve trust fails visibly and measuredly. Success is not "fleet broken";
success is a fleet (or its agents) that earns trust: validates identity,
corroborates claims independently, degrades gracefully, and recovers —
with numbers proving each, against a clean-run baseline.

Reframed success criteria (to confirm):
- Every attack is seeded, logged, replayable, and attributable after the
  run (presenter/observer view) while hidden from agents during it.
- No attack touches management, OTA/deployment, or recovery authority.
- Each capability below can be run alone, at graded intensity, and
  switched off instantly; fleet returns to baseline unaided.
- Each run reports: time-to-detect, nodes deceived, propagation depth,
  recovery time, and management-plane health during the attack.

## Assumptions — correct these before approving

1. Authorised lab only: this LAN, these sixteen nodes, fictional/simulated
   mission data. No third-party networks, no real-world targeting data.
2. Kulira attacks the **experiment/agent plane first** (peer reports,
   observations, learning inputs); the authenticated commissioning plane
   (ESP-NOW HMAC-SHA256, per-node keys, challenge–response, replay
   protection in [SPEC-flock-network.md](SPEC-flock-network.md)) is the
   control that *should* reject impersonation — we test that, not assume it.
3. "Lying" starts as an authenticated-but-false claim (the false-beacon
   precedent in
   [reconnaissance-swarm-experiment.md](docs/design/reconnaissance-swarm-experiment.md)),
   not stolen keys. Key compromise, if ever, is a separate gated scenario.
4. **Network jamming is offline.** No illegal blocking/jamming devices,
   no brute-force RF denial, no credential exfiltration. Interference —
   which *is* required for friction and spoofing — comes only from
   Layer 1/2/3 protocol techniques inside the controlled experiment
   (owner clarification, 4 Nov 2026): legitimate radios contending,
   impersonating, replaying, misdirecting, delaying or dropping traffic
   on the lab network, at lab power, on lab channels, against named
   targets only.
5. Kulira never gains firmware-deployment or node-identity authority;
   it is explicitly *not* HQ and *not* a seventeenth trusted node.
6. Learning impact is measured against the communication lab's clean
   baselines (e.g. clear vs scrambled payloads in
   [communication-learning-demo.md](docs/design/communication-learning-demo.md)).

## Capability map

| Module id | Responsibility | Depends on |
|---|---|---|
| `kulira-core` | Campaign orchestrator: seeded scenario schedule, intensity grading, safety interlock/kill-switch, tamper-evident attack log, run manifest | — |
| `kulira-disrupt` | Transport friction on experiment traffic: drop, delay, duplicate, reorder, partition, silent node | `kulira-core` |
| `kulira-spoof` | Impersonation: forged sender identity, replayed messages, Sybil/duplicate-label claims, rogue-node presence | `kulira-core` |
| `kulira-deceive` | Lying: false observations/telemetry, contradictory reports, poisoned learning examples, forged corroboration (copies ≠ independent sightings) | `kulira-core`, `kulira-spoof` |
| `kulira-rf` | USB gadget drivers: passive inventory/survey and Layer 1/2 impersonation/contention TX under core limits (no jamming devices) | `kulira-core` |
| `kulira-observe` | Scoring: ground-truth diff, who-believed-what timeline, detection/recovery metrics, clean-vs-attacked comparison report | `kulira-core` |

Build order: `kulira-core` → `kulira-rf` (passive only) → `kulira-disrupt` → `kulira-spoof` →
`kulira-deceive` → `kulira-observe` (scoring stubs from day one so every
attack ships with its measurement; full reporting last).

Dependency rules: arrows one way, no cycles. If `kulira-deceive` needs
identity it borrows `kulira-spoof`'s interface; it does not reach into
fleet internals. Interfaces (message contract, attack-log schema,
kill-switch) live in the provider module's spec, not here.

Notes on fit with existing modules: this map **adds one adversary actor**;
it does not rename existing ids. It consumes `flock-network` experiment
events and `experiments` scenario/seed machinery where they exist, and
stays out of `node-platform`, `cluster-deployment`, and
`management-console` authority. Where experiment messaging is still
future work, Kulira's first spec must say whether it attacks the host
lab/simulation, the Korvo lab, or live nodes — see Open Questions.

## Boundaries (proposed)

- **Always:** seeded + logged attacks; management/health/OTA verified
  live during every run; instant stop; restore baseline and prove it.
- **Ask first:** any attack on a live physical node (vs host/Korvo
  simulation); any intensity above the agreed starting grade; any new
  transport (ESP-NOW vs Wi-Fi) as an attack surface.
- **Never:** RF jamming/deauth; touching deployment, identity
  provisioning, or per-node keys; persistence on nodes after a run;
  presenting attack results as fleet defects without a clean baseline.

## Open Questions — need owner answers before module specs

1. **First target surface:** host communication lab/simulation only,
   Korvo-hosted lab, or live ESP-NOW/Wi-Fi nodes? (Recommended: lab
   first, one live node second, fleet last.)
2. **Who defends?** Is the fleet agents' validation/trust-scoring work
   in scope for this initiative, or Kulira-only with scoring by
   `kulira-observe`? This decides whether a defender spec follows.
3. **Impersonation depth:** unauthenticated forgery + replay only
   (expected: rejected by HMAC/challenge), or also a deliberately
   credentialed rogue node lying with valid auth (false-beacon style)?
4. **Disruption ceiling:** max drop/delay/partition share and duration
   for a first campaign, and is a whole-fleet partition ever allowed?
5. **Disclosure during runs:** fully blind to agents/operators, or
   presenter-visible in real time (observer view) with agent view blind?

## Next step

Owner reviews module boundaries, dependency direction, build order,
assumptions, and Open Questions. On approval, run Specify → Plan →
Tasks → Implement **per module**, starting with `SPEC-kulira-core.md`.
No code before that spec is approved.
