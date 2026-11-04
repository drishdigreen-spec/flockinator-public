# Reconnaissance HUD preview

Owner approved proceeding with the reconnaissance visual direction on 16 October 2026, specifically animated crosshairs, simulated flight and compact status labels. This is the visual-storyboard increment of `docs/design/reconnaissance-swarm-experiment.md`; it does not implement or deploy the future message/agent protocol.

Contract: each panel renders exactly 64×64 pixels, enlarged without interpolation. Six states (HOLD, SCAN, SEEN, SHARE, CHECK, DOUBT) use synthetic terrain, camera drift and moving observation brackets. Identity, SIM and short status remain legible. Distinguish an observation reticle from a second conflicting claim. The sixteen views remain independent; do not tile one image across them. Render at no more than eight updates per second. Provide play/pause, selected-node enlargement, state selection, a true native-size view and three palette options. Honour reduced-motion settings with initial pause. All figures/messages are scripted visual examples, not live telemetry, communication or inferred trust.

Use procedural pixel graphics so the visual style can later be ported to the node renderer without per-frame SD access. No third-party imagery, fonts, remote requests or new packages. Existing pixel-font conventions and the physical panel's 64×64 constraint are the design references. Layout: panel array as primary content, selected-node inspection beside it, controls above; stack at narrow widths, preserve keyboard focus and labels. Reject tiny multi-gauge dashboards and continuous whole-panel flashing.

Validation: deterministic renderer checks, 64×64 buffer bounds, state/palette differences, native pixel scaling, browser controls, pause, reduced motion, responsive layouts and console errors. Export an animated GIF and storyboard image from the same renderer. No live node is flashed by this preview.

Extension requested by owner: add simulated ENGAGE, LOST, ZOOM, CRASH, EMPTY and NOLINK. ENGAGE closes brackets around the fictional beacon. LOST loses its marker and searches. ZOOM magnifies the scene, goes entirely black briefly, then shows NO FEED. CRASH rotates the camera image through 180 degrees and freezes it, retaining upright status labels. EMPTY drains the simulated battery and dims/stops the view. NOLINK freezes the last synthetic camera frame and shows its increasing age; it is distinct from battery depletion. Eight-second event cycles are presentation timing only. Explicit scene selection starts the chosen event at its beginning. Keep the external inspector explanation visible during full-panel blackout.

Owner-directed visual revision: replace overhead buildings with a forward-looking, F-14 VDI-inspired attitude scene. A continuous bright horizon separates plain dark sky from shaded ground with sparse, perspective-projected moving trapezoid texture. Scripted pitch shifts the horizon vertically and bank rotates both horizon and ground; fixed central symbology makes attitude readable. Keep all twelve event behaviours, identity/status bands, palettes, 64×64 resolution and eight-FPS ceiling. The ground texture is an orientation/motion cue, not mapped terrain or measured speed. This is a stylised adaptation, not an instrument reproduction. Validate the existing event suite and browser checks, visually inspect banked/inverted views, and export an updated animation. Reference: Laminar Research F-14D simulator manual, section 5.1 VDI mode, https://www.x-plane.com/wp-content/uploads/2025/01/X-Plane_F14_Pilot_Operating_Manual.pdf .

Label revision: display KILL for the zoom/blackout event in the panel, selector and inspector. Retain the internal ZOOM key and existing animation timing.

Communication cue requested by owner: overlay a single-pixel perimeter at coordinates 0/63, orange for TX and green for RX, on corresponding nodes. Each scripted message drives one paired event, with two synchronised pulses (250 ms on, 125 ms off, 250 ms on). Fixed colours apply in every palette. Keep text inside the perimeter. SHARE preview cycles through sender/receiver pairs every two seconds; full sequence emits from a node currently in SHARE to an available recipient. Failure scenes do not fabricate successful reception. Other standalone scenes remain quiet. The renderer accepts direction/age/peer separately from mission state so later real TX/RX events can use the same cue. Pause freezes the pulse; scene selection resets the demonstration. Validate perimeter thickness, both pulse windows, palette independence, matching endpoints and frame/blackout regressions. These are scripted interactions until connected to live transport events.

Signal-loss ending requested by owner: CRASH rolls and holds for three seconds, then displays animated static and an upright SIGNAL LOST banner for exactly five seconds. KILL retains its four-second zoom and 1.5-second blackout, then shows the same five-second ending. CRASH remains an eight-second scene; KILL becomes 10.5 seconds so static is not cut short. Both standalone replay and full sequence use these durations. Static is seeded per node/frame, low-intensity monochrome noise with a dark banner behind the text. Preserve node identity and original event label; no stale flight telemetry is shown during static. Existing pause, communication overlay and native-resolution behaviour remain available.

Ten-variant revision requested by owner: every one of the twelve states has ten defined motion treatments (120 state/variant combinations). Vary attitude, ground flow, observation paths, search direction, zoom easing, crash roll and noise seed as appropriate. Choose a stable variant once per state occurrence, independently per node, using seeded shuffled sets of ten. Exhaust all ten before reuse and avoid the same variant at a set boundary. A page-session seed gives fresh selections on reload; Restart replays that session. Provide Random / 01–10 controls and the selected variant's name outside the pixel panel. Preserve state ordering, state meaning, failure timing, colour semantics and paired communication cues. Verify ten distinct rendered clips per state, deterministic replay, independent node choices, fixed selection within an occurrence, no-repeat coverage and all prior renderer/browser checks. This remains a browser preview.

Coordination storyboard requested by owner: add ALERT, PRIORITY, CLAIM, ASSIGN and YIELD, each using the ten visual treatments. Add a coherent twelve-second Coordination demo: broadcast a fictional beacon alert (0–2s), show preset P1/P2 priorities (2–4s), animate two scripted claims (4–6s), show one preassigned observation owner and yielding peers (6–10s), then return to observation/survey (10–12s). Fixed fixtures determine source, claimant and owner; no sensor classification, military target ranking, weapon control or operational allocation algorithm is implemented. Orange TX/green RX double pulses represent a single broadcast reaching its recipients, or a paired claim message. All identities refer to the same storyboard event. Existing full-sequence and standalone controls remain available, with broadcast cues for ALERT/ASSIGN and all previous timing constraints intact.

KILL label refinement: replace VIEW magnification with a visible 00:04 → 00:03 → 00:02 → 00:01 countdown, one second per value, during the four-second zoom. Then retain the 1.5-second blackout and five-second SIGNAL LOST ending. All ten variants share this timing.

KILL approach refinement: countdown starts at 00:10 and runs to 00:01 over ten seconds. Keep the beacon centred, hold the initial bank/pitch attitude to remove searching motion, and progressively magnify the view. A solid red one-pixel perimeter overrides TX/RX flashes during this approach; the timer remains visible even if a communication overlay is supplied. At ten seconds the image goes black for 1.5 seconds, then shows five seconds of SIGNAL LOST static. Total KILL scene duration is 16.5 seconds. All ten motion variants preserve these timings.

Repeating mission presentation: default to a coherent fleet mission rather than cycling the catalogue. Each mission has a two-second flashing MISSION APPROVED card, four-second readable survey instructions, six-second takeoff, 64 or 96 seconds of searching/observation/reporting including scripted coordination exchanges, then a seeded random KILL/CRASH/EMPTY ending per node. Terminal starts can be staggered by 0–4 seconds. A finished node stays blank; after the last ending completes, all sixteen are completely black for exactly five seconds before the next approval card. All choices replay from the session seed; each state visit uses the existing per-node shuffled-ten selection. Keep a continuous camera motion profile and time across state changes; state variants affect overlays without jumping the horizon/ground. Takeoff raises the simulated altitude from zero and smoothly enters flight. This is a fictional presentation timeline, not flight or mission-control logic.

KILL zoom correction: magnify only the centred beacon and its brackets. Background/horizon/pitch rungs retain their pixel scale and line thickness, with attitude held during fixation. Retain the ten-second timer, red border, blackout and static timings. Validate full mission boundary/restart behaviour, ≥60-second flight duration, terminal outcomes, exact blank gap, continuous camera inputs and fixed horizon pixels during KILL. Keep catalogue and individual-state previews available for inspection.

Reversible playback requested by owner: HOLD, SCAN, SEEN, SHARE, CHECK, DOUBT, ENGAGE, LOST, ALERT, PRIORITY, CLAIM, ASSIGN and YIELD use a four-second forward visual passage followed by the same passage backwards, repeating with eased turnarounds. Keep one variant through repetitions. Ordinary mission status segments last twenty seconds to demonstrate forward/reverse/forward playback; the scripted coordination schedule remains unchanged. Carry the camera's visual position across segment boundaries. The chronological mission clock, message events and status labels do not reverse. KILL, CRASH and EMPTY remain forward-only; NOLINK retains its frozen image/increasing age. Validate mirrored rendered frames for all thirteen reversible states and ten variants, continuous camera position at boundaries, forward-only terminal timing and unchanged communication pulse windows.

Takeoff correction: takeoff is a single forward-only six-second reveal, never a reversible status clip. Start with ground filling the camera region and the horizon above its top edge; reveal sky and the horizon as altitude increases. Interpolate toward the first airborne attitude without the ordinary pitch oscillation during ascent, then join the flight scene at the same camera position and attitude. Validate monotonic altitude/time and horizon reveal across all ten profiles and all sixteen node positions, including continuity into flight.

Owner-requested recovery and sensor-view extension: add LOITER (looping orbit or grid-pattern visual), forward-only R2B and LAND, then landed CHARGE; add STANDBY for two scripted reserve nodes per mission. Other nodes retain the long survey flight and receive seeded return/land/recharge or existing failure endings. After recovery completes, a node waits for the common five-second mission gap. These paths are presentation fixtures, not navigation or allocation algorithms. LAND lowers altitude to zero and settles into a ground-filled view; CHARGE visibly fills the battery. Keep all ten selectable visual variants.

Provide a Sensor view selector independent of scene and HUD palette: Night vision, Thermal (white-hot), Thermal (black-hot), and IR strobe. Thermal changes the camera region to monochrome with synthetic heat patches while text and TX/RX colours stay legible. IR renders a pulsing cyan diamond around a scripted beacon and an IR CUE label; an IR sighting alone does not assert friendly identity. Mission auto mode shows different scripted sensor views across nodes and flight segments. Preserve simulation labels, pause/restart, reduced motion and the strict 64×64 canvas. Test recovery ordering, reserve nodes, sensor-mode independence, thermal camera pixels, chronological strobes and prior mission/communication timing. Preview only; no device firmware deployment.

Designation colour revision requested by owner: use a closed, one-pixel blue square around a scripted friendly location and a closed, one-pixel red square around a scripted confirmed target. Unconfirmed observations retain neutral marks; IR detection alone remains a cyan cue. Add FRIEND and TARGET inspection states. During each mission flight block, one active fixture node broadcasts a friendly report at second 12; the common friendly location and report source remain visible on recipients for four seconds, with one orange TX / fifteen green RX double-pulse event. This is a fixed presentation event, not a classifier, friend-or-foe protocol or targeting decision. Keep the warning distinguishable from the existing state, and show a text warning on parked reserve displays. Preserve red KILL approach perimeter and countdown priority; terminal and blank screens do not invent reception. Validate one-pixel closed outlines in all sensor views/palettes, paired broadcast timing, consistent source/location, and clearing at the end of the warning window.

North indicator requested by owner: use the spare header space for a small N plus a rotating five-pixel arrow. North points up at heading 000, left at 090, down at 180 and right at 270; use eight directions for legibility at native resolution. Derive the arrow and numeric heading from the same synthetic heading, with signed turn motion following the existing flight profile. Sensor labels remain visible alongside the arrow. Keep it outside camera overlays and TX/RX borders, freeze it with held camera motion, and omit it on parked/title/blank/static screens. Validate cardinal orientation, heading wrap, consistent numeric/arrow inputs, unchanged status pixels and clear terminal screens.

Deployment/search timing revision requested by owner: after the six-second takeoff, run exactly twenty seconds of forward-only DEPLOY flight before starting the existing 64–96-second survey. During deployment suppress candidate dots, heat spots, IR sightings, designations and report broadcasts. The first survey block uses SCAN/LOITER, introducing unclassified contrast dots after four seconds of searching; later existing scripted reports remain available. Reserve nodes stay grounded. Camera position continues through takeoff → deployment → survey.

Add CAM (daylight) alongside NV, WH and BH; mission auto cycles these four sensor modes every five seconds with per-node offsets. Keep IR as a manually selectable sensor cue. Show mode abbreviation and numeric heading simultaneously in the header beside the north arrow. Draw sparse one/two-pixel synthetic ground contrast features during search, without assigning red/blue classification based on brightness. No detection, navigation or real target-selection algorithm is implemented. Validate exact deployment interval, absence of early cues/reports, all four sensor modes during a twenty-second sweep, continuous camera inputs, and existing terminal/recovery timings.

## Single-pixel contacts — 16 October 2026

Implemented browser visual correction: each synthetic person is exactly one
64×64 source pixel. Small groups contain separated pixels projected onto the
ground plane; bank/pitch move them with the ground. Remove the smooth thermal
heat blob and filled central beacon. Unknown contacts are white in WH, black in
BH, and contrasting black/white in optical views. Scripted classified contacts
use red or blue pixels in all modes. Selection outlines are separate overlays.
Contact bodies remain single pixels during the zoom sequence. Existing probability
and collaboration-based identity decisions are future campaign inputs, not newly
implemented classifiers. This update changes the browser preview only; deployed
firmware and historical GIF/video exports retain their previous renderer.

## Earlier campaign HUD proposal — superseded visually below

The owner requested replacing per-panel `SIM` with two-digit whole kilometres
from each simulated node's own launch point: `00` at home, `14` at 14 km. This
is specified in SPEC-experiments.md together with a fictional line of sixteen
homes 500 m apart. Distance to the selected mission remains a separately labelled
remote field. The remote/presenter retains campaign-simulation provenance.
The compact HUD revision below supplies explicitly labelled presentation samples;
actual campaign position and return-state integration remain pending.

## Compact HUD readouts — 16 October 2026 (visual study 14)

Owner-requested browser layout: node at x2, five-pixel north arrow centred at
x14 (no N), two-character TV/NV/BH/WH mode at x21, heading 000–359 at x33,
and D00 whole kilometres at x50. Retain optional IR mode. Heading wraps at 360.
State occupies x2–32 on row 52; NR0:00 occupies x38–60, becoming BINGO at zero.
Move the battery icon to row 58, retaining the detail/terminal timer on its left.
Missing inputs show D-- / NR-:--; overflow is explicit rather than wrapping.

This preview accepts display-only distance/countdown values. Its app supplies
labelled, authored sample data from chronological time, independent of reversing
camera clips. These samples do not calculate range, energy, safe return or mission
outcomes. A fresh mission resets the samples; grounded nodes show D00 and no
return deadline. Lost feeds do not invent live telemetry. Firmware is unchanged.
The campaign's actual state/energy source remains a separate draft requirement.

Future presentation idea: an ASSESS state could reuse a high/orbit/hover view and
show an observation as pending, uncertain or confirmed. Keep observation and
outcome separate; no additional-attack decision or allocation logic is added here.

## Close approach revision — visual study 15

Supersedes the fixed-horizon / single-pixel-during-KILL rule above. In KILL only,
apply a shared visual magnification around the selected red ground contact to
terrain, contact positions and contact sizes. Smoothly centre that contact as
the approach progresses. Its neighbours spread apart, the horizon moves out of
the camera area, and the central red contact fills that area just before black.
Use the ten existing easing profiles; retain the ten-second countdown, upright
HUD, solid one-pixel red border, 1.5-second black and five-second static ending.
Other states retain single-pixel people. This is an authored camera effect only.

## Grounded crash ending — visual study 16

CRASH tumbles and pitches down, then ends against textured dirt with no sky,
horizon, reticle or pitch marks in the camera region. Blend into the close dirt
view during the final quarter of each variant's existing tumble duration, then
hold it still until static starts at three seconds. Keep the HUD upright and
show GROUND after impact. Dirt respects TV/NV/WH/BH/IR presentation palettes.
The existing five-second SIGNAL LOST ending remains unchanged. Browser only.
