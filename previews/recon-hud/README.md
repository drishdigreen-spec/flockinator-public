# Flockinator reconnaissance HUD — animated visual preview

Created 16 October 2026 (Sydney), following approval of the reconnaissance visual direction. All imagery is procedural and synthetic, rendered into a 64×64 RGBA buffer and displayed with nearest-neighbour scaling. No external assets, network services or installed dependencies are required by the page.

Latest browser revision (**visual study 17**): choose **World view** in the Scene
menu. All sixteen cameras now render shared seeded terrain from continuous pose
snapshots, independently of animation labels. The original Mission loop remains
the default and is unchanged.

World controls: select a node, interrupt/resume its updates, or trigger an impact
from its current displayed pose. Pause freezes the entire preview clock; Restart
restores the authored paths and seed. Sensor and HUD palettes remain selectable.
The native-pixel option shows the actual 64×64 resolution.

The world fixture publishes at 2 Hz; presentation interpolates 500 ms behind it.
A 1.5-second receipt gap freezes and marks the node STALE, clearing its sightings.
Resume blends for 750 ms with a RESYNC label. Invalid or out-of-order data cannot
replace the last valid state. History is capped at four snapshots per node and
performance samples at 256 batches. The page reuses its sixteen frame buffers.

Peer IDs are neutral cyan sightings. Dashed edge cues indicate off-screen peers;
R prefixes a rear sighting. Up to three labels appear in stable ID order, with
an omitted count. White/black pixels are fixed neutral landmarks. These are
explicit fixture reports, not inferred classifications. Positions and altitude
use fictional units. D-- / NR-:-- / BAT? mean no corresponding value was supplied.
IR currently uses the NV terrain palette with an IR header; no IR sensor model
or strobe detection is implemented in World view.

Impact is an authored effect, not dynamics: two seconds to ground, one second
stationary dirt, five seconds of static, then stationary dirt until Restart.
These are source times; the sampled display follows the interpolation delay.
Camera position/orientation at entry comes from the selected displayed view.

Implementation: `world-view.mjs` (pure validation/projection/pixels),
`world-playback.mjs` (bounded sampling/effects), `world-fixture.mjs` (local data)
and `app.mjs` (controls/render scheduling). Snapshot coordinates are +X east,
+Y north, +Z up; heading clockwise from +Y, pitch positive up, roll rotates camera
right toward up. There is no external snapshot endpoint in this milestone.

Verification from repo root:

```sh
node --test validation/recon-hud/*.test.mjs
node validation/recon-hud/browser-check.cjs
node validation/recon-hud/world-browser-check.cjs
```

Sixty tests and both browser harnesses pass. Browser evidence, fixed-seed timings
and known limitations: `../../validation/recon-hud/world-view/README.md`.
The browser milestone itself did not change firmware. A subsequent authorised
port is now firmware 0.9.0; see `../../docs/validation/world-deployment/README.md`
for real ESP32 measurements and rollout evidence. Browser and device results
are recorded separately.

Previous browser revision (**visual study 16**): CRASH tumbles down into textured
dirt, then holds a stationary ground-only image until SIGNAL LOST starts at
three seconds. No horizon or reticle remains after impact. The HUD stays upright
and the lower detail changes from TUMBLE to GROUND. All ten variants and sensor
modes retain this ending. Browser only; firmware remains unchanged.

Animation: `crash-ground.gif`; storyboard:
`../../validation/recon-hud/crash-ground.png` (0, 0.5, 1, 1.5, 2.75, 3.5 seconds).
Regenerate with `node validation/recon-hud/export-crash-ground.mjs` from the root.

Visual study 15: KILL now enlarges the ground and
red contacts together, centres the selected contact, removes the horizon through
close-up framing, and fills the camera area before blackout. The ten-second
countdown, red perimeter, black interval and SIGNAL LOST ending are retained.
Other states keep single-pixel people. This supersedes the earlier fixed-horizon
and single-pixel KILL treatment. Preview only; no firmware rollout.

Animation: `close-approach.gif`; storyboard:
`../../validation/recon-hud/close-approach.png` (0, 4, 7, 9.99, 10.5, 12 seconds).
Regenerate with `node validation/recon-hud/export-close-approach.mjs` from the root.

Previous browser revision (**visual study 14**): compact node / arrow / TV-NV-BH-WH /
heading / D00 header, NR0:00 → BINGO beside the state, and battery moved to the
last row. Distance and return values are **scripted samples**, not calculated
aircraft telemetry. Missing and overflow values are explicit. The countdown uses
chronological time while camera clips can reverse. No firmware has been changed.
ASSESS hover/orbit presentation is recorded as a future idea only.

Visual study 13: people are separate single-pixel ground
contacts, with small clusters for groups. Unidentified contacts use contrasting
black/white, scripted classified contacts use red/blue. The thermal blob and
filled central beacon are removed; selection outlines remain separate. This
supersedes earlier descriptions below of enlarged beacon bodies. Historical
GIFs/videos and deployed node firmware have not been regenerated by this change.
Comparison: `../../validation/recon-hud/pixel-contacts.png`. Renderer regression
suite: `node --test validation/recon-hud/*.test.mjs` (45 passing tests).

Start from `/Volumes/devops/flockinator`:

```sh
uv run --project tools/node-commissioner python previews/recon-hud/serve.py
```

The preview server disables caching and versions the entire module graph to prevent mixed old/new assets in existing tabs. Reload after edits.

Open `http://127.0.0.1:8766/`. The default **Mission loop** runs complete repeating missions; **State catalogue** retains the earlier animation cycle. Select any of the sixteen nodes to enlarge it. Pause/restart the sequence, hold a scene, change palettes or choose native pixels. Reduced-motion preference starts paused. Node positions match the physical label layout: A1/B1/C1/D1 across the first row.

Each of the seventeen states has ten animation treatments, giving 170 state/variant combinations. **Variant → Random · all ten** selects independently per node and state occurrence. Each node uses all ten in shuffled order before reuse, with no immediate repeat at the boundary. A variant stays fixed throughout an occurrence; Restart replays the same session and reloading creates a fresh selection seed. Use the numbered selector to inspect a specific treatment; its name appears in the inspector.

| Variant | Treatment |
|---|---|
| 01 | Steady glide |
| 02 | Left bank |
| 03 | Right bank |
| 04 | Climbing |
| 05 | Descending |
| 06 | Weaving |
| 07 | Gusty flight |
| 08 | Wide turn |
| 09 | Low approach |
| 10 | Survey sweep |

These treatments vary bank/pitch, ground speed, observation trajectory and search direction. KILL uses different zoom easing/magnification; CRASH varies roll direction and speed; static has a variant-specific noise seed. EMPTY and NOLINK retain distinct held views. State meanings, ordering, blackout/static duration and TX/RX timing/colours remain consistent. The flight/state sequence is scripted; the variants are selected randomly.

- `recon-hud.gif`: 18-second loop, six states, 8 FPS; 64×64 source enlarged to 384×384.
- `storyboard.png`: six-state contact sheet from the same renderer.
- `events.gif`: 56.5-second loop of ENGAGE, LOST, KILL, CRASH, EMPTY and NOLINK at 8 FPS. KILL lasts 16.5 seconds; the other states last eight seconds.
- `events-storyboard.png`: contact sheet of the six additional event states.
- `horizon.gif`: 40.5-second demonstration of forward flight, zoom/blackout and inverted crash using the VDI-inspired scene.
- `horizon-storyboard.png`: level, banked, engaged, zoomed and inverted views.
- `variants.gif`: all ten treatments side by side through SCAN, CRASH and KILL (28.5 seconds); `variants-storyboard.png` is the SCAN contact sheet. Positions run 01–05 across the top, 06–10 across the bottom.
- `variants.mjs`: ten motion profiles and deterministic shuffled selection.
- `renderer.mjs`: deterministic procedural horizon/ground texture, crosshair, observation brackets, bitmap font and status overlays.
- `app.mjs`, `index.html`, `style.css`: interactive preview without a framework.

Validation evidence is in `validation/recon-hud/`: 18 palette/state cases verified correct dimensions, opaque pixels, deterministic rendering and animation; six state images differ. Isolated Chromium checks passed panel count, actual 64×64 canvas buffers, pause, selection, palette, native sizing, keyboard focus, reduced-motion start and no horizontal overflow at 320/768/1024/1440 pixels. Console was clean. Desktop/mobile screenshots were visually inspected. These checks cover the preview, not ESP32 rendering cost or physical LED brightness/colour reproduction.

The original flight preview includes twelve states, extended by five coordination states. ENGAGE closes the reticle around a fictional beacon; LOST drifts it out of view and searches. KILL (internal key ZOOM) locks onto the centred beacon and enlarges only that beacon and its brackets for ten seconds with a solid red one-pixel border and 00:10-to-00:01 countdown, blacks out the entire panel for 1.5 seconds, then shows five seconds of animated static with SIGNAL LOST. CRASH rolls the camera through 180 degrees and holds; at three seconds it enters the same five-second static ending. EMPTY drains the simulated battery and dims/stops the camera. NOLINK retains the last view and displays its age, independently of battery state.

Extension validation: four Node tests passed, including blackout boundaries, frame recovery, crash rotation, distinct battery/contact behaviour and deterministic opaque rendering for all twelve states at six event phases. Chromium checks passed all twelve scene controls, the visible blackout/recovery, existing controls and responsive/reduced-motion behaviour with a clean console. The event storyboard and desktop screenshot were visually inspected. Evidence: `validation/recon-hud/events-green.log`, `browser-checks.json` and `events-desktop.png`.

The subsequent horizon revision replaces overhead buildings with a plain dark sky, bright horizon and sparse perspective ground patches. Scripted pitch and bank move the attitude scene beneath the reticle. Ground flow suggests motion; it does not encode terrain or measured airspeed. It is inspired by the F-14 Vertical Display Indicator, described in section 5.1 of [Laminar Research's F-14D simulator manual](https://www.x-plane.com/wp-content/uploads/2025/01/X-Plane_F14_Pilot_Operating_Manual.pdf), and adapted for 64×64 readability. All GIFs/contact sheets have been regenerated in this style. Reproduce exports with `node validation/recon-hud/export.mjs` (requires FFmpeg); verify with `node --test validation/recon-hud/events.test.mjs` and, with the local server running, `node validation/recon-hud/browser-check.cjs`.

The existing flock firmware was not changed. Next hardware increment is a port of the approved pixel renderer and a one-node readability/performance check, followed by fleet deployment. Mission messages, trust decisions and A2A behaviour require the separate network/runtime contracts described in `docs/design/reconnaissance-swarm-experiment.md`. Scripted SHARE/DOUBT scenes are not evidence of live communication or autonomous decisions.

The horizon revision also fixes a pause timing race exposed by browser validation: pausing now renders the current time immediately and stops scheduled redraws, so no final frame arrives after the pause click.

Communication border: each scripted message produces two paired perimeter flashes, orange TX (`#ff8a24`) and green RX (`#32ed70`), with 250 ms on / 125 ms off / 250 ms on timing. SHARE cycles through sender/receiver pairs every two seconds; the full sequence chooses SHARE senders and available recipients. Other standalone scenes stay quiet. A transient TX/RX peer label accompanies the cue. The one-pixel perimeter leaves all text inside it. `communication.mjs` schedules the preview events; renderer input `communication: {direction, age, peer}` keeps the overlay separate from mission state. `communication.gif` shows A1 transmitting to B2. No live network integration is implied.

Validation: `node --test validation/recon-hud/events.test.mjs validation/recon-hud/communication.test.mjs` verifies pulse boundaries, exact border thickness/colour, blackout interaction and matching endpoints. Browser checks also inspect the paired orange/green canvas borders in SHARE and capture `validation/recon-hud/communication-desktop.png`.

`signal-lost.gif` shows the complete KILL and CRASH sequences (24.5 seconds total); `signal-lost-storyboard.png` shows their stages. Both full-sequence scheduling and selected-state replay preserve the full five seconds of static. Noise is deterministic per node and animation frame, with a dark, upright SIGNAL LOST banner and no stale flight readouts. Ten renderer/scheduler checks pass, including exact static duration and sequence boundaries; browser checks cover both static endings, changing noise and preserved banner visibility.

Variant validation: `node --test validation/recon-hud/events.test.mjs validation/recon-hud/communication.test.mjs validation/recon-hud/variants.test.mjs` passes all fourteen tests. Rendered clip fingerprints verify ten distinct animations for every state; selection tests cover all sixteen nodes and twelve states over 100 occurrences each, including shuffled coverage and repeat boundaries. Browser checks verify all ten selector choices, independent node assignments, stable paused selection, existing event controls and responsive layouts. Rebuild the comparison with `node validation/recon-hud/export-variants.mjs`. Other exports use treatment 01 as their reference.

## Scripted coordination demonstration

Select **Scene → Coordination demo** for a coherent twelve-second presentation across all sixteen nodes:

- 0–2 seconds: ALERT, one source broadcasts to all fifteen receivers with paired orange/green double pulses.
- 2–4 seconds: PRIORITY, show fictional beacon labels P1 and P2 with the preset P1 highlighted.
- 4–6 seconds: two CLAIM nodes send their requests to the source.
- 6–10 seconds: ASSIGN identifies one preassigned observation owner; fifteen YIELD nodes show the same owner's ID. The announcement is broadcast once.
- 10–12 seconds: the owner observes and the other nodes resume survey.

The next loop rotates the fixture's participants. `coordination.mjs` contains a presentation timeline and fixed roles; it does not rank real objects, compute threat/value scores, allocate weapons or control aircraft. The preview demonstrates how priority/ownership/duplicate-claim information could be communicated visually. The five new states also appear in the full sequence and can be inspected individually, each with ten variants. Outside the coordinated demonstration, standalone ASSIGN/YIELD use B2 as their reference owner; only the coordinated mode represents a complete shared transaction.

`coordination.gif` records the twelve-second fleet animation; `coordination.png` captures the owner/yield stage. Rebuild with `node validation/recon-hud/export-coordination.mjs`. All seventeen tests pass with `node --test validation/recon-hud/events.test.mjs validation/recon-hud/communication.test.mjs validation/recon-hud/variants.test.mjs validation/recon-hud/coordination.test.mjs`. Checks include all 170 animation combinations, one source/fifteen matching receivers, paired claims and exactly one scripted owner. Browser validation covers broadcast borders and owner/yield labels in addition to prior controls and failure endings. Live flock firmware remains unchanged.

KILL displays a countdown from 00:10 through 00:01 during its ten-second zoom, replacing the VIEW magnification readout. A solid red one-pixel border surrounds the approach and the initial bank/pitch is held to give a fixated view. The 1.5-second blackout and five-second SIGNAL LOST ending follow. `kill-countdown.gif` shows one complete cycle; all ten variants use the same countdown.

Latest KILL validation: eighteen renderer/coordination tests pass, including the solid red perimeter across all ten variants, timer preservation when a communication event is supplied, ten-second approach, 1.5-second blackout and five-second static ending. `kill-countdown-storyboard.png` shows countdown, blackout and SIGNAL LOST stages.

## Repeating mission loop

The default scene now runs a shared fleet lifecycle:

1. Flash MISSION APPROVED for two seconds, then display survey/report/keep-clear instructions for four seconds.
2. Active nodes take off over six seconds, then fly outbound for twenty seconds before searching; reserve nodes stay grounded.
3. Fly for 64 or 96 seconds. Nodes alternate searching, observing and reporting, with a twelve-second scripted coordination exchange in each 32-second flight block.
4. Each node ends with a seeded random KILL, CRASH or EMPTY visual, with a 0–4-second stagger. These presentation outcomes do not depend on real sensor observations or target valuation.
5. Finished nodes stay black. Once the last ending completes, the entire fleet remains completely black for exactly five seconds, then the next MISSION APPROVED flashes and the cycle repeats.

`mission.mjs` builds reproducible timelines from the session seed. Per-node/per-state variant visit counters preserve the shuffled-ten selection across missions. A continuous camera profile/time is held throughout each flight so changing state overlays does not reset the horizon or ground flow. In Mission loop, the Variant selector overrides the state animation treatment while the background keeps its flight profile for continuity. Restart begins the same seeded mission again. Reloading chooses a new session seed.

KILL now magnifies only the central beacon and brackets. Its horizon/background/pitch rungs retain their scale; the ten-second timer, solid red border, 1.5-second blackout and five-second static ending are preserved. This corrects the earlier whole-scene zoom.

`mission-loop.mp4` records a complete mission and the next approval in real time; `mission-flight.png` shows the fleet in flight. Export with `node validation/recon-hud/export-mission.mjs`. Validate with `node --test validation/recon-hud/*.test.mjs` and `node validation/recon-hud/browser-check.cjs`. All 40 renderer/scheduler tests pass, covering complete lifecycle boundaries, ≥60-second flights, terminal outcomes, exact black interval, deterministic replay, camera continuity and fixed horizon position/thickness during KILL. Browser checks confirm Mission loop is the default and retain prior interaction/event coverage. Live ESP32 firmware is unchanged.

## Forward–reverse playback

HOLD, SCAN, SEEN, SHARE, CHECK, DOUBT, ENGAGE, LOST, ALERT, PRIORITY, CLAIM, ASSIGN and YIELD now use four seconds forward, four seconds backward, repeating. Cosine easing slows each turnaround. One selected variant persists throughout the repeated passage. Ordinary mission segments last twenty seconds; coordination retains its twelve-second storyboard. Camera position carries across state changes while overlays change to the next status.

`playback.mjs` keeps reflected visual time separate from chronological time. KILL, CRASH and EMPTY remain forward-only; NOLINK remains frozen with an increasing age. Countdown, message direction, orange/green double flashes and mission progress never reverse. Reversing LOST may bring the fictional marker back into view without changing the LOST label; this is a visual loop, not a reacquisition event. Tests compare mirrored frames across all thirteen reversible states and ten variants, verify repeated mission frames and continuous boundary positions, and retain terminal/message timing coverage.

Takeoff is explicitly forward-only: ground fills the initial camera region, then sky and horizon appear during the six-second ascent. Its attitude interpolates to the first airborne frame without pitch oscillation during ascent. A rendered-pixel regression covers all ten profiles and sixteen node positions, plus monotonic altitude/time and continuity into flight. `takeoff-storyboard.png` shows ascent at 0, 2, 4 and 6 seconds.

## Recovery, reserves and sensor views

The catalogue now has 25 states with ten selectable treatments each. LOITER draws either an orbit or a grid-pattern survey, advancing the route marker forward. R2B plays for eight seconds, LAND descends for six seconds, and CHARGE fills the simulated battery over an eight-second pad sequence. These recovery animations do not reverse. Recharge time is deliberately compressed for presentation.

Each seeded mission keeps two nodes in STANDBY; their altitude remains zero, and they are excluded from active observation ownership. Active nodes receive a scripted recovery or one of the existing failure endings. Recovered nodes wait blank after their charging sequence; the whole fleet still receives the five-second blank interval before the next mission. Reserve nodes can receive broadcast cues while remaining grounded.

Sensor selection is independent of state and HUD palette. Mission auto cycles CAM, WH, BH and NV every five seconds during search, with per-node offsets. IR remains available as an explicit selection. Explicit selection applies one view across the fleet. Thermal renders grayscale synthetic imagery, with inverted polarity between white-hot and black-hot; HUD marks and communication borders keep their colours. IR shows an optical pulse and a cyan diamond labelled IR CUE, without automatically assigning friendly identity. The pulse clock remains chronological even when visual motion reverses. Parked/status-only displays do not show camera imagery.

The recovery/sensor regression checks ordering, reserve exclusions, descending altitude, charging progress, thermal polarity, mode-independent TX/RX colours and chronological IR pulses. Browser coverage includes each new scene and the sensor selector. No firmware or physical charging control is changed.

## Friendly and confirmed-target designations

Closed one-pixel squares use fixed blue (`#4488ff`) for friendly and red (`#ff3030`) for confirmed target designations in every sensor view and HUD palette. TARGET provides inspection of the red marker; ENGAGE and KILL also use it. Unconfirmed SEEN/CHECK observations stay neutral, and an IR detection stays a cyan diamond without implying an identity decision. FRIEND provides the blue marker plus a broadcast demonstration.

At second 12 of every 32-second mission flight block, a scripted active source broadcasts one friendly report. All nodes receive the same synthetic screen location and source ID, with a four-second warning. The message event gives one orange sender and fifteen green receivers the established double flash. Reserve nodes display the warning as text while remaining on their pad. Status animations and mission clocks continue independently; the warning does not assert local verification by every receiver. The fixture clears at second 16. These events remain synthetic and do not implement sensor classification or real A2A messaging.

## North indicator

The spare header area now contains N and a five-pixel arrow. It uses eight orientations, rotating opposite the simulated heading so north points left when facing east. Numeric heading and the arrow share one synthetic heading derived from signed flight-profile bank; this is a visual motion cue, not a navigation model. The arrow stays visible in thermal/IR modes alongside their sensor labels, follows reversed visual motion, freezes with held camera frames, and is absent from parked/title/blank/static displays. Tests cover cardinal directions, wrap, bounds, turn sign, sensor independence and held feeds.

## Deployment before search

Mission timing is now approval (2s), orders (4s), takeoff (6s), DEPLOY (20s), survey (64–96s), endings, then the five-second gap. `deploymentDuration` and `searchStart` are exported from `mission.mjs` to keep validation and schedules aligned. DEPLOY advances forward continuously and suppresses sighting cues and report broadcasts. The first survey block uses SCAN/LOITER only, with unclassified ground contrast features appearing four seconds into the sweep.

CAM adds a daylight sky/terrain palette. The header identifies CAM / WH / BH / NV / IR while retaining heading and the north arrow. Auto mode cycles the first four at five-second intervals with a node offset; explicit sensor selection overrides the view but cannot enable sightings during takeoff/deployment. Small contrast dots are synthetic scene features, not classification results. Reserve nodes remain on their pads. The complete mission export includes the additional twenty-second deployment.
