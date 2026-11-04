# Reconnaissance swarm: observations, orders and disagreement

## Current implementation — 16 October 2026

The approved visual storyboard is now implemented by node firmware 0.8.0 and
LilyGo 0.3.1-missions. Its launch/stop control and health reports use authenticated
ESP-NOW. All sixteen nodes are now on channel 4; the earlier C2 channel limitation
below is historical. The presentation still uses deterministic scripted events.
Peer beliefs, evidence evaluation and live experimental A2A decision-making in
the proposal below remain future work. See [remote usage](hud-remote-usage.md)
and [deployment evidence](../validation/recon-deployment/README.md).

Design proposal — 16 October 2026 (Sydney). The owner subsequently approved proceeding with the visual direction, specifically animated crosshairs, simulated flight and short HUD labels. The animated visual preview is implemented under `previews/recon-hud/`; no firmware or running experiment was changed. Existing autonomous Doom expressions remain active. Network/runtime specifications remain the next separate design stage.

## Presentation concept

Sixteen independent simulated reconnaissance quadcopters survey a fictional site and report observations to HQ. Every panel is one aircraft with its own mission state, observations and beliefs. The installation remains sixteen agents, not a tiled map pretending to be one screen.

Use a stylised top-down quadcopter avatar with rotor motion, a heading marker and a scanning arc. Its movement communicates activity; concise overlays explain why it is acting. A separate presenter view supplies the shared mission map, event timeline and ground truth. The eventual ARGB grid shows communication events between aircraft and HQ via configured display routes.

Flight position, altitude, energy and sightings are synthetic scenario inputs. Actual Wi-Fi connectivity, packet delivery, ESP32 health and storage status remain separate measured facts. A permanent SIM marker identifies simulated mission telemetry. This proposal does not connect to aircraft, flight controllers or operational mission systems.

## First story: the false beacon

A beacon at a fictional survey site is the object of interest. Its location is known to the simulator, but each aircraft receives only its own simulated observations and incoming reports.

| Beat | Audience sees | Experiment behaviour |
|---|---|---|
| Briefing | HQ issues SURVEY; aircraft acknowledge and begin moving/scanning | Run identity, assigned survey regions and order acknowledgements are visible |
| Discovery | A node observes the beacon and sends a report | Receiving nodes distinguish a peer report from their own observation |
| Propagation | More nodes receive the report and pass it onward | Original observation identity survives forwarding; ten copies are not ten independent sightings |
| Deception | One designated node claims a conflicting beacon location | The presenter can reveal the injected fault; other agents see only the claim and its provenance |
| Verification | Nodes disagree, request another observation and wait | Independent simulated observations support or contradict the report; confidence and uncertainty are visible |
| Containment | Some nodes discount the claim, or the false report spreads | Compare a naive report-sharing policy against a corroboration policy; do not script automatic success |
| Debrief | HQ receives a result with uncertainty and evidence | Show who believed what, how long the false claim survived and which messages changed beliefs |

First presentation should be short, repeatable and pausable, with a proposed 90-second guided run. Pause freezes simulated mission time, not management or physical diagnostics. A fixed seed makes policy comparisons reproducible. The stop control returns nodes to a neutral display while OTA/status remain accessible.

## Panel language at 64×64

Preserve native resolution, brightness defaults and the existing 50% hard ceiling. Prefer a few legible symbols over a miniature cockpit full of unreadable numbers.

- Top 8 pixels: node identity and SIM; retain a distinct genuine hardware-warning mark when required.
- Middle 40 pixels: drone avatar, rotor/scan motion, heading cue and one nearby observation or disagreement symbol. The drone can gently bank or change its apparent speed to express mission activity.
- Bottom 16 pixels: short activity label and one rotating telemetry/event line. Examples: SCAN / ALT 42; SHARE / TO B3; CHECK / FROM C2; HOLD / HQ WAIT. The permanent SIM marker applies to fictional altitude/energy fields. Avoid presenting invented signal quality as measured RSSI.
- A report transmission generates a brief local pulse; acknowledgement generates a different mark. Silence, packet loss and a quiet but healthy agent must look different.

| Mission/interaction state | Visual treatment |
|---|---|
| Ready / awaiting order | Level drone, restrained rotor animation, HOLD |
| Surveying | Moving scanning arc, heading cue, SCAN |
| Object observed | Brief ring around a beacon symbol, SEEN |
| Reporting / receiving | Outward/inward short pulse, SHARE / RX |
| Awaiting evidence | Slower motion and question mark, CHECK |
| Conflicting reports | Two disagreeing beacon markers or split brackets, DOUBT |
| Report discounted by this node | Source label plus crossed report icon, IGNORE |
| Experiment link disruption | Broken-line icon, LINK?; underlying management status still reported separately |

White/cyan can carry normal activity, amber uncertainty, magenta disagreement and a distinct outlined warning symbol genuine hardware trouble. Colour always has a corresponding shape or label. Avoid full-panel flashing. Do not make every node display ROGUE merely because the scenario operator designated one: that would reveal information the agents have not earned.

The presenter may select **observer view** (ground truth and designated deceptive node visible) or **agent view** (only that node's local beliefs and received evidence). Experimental suspicion/exclusion is a local assessment with reasons, not a hardware diagnosis or a universal binary label.

## Communication and authority

The first meaningful experiment needs real application messages between node identities. Random animation and the existing commissioning heartbeats cannot stand in for that. A visual storyboard may simulate messages, but must be labelled as such; a validated experiment animates events emitted by the message/runtime layer.

Use A2A here to mean application-level agent-to-agent interaction. Choosing or claiming compatibility with a particular external A2A specification is a separate interface decision. The existing commissioning wire protocol has no mission-message implementation yet.

Proposed message meanings: mission order, order acknowledgement, observation, forwarded report, evidence request, evidence response, local assessment and run summary. Their detailed encoding belongs in the network/runtime specifications after this scope is agreed. Preserve run/message/observation identity, sender and intended recipient, expiry, evidence origin and causation. Keep an observation distinct from an inference or a relayed claim.

Authentication answers who sent a message; it does not prove that the sender's claim is true. The deceptive node should send an authenticated but false simulated observation, rather than breaking the management keys. Replays, duplicates and forwarded copies must not count as independent corroboration. HQ orders and peer observations have different authority; a peer claiming to relay an order does not acquire HQ authority.

Use Wi-Fi application messaging first on the current network. All sixteen nodes have working authenticated Wi-Fi management, while C2's channel-10 association prevents participation in the channel-4 ESP-NOW group. A broker/relay on the host can be a first transport provided sender identity, delivery semantics and the extra hop are explicit. Do not label a relayed path as direct radio delivery. ESP-NOW remains a later experiment transport once common-channel behaviour is addressed.

Application-level perturbations can delay, drop or duplicate selected experimental messages, suppress one observation source, or cause one node to publish a false report. The fault injector must leave management, firmware deployment and recovery traffic alone. Transport loss and deliberate deception are separate selectable scenarios, not equivalent explanations for missing data.

## Capability boundaries proposed for review

Reuse the existing stable project module IDs; this is not a new combined management/mission controller.

| Existing module | Scope needed here | Provider dependencies |
|---|---|---|
| node-platform | Drone-themed renderer consumes bounded mission/belief snapshots; genuine hardware status stays accessible | Existing display/state/SD/OTA implementation |
| flock-network | Experiment message delivery, identities, freshness and event reporting separate from commissioning | node-platform |
| agent-runtime | Small local rule-based agent keeps beliefs, evaluates reports and chooses simulated actions; remote brains can replace it later | node-platform, flock-network |
| experiments | Synthetic world, per-agent observations, HQ mission role, fault injection, seeded replay and presenter timeline | agent-runtime and flock-network event interface |
| management-console | Optional start/pause/stop and experiment status controls; deployment remains independently available | experiments control interface, existing management providers |
| communication-lighting | Future ARGB event consumer with configurable visual routes and filtering | flock-network events and physical LED mapping |

HQ is a role inside the experiment. It must not become the only firmware manager or be granted the ability to alter node identities. The current Mac can host the synthetic world/presenter initially; a Pi or future P4 gateway is an optional later host. No GPU is needed for the first deterministic decision rules. A remote inference service can later receive the same bounded observations and return proposed actions without taking over management.

Proposed build order: native-resolution visual storyboard → experiment message contract and delivery proof → local rule-based beliefs/decisions → complete false-beacon scenario and presenter → optional LilyGo controls and ARGB event adapter. Existing random-face mode remains available throughout development.

## What the experiment should measure

- Per-node belief about the beacon and the evidence supporting it, compared with hidden ground truth.
- Time for a true or false report to propagate; number of nodes that accept each claim.
- Independent corroboration versus repeated copies of one original observation.
- Time to recover from a false report; mistaken accusations or exclusions.
- Messages/bytes, acknowledged delivery, timeouts and observed latency by transport.
- Whether management remains responsive while experiment traffic and perturbations run.

Replay should distinguish recorded actual message events from a fresh live run. Animated ARGB paths are a visual route through the installation, not a claim about the radio signal's physical path.

## Next design deliverable

Readable animated 64×64 storyboards for HOLD, SCAN, SEEN, SHARE, CHECK and DOUBT are now available in `previews/recon-hud/`, with sixteen independent views, native-pixel sizing, selected-node enlargement and three palette choices. This completes the first visual deliverable. Review physical readability with a future one-node firmware port, then specify the network and runtime contracts within their existing module boundaries. No autonomous-flight system or new mission protocol is implemented by the visual preview.

The 16 October visual extension adds ENGAGE, LOST, ZOOM, CRASH, EMPTY and NOLINK. These scripted events show reticle convergence, lost observation/search, zoom followed by blackout, an inverted frozen camera, battery depletion and stale contact respectively. All twelve scenes are selectable in the browser; `previews/recon-hud/events.gif` records the six new events. Renderer and browser checks passed. Firmware deployment remains a subsequent hardware increment.

The owner subsequently requested an F-14-style horizon presentation. The preview now uses a forward-looking VDI-inspired scene with a banking/pitching horizon, dark sky and moving perspective ground patches, replacing the overhead buildings. These are synthetic orientation cues. `previews/recon-hud/horizon.gif` demonstrates the revised style, including inversion, while preserving all twelve states and the existing control surface.

The visual preview now defaults to a complete repeating mission: approval/instructions, fleet takeoff, 64–96 seconds of search/reporting and scripted coordination, randomized per-node visual endings, and a five-second fleet-wide blank gap before the next approval. This is a seeded presentation timeline with fixed fictional coordination fixtures, not an operational mission controller. Continuous camera motion avoids state-boundary background jumps. KILL magnifies its beacon only; the horizon retains its scale. See `previews/recon-hud/README.md` and `mission-loop.mp4`.

HUD preview refinement: thirteen ordinary status animations now repeat forward/reverse with eased turnarounds and a stable variant. Twenty-second ordinary mission clips preserve camera position at transitions; KILL/CRASH/EMPTY and chronological timers/events remain forward-only. See `previews/recon-hud/DESIGN.md` and `playback.mjs`. This remains a browser visual prototype.

Recovery/sensor preview extension: LOITER, R2B, LAND, CHARGE and STANDBY are available; two reserve nodes remain grounded per scripted mission. Sensor mode is separate from mission state, with night vision, white-hot/black-hot thermal and an unverified IR-strobe cue. Recovery and strobe clocks advance forward. These remain procedural display fixtures for later agent integration, not navigation, identification or charging controls.

Presentation timing refinement: active nodes now fly outbound for twenty seconds after takeoff before entering SCAN/LOITER search. Sightings and report cues are suppressed during deployment. Search introduces unclassified high-contrast ground dots and cycles CAM/WH/BH/NV at five-second intervals per node; IR remains manually selectable. Sensor mode and heading coexist in the header. This is a scripted visual sequence, not a detection or flight-control implementation.
