# Decision register and future work

Physical design, 28 October 2026: [consolidated decisions, dimensions, model status
and physical fit evidence](../design/physical-build-checkpoint-2026-10-28.md).
Four acrylic tiles on a reinforced frame, separate world/sensor panel, rear-facing
speakers and 5 mm raised panel-face trial are the current direction. Speaker post
pattern **92 × 36 mm / D5.6** is physically fitted; final clips/case remain pending.

Current priorities and operating state (19 October 2026): [development baseline](../development.md).
Historical entries below retain their original checkpoint dates.

Map correction, 17 October: keep completed cinematic poses fixed through the
blank intermission, retaining lost/parked status until the next cycle. Use the
camera's seeded field pattern for the overhead terrain. Browser-only correction;
existing fictional paths and mission scripts remain. The proposed range ring,
real-distance deployment and attack-allocation/identification mechanics are not
implemented. Validation covers deterministic seeks and all terminal outcomes.

Presentation map extension, 17 October: browser-only fullscreen and a separate
session-linked map viewer, synchronized TX/RX pulse colors, and explicitly
illustrative red/blue reports. It preserves the running scripted mission and
freezes visibly on source-tab loss. No hardware, inference, target allocation or
attack GO controls changed. Camera sprites still lack shared-world contact
coordinates; report map locations must not be presented as actual inferred truth.

Latest owner selection: preserve automatic mission scenarios and restore shared
world terrain and relative drone tracking within that presentation. Implemented
and deployed on all sixteen nodes as **0.10.1**, with a browser world map and
continuous per-node camera poses. The original mission schedule, terminal
cinematics, communication borders and LilyGo commands remain. Peer positions
are authored shared-world fixtures, not received A2A reports or inference.
The separate host survey bridge remains stopped. Evidence:
`docs/validation/mission-world-deployment/README.md`.

17 October update: the fictional survey engine and authenticated node adapter
are implemented and deployed as firmware 0.10.0 across all sixteen. Mac-hosted
state and browser commands own the survey; the node is a renderer. Energy/world
units are invented, and peer cues use simulated session positions. No distributed
inference is claimed. LilyGo remains on its existing mission UI, with its survey
adapter pending. See `docs/validation/survey-deployment/README.md` and
`tools/survey-simulator/README.md`. Earlier broader campaign proposals below
remain proposals, not the contract for this implementation.

Consolidated 16 October 2026. Status matters: **implemented**, **owner requirement**,
**proposal**, and **deferred idea** are not interchangeable. Historical research
notes remain evidence of earlier thinking; this register and HANDOVER.md identify
the latest position. Module specifications retain their existing approval status.

## Confirmed requirements and implemented choices

| Decision | Status and rationale | Where to resume |
|---|---|---|
| Sixteen distinct nodes, not a tiled screen | Owner requirement; each panel is an independently observable agent body | `docs/requirements.md` |
| 64×64 P2.5 panels, 160×160 mm, maximum 50% brightness | Owner requirement; retain all 4,096 pixels | Node spec; mechanical drawings |
| Local bodies, optional remote brains | Owner requirement; hardware sensing/output and management must survive changes of experiment backend | `docs/design/embodied-experiment-platform.md` |
| Wi-Fi, ESP-NOW and serial paths | Implemented commissioning/management capabilities with distinct evidence; transport choice remains workload-dependent | Network/deployment specs |
| Identity recorded before panel assembly | Implemented all sixteen; private inventory maps physical labels/MACs/addresses | `docs/inventory/` |
| Per-node SD memory/media/logs | Implemented FAT32 maintenance; capacities vary; interrupted capacity tests remain incomplete | SD register and recovery evidence |
| LilyGo handheld, separate from display | Owner requirement; real touch/status/mission presentation already works | Console spec |
| Node-authoritative five-state Overview | Implemented node 0.8.1 + console 0.3.3; hardware freshness distinct from fictional condition | Overview validation |
| Scripted HUD / communications presentation | Implemented; ten treatments, chronological takeoff/recovery/endings, reversible eligible clips, paired TX orange/RX green flashes | Browser design and shared recon model |
| Individual ground people are pixels | Implemented browser visual study 13 only; unknown black/white, classified red/blue, separated groups, no thermal blob | `previews/recon-hud/DESIGN.md` |
| Current private GitHub snapshot | Requested by owner; retain project progress without claiming public asset rights | `docs/backup-and-restore.md` |

## Proposed campaign architecture and design

All rows below are captured in `SPEC-experiments.md` and await campaign spec review.

| Proposal | Reason / important distinction |
|---|---|
| Mac headless engine → Linux/Pi deployment | Easier deterministic testing, persistence and replay; management is independent of GPU experiments |
| Portable C++ core with host/firmware adapters | Candidate path to later embedded hosting; Linux container portability is different from an ESP-IDF firmware port |
| LilyGo as command client | Remote sleep should not pause the backend; explicit Pause does; backend restart restores paused and reconciles |
| Single campaign authority | Revision/epoch ownership prevents divergent state; no automatic second authority after a timeout |
| Persistent resource-management game | Selected nodes, disjoint concurrent assignments, finite fitted/spare packs, timed servicing, persistent losses and retained reserves |
| READY / OM / LOST campaign cards | Charge/health/distance/service shown separately; differs from installed five-state demonstration |
| Summarised five-paragraph briefing | Situation, Mission, Execution, Sustainment, Command/Signal; fictional game adaptation, not a complete doctrinal form |
| Browser playable without hardware | Virtual panel display, full commander interface; public synthetic mode isolated from private management |
| Staged scenarios and score breakdown | Communication loss, partitions, inconsistent reports and recovery; game score is distinct from research metrics |
| Traceable decision timeline | Per-agent lanes, observations/receipt/use events and branching/merging provenance; unknown reasons remain unknown |
| Shared portable replay | Seed/version/event history; knowledge-at-the-time separated from researcher truth; counterfactual runs labelled separately |
| Distance field | D00 whole km from own fictional launch location; mission distance separate. Browser study 14 has labelled sample values only; campaign integration and firmware pending |

## Research ideas retained

- Robustness of mesh communications and agent trust under synthetic loss, delay,
  isolation, inconsistent reports and a simulated compromised participant.
- Compare actual bounded agent decisions against the existing scripted display.
  Do not claim that authored probabilities demonstrate distributed intelligence.
- Measure delivery, stale information, errors, abstentions, false exclusions and
  recovery. Preserve report origins so repetition does not create independent evidence.
- Hypotheses include benefits and risks of additional peers: more peers can repeat
  the same mistake; fewer links may lead to cautious abstention rather than error.
- Distinguish action completion from uncertain, delayed or contradictory outcome
  assessment. Record resource contention, reserve use and human oversight questions
  at the fictional scenario level, without operational attack-selection algorithms.
- Virtual hundred/thousand-agent studies are a future benchmark; they cannot prove
  real RF capacity or the physical sixteen-node system's scalability by themselves.
- Future non-military avatars and scenarios, including animal-like alertness and
  fruit-fly-inspired remote brains, remain possible. Doom media belongs to a separate
  project and its reuse/redistribution requires provenance and licensing care.
- Audio experiments: local sounds, shared timing/pitch, microphone feedback and
  possible acoustic communications. Keep the separate ReSpeaker assistant project
  distinct; see `docs/research/respeaker-lite-vs-waveshare-audio.md`.

## Physical design and hardware backlog

- The long-term design keeps separated, centred panels and rounded diffused tracks
  with a honeycomb appearance. The current touching-panel/whiteboard arrangement
  is a temporary prototype, not a change to that visual goal.
- Use `cad/panel-hole-review/` for corrected panel mounting geometry. The owner
  confirmed the latest joints fit. `cad/temporary-panel-joints/rejected-v1/` is
  rejected and must not be printed. Inlaid inner mounts can serve a future backplate.
- The owner reports 12 mm magnetic standoffs clear the ESP32; rearward speakers
  lack clearance. Speaker boxes/border modules need further redesign. Preserve
  existing revisions rather than treating any as a final print instruction.
- Speaker confirmed approximately 98×44×20 mm, with roughly 6 mm mounting holes;
  prior reference centres 90×36 mm. Four forward-facing speakers per side,
  full border/corner continuity, protected diaphragms and acoustic fibre remain
  preferences. Cable extensions are expected for central nodes. Verify physical fit.
- One rigid assembly around 1 m square is acceptable; routine disassembly is not
  required. Stand or white-painted wooden feet and a rear power enclosure are
  preferred; weight, stability, cooling and electrical design remain validation work.
- Purchased MEAN WELL LRS-350-5 is rated 5 V 60 A / 300 W; do not repeat the early
  assumption that its model number means 350 W at 5 V. ARGB supply/load remains TBD.
- Bambu PLA Basic Jade White/Black and Matte Ivory White/Charcoal were ordered for
  optical/contrast tests. Compare actual printed samples before standardising a
  production material. Full 64×64 diffusion, not an 8×8 substitute.
- Wobbl3D H2C/H2D outsourcing and local X2D sample printing are owner plans; printer
  profiles, tolerances, filament and final quantities require physical validation.
- Dedicated GLEDOPTO/WLED controllers, TFmini Plus and camera hardware are available
  ideas. Mapping communication events to LED paths and shared sensor adapters is
  future work. Never infer camera compatibility from connector appearance alone.
- Exact incoming primary controller: **unresolved** P4+C6 board versus ESP32-S31.
  Confirm its model before choosing drivers or moving the engine onto it.

## Next decisions on resumption

1. Review the consolidated campaign spec, then follow its approved implementation
   workflow. No game engine has been created by documenting these ideas.
2. Decide whether the next code task is the small pixel-contact firmware port or
   the approved first campaign slice; avoid bundling an unreviewed game rewrite
   into a visual fix.
3. Confirm future board model and whether/when a Pi should host the service.
4. Select fictional game timing/pack presets and scoring weights through play tests.
5. Define a separate reproducible trust experiment with neutral tasks and explicit
   hypotheses before interpreting game behaviour as research evidence.

- Browser study 14: north arrow without N, TV/NV/BH/WH, heading 000–359,
  D00 and NR0:00 → BINGO. Return labels are authored presentation data only.
  A hover/orbit ASSESS observation view is a future presentation idea, without
  additional-attack decisions or allocation logic.

- Browser study 15 supersedes the KILL fixed-horizon/single-pixel exception:
  terrain and red contacts enlarge together until a contact fills the camera,
  followed by the existing black/static ending. Other states remain unchanged.

- Browser study 16: CRASH pitches/tumbles into a close dirt view and holds still
  with no horizon or reticle until the existing static ending at three seconds.
  HUD remains upright; TUMBLE changes to GROUND. No firmware change.

- Browser study 17 implements the owner-approved `SPEC-world-view.md` and
  `tasks/world-view/` plan: persistent shared seeded terrain, authored camera
  snapshots, interpolation/stale/resume handling, local impact and neutral peer
  sightings. The existing mission loop remains selectable and the default.
  Snapshot cadence 2 Hz; interpolation delay 500 ms; stale threshold 1,500 ms;
  resynchronisation blend 750 ms; at most three peer labels in stable ID order.
  Unprovided metrics stay unknown. Scope is browser presentation only: no physical
  rollout, operational model, inference or combat-decision implementation.
  Evidence and timing environment: `validation/recon-hud/world-view/`.

- Hardware World-view extension, 16 October 2026: user explicitly requested the
  upload after browser validation. Ported local synthetic rendering to ESP32-S3
  firmware 0.9.0, canaried A1, then updated the sixteen-node fleet over Wi-Fi OTA.
  Existing diagnostics, legacy mission mode, identities/keys, SD contents,
  ESP-NOW/OTA receivers and 25% brightness remain. Camera peers are authored
  fixtures, not live node observations. LilyGo unchanged. Exact measurements and
  per-node image/boot/SD evidence: `docs/validation/world-deployment/`.
