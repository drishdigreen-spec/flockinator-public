# World-view renderer specification

Status: **approved by the owner**, 16 October 2026, via “proceed” following
review of this specification. Implementation plan/checklist also approved via the subsequent “proceed”; see
`tasks/world-view/plan.md` and `tasks/world-view/todo.md`.
Scope: a presentation slice of the existing `experiments` module; future device
adapter belongs to `node-platform`. No new capability-map module is introduced.
This does not approve or implement the broader campaign in SPEC-experiments.md.

## Objective

Replace clip-relative camera motion with a continuous camera-state-driven view
of a small synthetic world. Each 64×64 panel depicts its own camera position and
orientation. Terrain persists across views and state changes. A synthetic survey
fixture demonstrates the effect without flight-control or combat-decision logic.

Success means changing an observation label does not rewind the camera, nearby
views share terrain features, and a scripted impact begins at the current pose
and ends against the ground. Preserve the current repeating demo as a separate
mode so the display remains usable during development.

## Assumptions and scope

- Browser first, with sixteen independently rendered 64×64 views. No flashing,
  new network transport, inference integration or controller change in this slice.
- Coordinates describe an invented local world; no real terrain, geographic data,
  aircraft performance, operational routes or sensor specifications are used.
- Camera state is supplied to the renderer. Demonstration paths are authored
  fixtures, not autonomous navigation or decisions derived from the scene.
- Shared terrain is generated from a stable seed and world coordinates, rather
  than the current per-node offsets and clip clocks.
- The initial terrain is a flat textured surface. Occlusion by hills, buildings,
  realistic sensor signatures and photorealistic rendering are not required.
- Peer cues are neutral labelled sightings: ID, projected location or a dashed
  edge-direction indicator when out of view. Limit clutter and distinguish them
  from observation markers. They do not connect peers to ground attack targets,
  allocate roles, express targeting solutions or imply authenticated identity.
- Existing KILL visuals remain in the separate authored demonstration. This slice
  does not connect them to world navigation, targeting or decision policies.

## State and rendering contract

Use a versioned, immutable snapshot containing simulation time, terrain seed,
node identity, camera pose and explicitly supplied visible observations/peers.
World truth and agent reports are separate data: rendering a report does not
make that report true, and the renderer must not act as a classifier.

Use consistent axes, units and angle conventions documented alongside the type.
Bound collection sizes and reject non-finite pose values. Rendering has no device,
network, clock or SD side effects. Given the same snapshot and sample time, it
produces the same pixels. A presentation clock advances independently of labels.

Example intended style (contract sketch, not an implemented API):

```js
const pixels = renderWorldView({snapshot, sampleTimeMs, sensor: 'night'});
```

The snapshot timestamp is distinct from receipt time. Interpolation is bounded;
missing or stale snapshots must visibly indicate stale data instead of allowing
unlimited invented movement. Exact interpolation window and loss threshold are
configuration values to be selected and documented during planning.

## Visual behaviour

- Camera position and orientation determine ground projection and the horizon.
  Ground feature size and movement follow that view consistently.
- Labels such as survey/hold/share may change without changing camera pose.
  An authored loiter path continues forward in time; no clip reversal is needed.
- A synthetic impact transition retains its entry pose, progresses into the
  ground, holds a stationary dirt view, then can enter the existing static ending.
- Peer markers use the same camera projection as other visible scene features.
  Off-screen cues are clipped to the camera area and do not overwrite the HUD.
- The latest compact HUD remains a separate layer. Numeric fields consume explicit
  inputs; the renderer does not calculate energy reserves or safe-return decisions.
  Display missing values honestly. Battery icons and stale values must not imply
  measured hardware or an implemented energy model.
- Keep simulation provenance outside the tiny camera image, native-pixel scaling,
  pause/restart/reduced-motion controls and selectable sensor palettes.

## Structure and commands

Keep browser code in `previews/recon-hud/`, with focused world-view and fixture
modules separated from the existing renderer/scheduler. Tests belong in
`validation/recon-hud/`. Prefer existing ES modules and Node's test runner;
no framework or package dependency is needed for this slice.

From `/Volumes/devops/flockinator`:

```sh
node --test validation/recon-hud/*.test.mjs
uv run --project tools/node-commissioner python -m http.server 8766 --bind 127.0.0.1 --directory previews/recon-hud
node validation/recon-hud/browser-check.cjs
```

Reuse a running preview server. The existing browser-check script covers the
legacy demonstration and must be extended for the new mode. It currently uses a
machine-specific Playwright path; this remains a known tooling limitation.
There is no browser compilation step.

## Acceptance and validation

1. The same seed and snapshot produce repeatable pixels. Node identity alone does
   not alter the terrain; equal camera poses see equal scenery aside from HUD/IDs.
2. Synthetic camera movements give consistent horizon direction and terrain
   scale, with no reset when a status label changes.
3. Two known camera fixtures see the same world landmarks at their expected
   projected positions. Compare geometry as well as screenshots.
4. Impact transitions from multiple poses finish on ground with no visible sky;
   existing blackout/static timings and HUD boundaries retain regression coverage.
5. Peer IDs and dashed off-screen direction cues stay within the camera region,
   obey the marker limit, and never imply an assignment to an attack target.
6. Interpolation, pause, stale snapshots, reconnection and malformed inputs have
   explicit tests. No camera teleport is hidden as a normal label transition.
7. All sixteen views remain usable at the current 8 FPS presentation target in
   the browser. Record measured frame times and dropped frames; do not claim an
   ESP32 frame rate from desktop results.
8. Existing tests and controls continue to work. Inspect representative sensor
   modes and different camera positions in a real browser.

## Boundaries and later work

Always preserve the independent-node view, existing management/update interfaces,
clear provenance and deterministic fixture replay. Keep source and documentation
in the private repository; no credentials or frozen release edits.

An ESP32 port is a later bounded step: build and benchmark on one identified node
with normal networking/audio/storage activity, capture frame time, dropped frames,
heap and watchdog behaviour, then decide whether to optimise or reduce detail.
The current hardware renderer targets 8 FPS; no higher-rate guarantee is made.

This specification excludes autonomous target selection, lethal-action delegation,
strike outcomes/follow-up decisions, operational flight planning, model training,
mission/resource optimisation and connections to real aircraft. Generic inference
adapters and non-weapon cooperative observation experiments require their own
subsequent scope. Existing broader campaign proposals are not approved here.

## Implementation checkpoint

Browser slice implemented as visual study 17 on 16 October 2026. See
`tasks/world-view/todo.md` and `validation/recon-hud/world-view/README.md` for
verification. The state/scope contract above remains authoritative. There is no
ESP32 implementation or performance claim in this checkpoint.

## Approval record

Owner approved this browser-first world-view scope with “proceed”. This approval
does not expand the exclusions above or authorise a physical firmware rollout.

## Hardware extension authorised 16 October 2026

The owner subsequently requested upload to the ESP32 fleet. The local renderer
port and identity-checked OTA rollout are now authorised; follow
`tasks/world-deployment/plan.md`. This extends only the previous physical-rollout
boundary. No broader campaign, inference or operational-control scope is added.

## Mission presentation integration — 17 October 2026

Owner request: retain the automatic mission scenarios and bring shared world
space and relative drone tracking back into those visualisations. This updates
the earlier separate-mode constraint; the approved rendering boundary remains.

- Reuse the existing mission scheduler, orders, variants, communications, terminal
  effects and repeat cycle. No new mission decision or attack policy is introduced.
- During ordinary flight, draw shared seeded terrain using continuous authored
  poses, independent of the reversible state-animation clock. Pose-derived bearing
  and north arrow agree with that camera. Each peer uses its own corresponding pose.
- Takeoff, return and landing are authored presentation transitions. Reserve,
  parked and lost-feed nodes are omitted from airborne peer cues. At most three
  neutral cyan IDs are labelled; offscreen/rear cues remain distinct.
- Terminal close-ups and crash effects retain their cinematic treatments;
  contacts/classification overlays remain scripted, not world-derived inference.
- Browser and node implementations are covered by continuity, peer consistency,
  terminal-effect regression and frame-bound tests. Test native and hardware
  builds, then an A1 canary before rolling out the identical image to all nodes.
- No transport/protocol change or LilyGo firmware change is needed. Mission launch
  commands continue to work. Shared positions are deterministic local fixtures,
  not measured physical locations or received A2A telemetry.

## Presentation map extension — 17 October 2026

Extend the existing presentation map with full-screen and a separate read-only
map tab. The map consumes the same mission frame as the browser camera grid;
TX orange / RX green reuse the existing double-pulse timing and colors. A separate
tab follows its originating preview session, and freezes visibly when disconnected.
Red/blue contact annotations are authored report illustrations with explicit
provenance, not inferred targets or persistent world truth. Keep marker location
and interpretation separate: existing camera contacts have no supplied world
coordinates, so map annotations must be labelled illustrative placements.
No mission-target assignment, attack GO controls, new mission planning or inference
integration are included. No hardware or LilyGo firmware change in this slice.
Verify cross-tab consistency, pulse timing, stale source handling, full-screen
entry/exit, mobile layout and existing preview behavior.

### Map lifecycle and terrain correction — 17 October 2026

Hold completed cinematic nodes at their terminal pose through static and blank
intermissions. Returned/reserve nodes remain parked; lost markers retain their
status until the next cycle. Seeking directly into an intermission must produce
the same result as continuous playback. Use the camera's seeded ground pattern
for cosmetic overhead terrain, retaining fictional units and existing paths.
This correction does not add range envelopes, allocation or identification logic.
