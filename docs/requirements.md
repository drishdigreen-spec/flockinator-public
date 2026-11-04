# Captured Requirements

Current physical-design decisions and measured fit results, 28 October 2026:
[physical build checkpoint](design/physical-build-checkpoint-2026-10-28.md).
It supersedes conflicting older case/speaker/transport appearance notes below:
four acrylic manufacturing tiles on one rigid reinforced assembly; separate
touchscreen/shared-sensor panel; rear-facing speakers without a default separate
grille; 5 mm proud panel-face trial; physically fitted 92 × 36 mm / D5.6 speaker
posts and measured 1.9 mm lugs. Final clip retention, complete node cases and
wall/VESA/frame hardware remain to be designed and tested.

Status: user-provided intent and inventory, consolidated 8 October 2026; node provisioning, deployment and flexible body/brain roles updated 13 October 2026. This document records requirements; it is not an approved module specification.

## Purpose

Provide a visually impressive, interesting-to-watch installation supporting many experiments in agentic AI, swarm behaviour and distributed inference. Each node retains local sensing, state, output timing and hardware supervision. Its decision-making may run locally, remotely or across both. External GPU/CPU brains are a first-class operating mode, configurable per experiment.

The visual identity should express distinct nodes unified through communication. A continuous honeycomb motif in the communication channels is desirable; a single unified fascia across the node faces is not the assumed design direction.

## Nodes

- Sixteen Waveshare ESP32-S3-RGB-Matrix controllers and P2.5 64 × 64 panels.
- Each panel measures 160 × 160 mm and operates independently.
- Panel brightness must never exceed 50% of the configured full-scale brightness. This ceiling applies to boot, diagnostics, experiments and OTA replacement images; the user considers full brightness unnecessary.
- Proposed physical arrangement: spaced 4 × 4 grid. No composite framebuffer or single-screen requirement.
- Onboard sensors, microphones and attached speakers provide local interaction.
- An SD card will be installed on every node for memory, media and data. Engineering recommendation: 32 GB microSDHC, FAT32; 8 GB is a practical starting minimum for modest media/logs, not a hardware minimum. Retention policy remains undecided.
- User will connect nodes to this host one at a time for initial USB provisioning and label them A1–D4. Record hardware identities against these physical positions from the outset; see `inventory/nodes.csv` and `inventory/README.md`.
- Owner confirms each HUB75 controller exposes 3.3 V, GND and two GPIOs on a
  header with a small cable (27 October 2026). Treat this as a per-node sensor
  expansion interface. Exact pin numbers, header order, firmware/peripheral
  conflicts, voltage tolerance and available supply current remain unverified.
  Node cases should reserve an accessible expansion-cable exit and removable
  sensor mounting provision; do not fix an opening or connector footprint until
  the supplied cable is measured. Two-pin I2C or simple digital sensing are
  candidates, subject to pin capabilities, existing buses and sensor requirements.

## Communication and computation

- Keep transport configurable: Wi-Fi IP, ESP-NOW, BLE and USB serial are candidate paths for different workloads. Wi-Fi OTA is implemented on A1; ESP-NOW is the intended handheld deployment path but is not yet implemented for firmware images. No universal transport is selected for experiments.
- Agent-to-agent messages can convey observations, decisions or inference work according to experiment.
- Support direct ESP32 body ↔ external brain streams, independently of LilyGo presence. Measure sensor-to-action latency, jitter and loss under the actual model and concurrent sixteen-node load. Keep display/audio timing local.
- Possible experiments include acoustic communication using speakers and microphones. Radio observations are limited by supported hardware/APIs; the nodes are not general EM-field sensors.
- Treat sixteen sandboxed fruit-fly-derived brain models as a candidate experiment requiring model/backend selection, explicit sensory/action mappings, isolation controls and performance measurement. Emergent communication is a hypothesis, not guaranteed behaviour.
- All sixteen nodes can be attached to USB-C hubs for provisioning, flashing, diagnostics and serial interaction.
- Optional shared vision, lidar or mmWave sensing may serve the whole installation. Sensor choice and processing/distribution are open.

## Management and deployment

- LilyGo T5 4.7-inch ESP32-S3 touch e-paper device is the preferred portable remote and firmware/image store, with live status and optional bounded logging. It is not the exclusive controller, logging destination or required relay.
- External systems may host inference, web management, deployment and central logging. Multiple managers need explicit command ownership/takeover and deployment exclusion.
- Node SD cards hold assets, local/node-specific data, rotated logs and optionally staged images. SD staging is an idea for later validation; installation still targets the inactive internal flash slot.
- Change experiment configuration/brain assignment/media without reflashing when supported; preserve management/recovery and persistent-data compatibility when reflashing.
- Treat the LilyGo as a separate battery-powered handheld remote and status display, not a display-mounted panel. Battery capability is user-reported; battery capacity, runtime, charging access and the handheld enclosure remain to be verified.
- Proposed operational criterion: a running swarm experiment continues when the remote sleeps or disconnects. Firmware-serving and deployment behaviour during remote power loss require explicit recovery design.
- The installed 128 GB console SD card mounted successfully on 9 October 2026; sustained storage workloads and filesystem type remain unverified.
- Prefer wireless firmware deployment to avoid repeatedly connecting panels to USB hubs.
- Prefer selecting and initiating deployments from the LilyGo, using stored firmware images.
- ESP-NOW is the intended handheld-to-node firmware deployment transport, reaffirmed by the owner on 9 October 2026. Experiment messaging remains open. PXE-style network boot is not an established capability.
- Support individual, grouped and cluster deployments as proposed design requirements for review.
- Initial USB provisioning and recovery remain available.

See [flexible bodies, brains and controllers](design/embodied-experiment-platform.md) for the captured architecture, transport/storage distinctions and fruit-fly experiment constraints.

## Communication lighting

Owner power-path clarification, 28 October 2026: the keyed power header on each
panel receives its normal 5 V/GND supply and also supplies the attached ESP32
controller's 5 V rail and ground. Normal operation does not require a USB-C cable
to the controller. Case design should prioritise clearance for the keyed panel
power plug, its cable bend, retention and service disconnection. Retain controller
USB-C access for programming/debugging, without reserving a permanently installed
USB cable. This records the owner's installed arrangement; simultaneous external
power and USB power behaviour has not been established here.

Power distribution update, 27 October 2026: owner will run eight low-voltage
power extensions from the power case, each serving two panels. This fixes branch
count, not conductor gauge, connector rating, protection or splitter arrangement.
Proposed pairing keeps both panels on one acrylic tile: A1–B1, A2–B2, C1–D1,
C2–D2, A3–B3, A4–B4, C3–D3 and C4–D4 (front-view labels). Pairing is provisional.
Each branch includes supply and return conductors. Size its shared trunk and
connectors for both loads; verify voltage at both panels under simultaneous load.
Allow independent panel disconnects, strain relief and service slack. Final
branch protection, wire sizes and distribution hardware await cable specifications
and measured panel/controller/audio demand at the enforced brightness ceiling.

- ARGB strips hidden in diffuser channels surround panels and form a grid.
- Animate a square around a communicating node and paths to recipient node(s).
- Styles, timing, event meanings and route mapping are undecided.
- Lighting needs at least one output controller in addition to the sixteen panel
  ESP32s. The 10-inch touchscreen is the candidate world/overview controller;
  a smaller WLED-compatible driver is under consideration for the LED paths.
  Hardware and controller count remain open; see [lighting controller direction](design/lighting-controller-direction.md).
- Drawn paths need not imply actual packet forwarding hops; experiment semantics must make this clear.
- Visual behaviour should support experiments involving disrupted communication, intercepted or modified inference streams, rogue nodes, propagation of false information, trust assessment and exclusion. These are experiment scenarios, not implemented capabilities.
- Proposed event distinction: attempted transmission, delivery, acceptance/influence and rejection/exclusion should be representable separately. Node beliefs and assessments must remain distinguishable from the experiment operator's knowledge of an injected rogue node.

## Physical assembly

- FreeCAD is available to create/adjust prototype models and mounts.
- Duality LED Track System bundle has been purchased and supplied under `references/duality-track-system-bundle-original-track-and-evolution-pack-model_files/`. Suitability and assembled fit remain to be verified.
- Suspected 150 × 150 mm track squares are unverified and may describe openings rather than pitch.
- Panels may sit above the grid, provided separation, diffuser visibility, wiring and service access work.
- Grid pitch and spacing must remain parameters, not fixed to the suspected track size.
- Transport the display as one rigid assembly. The user considers approximately 1 × 1 m manageable despite its weight; the earlier four-quadrant disassembly proposal is superseded. Retain removable individual panels and printable track segments for manufacture/service rather than routine transport disassembly. Handle placement, measured total mass, protection and structural mounting remain to be designed.
- Prefer rounded track corners and a continuous hexagonal tile pattern to give an organic beehive/swarm-of-bees impression while keeping all sixteen nodes visually distinct.
- Support may be a stand or wooden feet painted white. Foot dimensions, stability, frame attachments and the complete mass including the power enclosure require validation.
- Prefer Bambu filament available to both the owner and Wobbl3D; establish an accepted physical optical sample and recorded print profile before production.
- A shared backing (acrylic/Perspex or wood, material undecided) mounts the diffuser grid and independently supports each panel through its M3 mounting points.
- Speaker protection: printed mounts must include a surrounding shell and a grille protecting both exposed moving surfaces, with removable access, retained wiring and preserved acoustic openings. A bare carrier is only an intermediate prototype. On 11 October 2026 the owner authorized a fully surrounding enclosure with acoustic fibre behind the speaker, 50% gyroid infill and five wall loops. The independent enclosed-v2 CAD implements a removable grille, shell, padded retaining frame and integrated T rear cover; physical fit, slicing and sound quality remain to be tested on one sample. See `../cad/perimeter-speakers/enclosed-v2/README.md`.
- Speaker wiring: each speaker has an owner-reported 150 mm lead with ESP32 connector. Use stock leads where the installed route permits; solder extensions for the central four and any other short leads. Determine reach from the actual board connector to speaker cable exit, including retained routing and service slack; edge-panel reach is not yet verified. Preserve conductor pairing/polarity and insulate and strain-relieve splices.
- Final assembly intent: power leads and optional USB-C serial cables sit concealed behind each panel, with retained wiring. Speaker placement must provide acoustic access and adequate depth.
- Temporary whiteboard prototype, reported 11 October 2026: revision 2 joints fit and most panels are joined with X pieces. Owner reports 12 mm magnetic standoffs clear the ESP32 in HUB75, but do not accommodate the rear-facing speaker. Extend T connectors beyond the array for forward-facing perimeter speakers, four per side, with longer leads from the centre four nodes. Owner initially agreed with the reference speaker dimensions, then supplied actual body measurements of 98 × 44 × 20 mm and four mounting holes approximately 10 mm from front/back fascia. Actual body measurements take precedence. Mounting-depth datum needs clarification; the previously agreed 90 × 36 mm hole pattern has not been replaced by a new measured pattern. Carrier v1 prototypes preserve the proven T interface, with two single carriers and one twin carrier per side. Exported geometry is checked; physical fit, installed whiteboard clearance and rigidity remain pending. See `../cad/perimeter-speakers/README.md`.
- Prefer purchased default track sections and seamless hexagonal diffuser skins to preserve a continuous honeycomb appearance. Geometry must establish whether panels fit inside or sit forward of the channels.
- Explore removable panel-face diffusion: thin white/translucent front layer with black pixel-isolation walls. Investigate slicer-generated grid infill and hex styling while preserving the ability to display native 64 × 64 content. Prototype diffusers must cover the full 64 × 64 panel (all 4096 pixels); reduced 8 × 8 test coupons are not requested. This is an experiment, not a selected optical design.
- Preferred appearance is predominantly white/semi-translucent, with black or other contrasting elements under consideration. Optical isolation and concealed hardware may require opaque internal parts. Final colours, opacity, surface finish and extent of visible contrast remain experimental.
- Use the user's Bambu Lab X2D with four-spool AMS and one-spool AMS HT for local visual and fit prototypes. One full 64 × 64 panel-face diffuser with a border assembled from printable segments is acceptable. Small joint/material samples can supplement, but do not replace, the full-panel optical test.
- [Wobbl3D](https://wobbl3d.com/) is the selected outsourced fabricator, with Bambu Lab H2C/H2D printers reported by the user. Local X2D tests precede outsourced production where practical; supplier nozzle sizes, filaments, tolerances and slicer profiles remain to be confirmed. Transfer the accepted appearance and dimensions, then validate a supplier-made sample before repeating across sixteen nodes.

## Ordered prototype filament

User reported ordering four 1 kg Bambu refills on 8 October 2026: PLA Basic Jade White 10100, PLA Basic Black 10101, PLA Matte Ivory White 11100 and PLA Matte Charcoal 11101. Receipt, batch numbers and delivery date are unconfirmed. Compare Basic/Matte optics and pixel walls before selecting production materials; see `docs/research/filament-and-local-validation.md`.

## Purchased power hardware

| Item | Quantity | User-supplied details |
|---|---:|---|
| MEAN WELL LRS-350-5 | 1 | 5 V, 60 A, 300 W |
| MEAN WELL TBC-09 | 1 | Nine-way terminal cover |
| MEAN WELL MHS012 | 4 | Mounting brackets |
| PowerNex ST303015 | 1 | Grey steel IP66 enclosure, 300 H × 300 W × 150 D mm |

The current preference is a rear-mounted steel power enclosure with one 240 V inlet and internal 5 V and 12 V supplies; this supersedes the earlier external-box concept. The 12 V supply is not yet selected. Mount the box to a load-bearing frame and verify enclosure heat rejection, protective earthing, electrical protection and service access before assembly. The user has clarified that panels will never exceed 50% brightness; the earlier estimate of at least 300 W for panels is superseded as an operating assumption. Actual node demand at this ceiling remains to be measured. The lighting estimate of a similar power level remains provisional. A future 12 V AC/DC supply is now preferred for lighting; strip compatibility, capacity, fit and thermal performance require validation.
