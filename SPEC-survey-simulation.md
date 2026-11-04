# Shared survey simulation

Status: **approved by the owner**, 17 October 2026, via “proceed” in response
to the specification review request. This approves the bounded fictional survey
slice; it does not mark the older campaign proposal as approved.
Implementation plan and checklist: `tasks/survey-simulation/plan.md` and `todo.md`.

Module: a bounded slice of `experiments`, using the existing world-view renderer.
Existing boundaries remain: the engine owns simulated state, `node-platform`
owns physical rendering/health, and `management-console` owns handheld controls.
No new capability-map module is introduced.

## Objective

Replace authored demonstration paths with one host-owned, persistent-in-session
survey scenario for sixteen virtual camera nodes. The presenter selects nodes,
starts a survey, requests return, and watches position and energy evolve in the
same world. An independently rendered camera view is a consumer of that state.

This first slice proves consistent state, explicit commands and repeatable
transitions. It does not claim distributed inference or autonomous collaboration.
Cooperative observations and trust experiments can subsequently consume its
recorded events and snapshots.

## Assumptions

- Mac host first, ordinary Node.js ES modules and built-in HTTP/test facilities;
  no new runtime dependencies. The code should also run on a Linux/Pi host.
- Browser command interface and sixteen views first. ESP32 streaming and LilyGo
  command/status integration follow after this contract and state loop work.
- Invented Cartesian world units, energy points and simulation seconds. No 6S
  capacity, electrical discharge model, kilometres, aircraft performance or
  payload endurance calibration. UI provenance says **fictional survey**.
- Sixteen home sites span a line in the invented world. Scenario data explicitly
  maps node IDs to sites; hardware layout does not imply world location.
- Survey subjects are neutral beacons. This slice does not classify people,
  select attack targets, model enemy fire or connect to legacy KILL sequences.
- Cosmetic camera palettes preserve TV/NV/WH/BH/IR choices; changing a palette
  does not introduce a real sensor model or change detection capability.
- Reloading a browser reconnects to host state; it never resets a sortie or
  replenishes energy. Restarting the process starts a new explicitly identified
  session unless the presenter deliberately loads a compatible replay.

## Behaviour

Each node has a stable ID, home pose, current pose, energy, state, assignment and
transition reason. States are READY, TAKEOFF, TRANSIT, SURVEY, RETURN, LAND,
CHARGING and UNAVAILABLE. READY remains stationary at home; takeoff only moves
forward through its transition. Returning reaches its own home, lands and then
charges. Completing a survey returns the node. The loop never relaunches itself.

The presenter selects one or more READY nodes and a fictional survey site.
Launch is validated atomically: an invalid selection rejects the command with a
reason rather than partially dispatching it. Return applies to selected airborne
nodes and is idempotent. Pause freezes all simulation progression, including
energy and charging. Reset is explicit and creates a new session.

Use a small versioned scenario preset with declared, invented rates/timings.
Energy starts at 100 points, decreases in airborne states and increases only
while charging at home. A declared game reserve threshold triggers RETURN;
it is a simple game rule, not a calculated safe-flight envelope. No battery swaps,
payload classes, route optimisation or one-way expenditure policy in this slice.
At zero airborne energy the node becomes UNAVAILABLE with reason ENERGY_EMPTY;
it does not silently recover. Ground depletion leads to CHARGING instead.

A presenter can mark a selected simulated node UNAVAILABLE. This is an explicit
scenario event, not an inference from a physical panel failing to answer.
No automatic reassignment occurs yet. Preserve separate fields for physical
device health, stream freshness and simulated availability.

Movement uses simple bounded scripted transitions driven by current engine pose
and time; changing a label must not restart the camera. Return starts from the
current position. Paths and animation are game geometry, not a flight controller.
All peers shown in engine mode come from that session's actual simulated state;
do not retain independently generated fixture peers in this mode.

## State, commands and time contract

- A pure fixed-step core accepts validated commands and returns state/events.
  Tick size is 100 ms; command application has a defined tick and sequence order.
  The same engine/scenario versions, seed and command log reproduce the run.
- Snapshot publication is initially 2 Hz; rendering remains 8 FPS using the
  existing bounded interpolation. Engine time and network receipt age are
  distinct. A host clock stall uses bounded catch-up and reports lag; it does not
  silently advance hours or run an unbounded update loop.
- Commands carry session ID and unique command ID. Reject commands for another
  session. Duplicate commands return the recorded result without reapplying.
  Bound deduplication storage; stale command sequences remain rejected after
  their cached result is evicted. Only the engine advances authoritative state.
- Version snapshots separately from legacy world-view v1. Include session,
  sequence, simulation timestamp, seed, node ID, pose, state, energy points,
  destination distance in world units and transition reason. Optional values are
  explicitly null when unavailable, never invented by the renderer.
- Use `D` for destination distance, with world-unit provenance in the surrounding
  interface. Display energy as a game percentage. Replace NR/BINGO in this mode
  with an unambiguous game reserve indication (OK / LOW / RETURN); no claim of a
  realistic point-of-no-return calculation. Exact compact placement is subject
  to a 64×64 visual check before firmware integration.
- Export scenario metadata and accepted commands plus state transitions as
  JSON/JSONL for replay. Invalid commands produce bounded diagnostic records.
  Record seed and engine version; presentation frames need not be logged.
- Bind the service to loopback by default. A same-origin browser client consumes
  state and sends commands. Reject unexpected origins and Host headers; bound
  request sizes, values, node counts and log/session growth. No hardware secrets
  are required. LAN exposure and a device transport are later adapter work.

## Structure and commands

Proposed files:

- `tools/survey-simulator/`: dependency-free engine, scenario, HTTP service, replay.
- `previews/recon-hud/`: optional survey client/view adapter, preserving World view
  fixture and legacy animation modes.
- `validation/survey-simulator/`: state, protocol, replay and browser checks.
- `tasks/survey-simulation/`: implementation plan and completion evidence.

Planned commands (entry points to be implemented; not currently available):

```sh
node tools/survey-simulator/server.mjs --host 127.0.0.1 --port 8767
node --test validation/survey-simulator/*.test.mjs
node tools/survey-simulator/replay.mjs --input run.jsonl --verify
node validation/survey-simulator/browser-check.cjs
```

Existing renderer regression command:

```sh
node --test validation/recon-hud/*.test.mjs
```

Reuse the running preview on 8766; the new service must not replace it. Serve the
survey client from the new service origin so CORS is unnecessary. Browser tests
can use the existing bundled Playwright, with its machine-specific path documented.

## Code style

Pure ES modules with explicit inputs, immutable output snapshots and validation
at boundaries. Keep transport and wall-clock access outside the engine. Example
contract sketch, not an existing API:

```js
const result = applyCommand(state, command);
if (!result.accepted) return result;
const next = advance(result.state, {ticks: 1});
const snapshot = snapshotFor(next, {node: 0});
```

## Acceptance and tests

1. Two browser clients share one session and see the same node state. Refreshing
   either client does not reset energy, positions, assignments or recharge.
2. Selected nodes complete TAKEOFF → TRANSIT → SURVEY → RETURN → LAND → CHARGING
   → READY; unselected nodes remain home. No automatic new sortie occurs.
3. Return from multiple intermediate positions is continuous. Energy and reserve
   transitions are tested at exact thresholds and never leave the 0–100 range.
4. Pause freezes pose, energy, charging and event time. Reset creates a new
   session and old commands/snapshots cannot alter it.
5. Duplicate launch/return, invalid node selections, malformed/non-finite fields,
   oversized input and stale sequence/session data have explicit tests.
6. A recorded run replays to matching state and transition events under the same
   version; incompatible versions fail visibly. Fixed-step results do not depend
   on browser refresh or render frequency.
7. Disconnected browser views show stale state and resume without inventing data.
   Simulated unavailability and transport failure remain visibly distinct.
8. Sixteen views remain legible at 64×64. Measure browser rendering overhead,
   inspect ground/air/return states and energy fields, and run legacy regressions.

## Boundaries and subsequent integration

Always preserve local-only operation, independent displays, explicit provenance,
management credentials and existing update services. Save source and evidence in
the private repository. Never edit frozen release snapshots or silently reinterpret
fictional energy as measured panel or real aircraft battery telemetry.

Ask before broadening to public/LAN hosting, new dependencies or a materially
different simulation model. Physical integration requires a reviewed snapshot
adapter and one-node test before fleet rollout; this specification alone does
not assert that deployed 0.9.0 accepts external world snapshots.

Later slices: authenticated node snapshots and live HUD fields; LilyGo command
and status client; neutral beacon observations with separate truth/belief data;
synthetic message loss/delay/deception; causal replay visualisation. Those remain
separately verifiable extensions under the existing module boundaries.

Excluded: realistic weapon endurance, autonomous attack coordination, damage or
follow-up attack decisions, real aircraft integration and operational mission
planning. The historical campaign draft is not the implementation contract.

## Review questions

No additional hardware or credential information is needed to start this slice.
The owner approved the host/browser-first boundary and fictional reserve
indicator. Implementation planning is recorded separately for review.

## Deployment extension authorised 17 October 2026

The owner requested deployment to the nodes after reviewing the implementation
plan. This authorises building the plan and adding the authenticated snapshot
adapter needed for a one-node canary, followed by verified fleet OTA. The host
remains the simulation authority; firmware 0.10.0 renders supplied pose/metrics
and freezes with STALE after two seconds without updates. A bounded 512-byte
maintenance command carries v2 survey state and up to three simulated peers.
No physical energy measurements or distributed inference are implied. LilyGo
UI integration remains later work; browser commands control this first release.

## Linux reliability increment — 19 October 2026

The owner authorised the reviewed Linux baseline and survey reliability work.
The engine remains session-only JavaScript with the same simulation/replay model.
Browser registration now resumes a tab token and evicts least-recently-used clients
at the 32-client bound. IDs are never reused within a process; evicted envelopes
are rejected. Re-registration does not resend a previous user command.

The bridge explicitly accepts 0.10.0 and 0.10.1, requires `--take-control`, acquires
local per-node locks, and yields after an observed mode/run change. These checks
are not firmware-enforced leases and cannot make status-read/write atomic. A
firmware ownership protocol and physical canary remain required before mixed
controller operation. No hardware rollout occurred in this increment.

See `docs/development.md` for current commands, credential access, evidence and
remaining gates. Earlier Mac paths and planned filenames above are historical.
