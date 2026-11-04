# Spec: Kulira Core — chaos orchestrator (`kulira-core`)

Status: **approved by owner**, 4 November 2026 ("approve"). Implementation
plan: [tasks/kulira-core/plan.md](tasks/kulira-core/plan.md).
Module: `kulira-core`, from [CAPABILITY-MAP-kulira-chaos.md](CAPABILITY-MAP-kulira-chaos.md)
(approved "proceed", 4 Nov 2026, with RF/EW context below).
Sibling modules (own specs later, in build order): `kulira-disrupt`,
`kulira-spoof`, `kulira-deceive`, `kulira-observe`. Fleet modules are
unchanged; Kulira consumes their experiment interfaces, never their
management authority.

## Objective

Give Kulira (`lab-host.example.internal`, 192.168.1.10) one safe,
reproducible way to run offensive experiments against the Flockinator
fleet: schedule seeded chaos, arm exactly one attack at a time, enforce
hard safety limits, keep a tamper-evident log, and always be able to
stop and prove the fleet is back to baseline. Kulira models a hostile
neighbour — another swarm's drones or EW devices — not a fleet insider.

Why: the fleet is learning to optimise by trusting peer messages. Without
a disciplined adversary, "it learned faster" and "it learned to be
gullible" look identical. `kulira-core` is the discipline: every later
attack module plugs into it, inherits its limits, and is scored the
same way.

User: the owner/operator on Kulira, running a campaign against their own
sixteen nodes (A1–D4, 0.10.2-journal) and the Korvo lab (0.9.0).

Framing (owner, 4 Nov 2026): this is a controlled experiment. The drone
scenario is a conceptual visualisation of an intelligent agent swarm
learning under adverse conditions — nature's way (animals, viruses,
DNA): not an easy path to optimisation, but hardship and struggle over
evolutionary time, compressed into seeded runs a human can watch. The
method applies to reinforcement learning for small models trained in
isolation: intelligence evolves in the node, external to the node, and
between nodes. Kulira supplies the selective pressure; it does not
"win" when the fleet merely breaks — a run only teaches something when
the pressure is graded, survived or not, and the difference is measured.

Success looks like: `campaign run` executes a written scenario end to
end, every emitted action is in the log with its seed, `campaign stop`
halts RF/app emission within 1 s at any moment, and the post-run report
shows management-plane health stayed live throughout.

### RF / EW context (owner, 4 Nov 2026)

Kulira has USB-attached RF gadgets that can impersonate devices and
interfere with the EM environment between nodes. In the experiment they
stand in for hostile drones / electronic-warfare devices in another
swarm. **Network jamming is offline** (owner, 4 Nov 2026): no illegal
blocking/jamming devices and no brute-force RF denial. Interference is
required for friction and spoofing, and is produced only by Layer 1/2/3
protocol techniques inside this controlled experiment:

| Layer | Techniques in scope (lab LAN, named targets, graded) |
|---|---|
| L1 physical | Co-channel contention from legitimate lab radios, controlled attenuation/distance/shielding, presence/absence of a transmitter |
| L2 link | Frame/MAC impersonation, replay, rogue peer/AP presence, duplicate-label claims on the experiment channel |
| L3 network | IP spoofing/misdirection, rogue relay, drop/delay/duplicate/reorder/partition via a lab-controlled path |

Consequences for this spec:

- Attack surface is three planes, selected per scenario, never mixed
  silently: **app** (IP/ESP-NOW messages), **link** (association,
  channel, peer presence), **RF** (in-band energy, replayed waveforms).
- `kulira-core` does not transmit. It owns the *contract* every RF
  actuator must satisfy (arm/fire/stop, power/frequency/duty limits,
  logging) so `kulira-disrupt`/`kulira-spoof` RF actions are bounded
  before any gadget driver exists.
- Gadget inventory is evidence, not assumption: at spec time
  `hackrf_info` (2026.01.3) is installed and reports **no HackRF
  attached**; four `/dev/cu.usbserial-*` devices are present and
  **unidentified**. No scenario may name a gadget until it is
  inventoried (model, serial, TX capability, antenna/load) in
  `docs/inventory/` style. Passive receive/inventory always precedes
  any transmit authorisation.

## Tech Stack

- Host: Python 3 on Kulira, managed with **uv** (repo rule: `uv run`,
  `uv.lock` committed; never system pip). New package
  `tools/kulira-core/` mirroring `tools/korvo-monitor/` and
  `tools/node-commissioner/` layout (flat modules + `test_*.py`).
- No new runtime dependencies in this module. Gadget drivers (HackRF via
  `hackrf` tools, ESP-class USB serial radios, etc.) are separate
  later modules behind the actuator contract; core talks to fake
  actuators in tests.
- Runs are plain files: scenario YAML/JSON in, JSONL log + JSON manifest
  out, under `validation/kulira/<run-id>/` (git-ignored if it ever holds
  credentials — it must not; see Boundaries).
- Fleet truth sources read-only: `docs/inventory/nodes.csv`,
  `docs/inventory/network.csv` (A1=192.168.1.10 … D4, Korvo
  192.168.1.10). Core never writes inventory.

## Commands

```sh
# from repo root, on Kulira
uv sync --project tools/kulira-core
uv run --project tools/kulira-core kulira campaign validate scenarios/false-beacon.json
uv run --project tools/kulira-core kulira campaign run scenarios/false-beacon.json --dry-run
uv run --project tools/kulira-core kulira campaign run scenarios/false-beacon.json
uv run --project tools/kulira-core kulira campaign stop --run <run-id>
uv run --project tools/kulira-core kulira campaign report --run <run-id>
uv run --project tools/kulira-core python -m pytest tools/kulira-core -q
```

`--dry-run` is the default for any scenario touching `plane: rf` or
`targets: live-nodes` until the owner flips that scenario's
`authorised: true` after review. There is no `--force` bypass.

## Project Structure

```
tools/kulira-core/
  pyproject.toml        # uv project, console script `kulira`
  kulira_core/
    __init__.py
    scenario.py         # schema, validation, seed expansion
    orchestrator.py     # run state machine, scheduler, one-attack lock
    actuator.py         # Actuator protocol (app/link/rf), FakeActuator
    safety.py           # limits, interlock, kill-switch watcher
    log.py              # append-only JSONL, hash-chained entries
    manifest.py         # run manifest, baseline before/after proof
    cli.py              # campaign validate|run|stop|report
  scenarios/            # reviewed scenario files, e.g. false-beacon.yaml
  test_scenario.py  test_orchestrator.py  test_safety.py  test_log.py
validation/kulira/<run-id>/   # manifest.json, attacks.jsonl, report.json
```

Scenario shape (illustrative; schema is the contract, JSON in v1):

```json
id: false-beacon-001
seed: 271828
plane: app            # app | link | rf  (rf needs gadget inventory ref)
targets: [B2]         # labels from nodes.csv; or lab-only
attacks:
  - module: kulira-deceive
    action: false-observation
    at_s: 30
    duration_s: 60
    intensity: 1      # graded 1..3, scenario cap enforced by safety
limits: { max_duration_s: 600, require_management_health: true }
authorised: false
```

## Code Style

Follow the repo's host-tool style (`tools/korvo-monitor/bridge.py`):
typed, small, explicit; no hidden globals; time and randomness injected
for tests. Four-space indent, `snake_case`, dataclasses for records.

```python
@dataclass(frozen=True)
class AttackAction:
    module: str          # e.g. "kulira-deceive"
    action: str
    at_s: float
    duration_s: float
    intensity: int       # 1..3

class Actuator(Protocol):
    def arm(self, action: AttackAction) -> None: ...
    def fire(self, action: AttackAction) -> None: ...
    def stop(self, reason: str) -> None: ...   # must be idempotent, <=1 s
```

Safety is not a comment, it is the type system plus one choke point:
actuators are only reachable through `SafetyGate.fire(...)`, which checks
limits, authorisation, and the kill-switch before delegating.

Hash-chained log entry (one per arm/fire/stop/observation):

```json
{"seq": 41, "t": "2026-11-04T12:30:01Z", "kind": "fire",
 "action": {"module": "kulira-disrupt", "action": "drop", "intensity": 1},
 "prev_sha256": "…", "sha256": "…"}
```

## Testing Strategy

- Framework: pytest via uv, beside the code (`test_*.py`), mirroring
  `tools/korvo-monitor/test_bridge.py`. No hardware in unit tests:
  `FakeActuator` records calls; a fake clock drives the scheduler.
- Unit: scenario schema rejects unknown modules/planes, unlabelled
  targets, intensity over cap, RF without inventory ref, and
  `authorised: false` live runs. Seed expansion is deterministic
  (same seed → same schedule, golden test).
- Safety: kill-switch during `fire` → `stop` called, state `ABORTED`,
  no further actions; management-health check failing → run refuses to
  start and aborts mid-run; one-attack lock rejects concurrent campaigns.
- Log: hash chain verifies; a tampered/truncated line fails verification
  loudly, never silently.
- Integration (no RF, no fleet): dry-run of `false-beacon.yaml` against
  the host communication lab produces manifest + report with baseline
  section empty-but-present, labelled `dry-run`.
- Experiment-design tests reviewers will ask about: every claim needs
  a control (same seed, no attack), one changed variable per comparison,
  replication across seeds (seed = replication unit, agents on a team
  are not independent samples), and a held-out check with learning
  frozen — mirroring the communication lab's method. Core enforces the
  paperwork: scenario, seed, control pairing, and artefact retention.
- Live acceptance is a later, separately authorised step per scenario —
  not part of this module's CI. Success there means the *paperwork* is
  right: log matches what the operator saw, stop worked, baseline proof
  (authenticated health from all targeted nodes) is attached.

## Boundaries

- **Always:** seeded + hash-logged actions; passive inventory before any
  gadget is named; management/health plane (authenticated ESP-NOW /
  Wi-Fi health per SPEC-flock-network) checked before, during, and
  after; `stop` ≤ 1 s and idempotent; post-run baseline proof; fictional
  data only; runs labelled simulation/experiment, never presented as
  measured fleet defects without the clean baseline beside them.
- **Ask first:** first live-node run of any scenario; any `plane: rf`
  transmit (gadget, frequency, power, antenna vs dummy load/shielding,
  duration); any intensity > 1; targeting > 1 node; any change to the
  management-health requirement. Transmission only from inventoried,
  legitimate lab radios in a contained setup (shielded enclosure /
  cabled-attenuated / dummy load by default; over-the-air only at
  minimum power, shortest duration, owner present, and lawful on this
  LAN's channels — if containment cannot be shown, the scenario does
  not run). Dedicated jamming/blocking devices are never authorised.
- **Never:** gain or use firmware-deployment, OTA, identity-provisioning
  or per-node-key authority; store credentials/keys in scenarios, logs,
  or the repo; persist anything on a node after a run; attack third-party
  networks/devices or non-fictional data; use any dedicated jamming or
  blocking device, or disrupt anything outside the named targets and
  window (no ambient/broadcast disruption); run
  two campaigns at once; bypass `SafetyGate` from an attack module.

## Success Criteria

1. `campaign validate` accepts the example scenario and rejects, with a
   named reason, each of: unknown module, bad label, RF without gadget
   inventory, intensity over cap, missing seed.
2. Dry-run executes the full schedule against `FakeActuator`/lab with
   zero fleet traffic; manifest, hash-verified log, and report exist.
3. Kill-switch test: stop issued mid-attack halts emission ≤ 1 s,
   run ends `ABORTED`, log shows arm/fire/stop in order.
4. Management-health gate test: with health check forced to fail, a live
   run will not start; forced failure mid-run aborts it.
5. Determinism test: two runs, same seed → identical schedules and log
   action sequences (timestamps excluded).
6. pytest suite green via the Commands above; no test needs a gadget,
   a node, or the network.
7. Capability map updated: `kulira-rf` actuator plane recorded (see
   below), gadget inventory entries created only from observed devices.

## Capability-map change proposed with this spec

Add one row to [CAPABILITY-MAP-kulira-chaos.md](CAPABILITY-MAP-kulira-chaos.md)
and adjust two (owner to confirm with this spec):

| Module id | Responsibility | Depends on |
|---|---|---|
| `kulira-rf` | USB gadget drivers + RF actuator contract: passive inventory/survey, Layer 1/2 impersonation/contention TX under core limits (no jamming devices) | `kulira-core` |

`kulira-disrupt` and `kulira-spoof` then each declare `plane: app|link|rf`
per action; RF actions additionally depend on `kulira-rf`. Build order
becomes `kulira-core` → `kulira-rf` (passive only) → `kulira-disrupt` →
`kulira-spoof` → `kulira-deceive` → `kulira-observe`. RF *transmit*
stays gated per scenario regardless of build order.

## Open Questions

1. Defaults unresolved from the map — confirm or override: first live
   target = host lab, then one node (recommend B2), then fleet; defender/
   trust-scoring work is **out** of Kulira's scope (scored by
   `kulira-observe` only); impersonation includes a credentialed rogue
   (false-beacon style) only as a later gated scenario; whole-fleet
   partition not in any v1 scenario; presenter sees attacks live,
   agents stay blind.
2. Which USB gadgets should be inventoried first? The four
   `/dev/cu.usbserial-*` devices are unidentified — owner to say what
   they are (or authorise read-only enumeration) before `kulira-rf`.
3. RF containment available on this bench: Faraday enclosure / shielded
   box, attenuators/dummy loads, or only low-power open bench? This
   decides whether any `plane: rf` scenario can leave dry-run.
4. Scenario file format: YAML (needs a parser dependency) or JSON only
   (stdlib, uglier)? Recommendation: JSON for core v1.
5. Where do run artefacts live long-term: `validation/kulira/` in-repo
   (small, reviewable) with RF logs trimmed, or out-of-repo storage?

## Next step

Owner approves this spec (and the map change + defaults in Open
Questions 1). Next turn: Phase 2 plan in `tasks/plan.md` for
`kulira-core` only. No code before the plan is reviewed.
