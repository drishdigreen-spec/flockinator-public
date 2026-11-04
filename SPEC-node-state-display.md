# Node state display: visual states and interchangeable themes

Status: **display specification approved by owner**, 15 October 2026 ("proceed, we will use the doom guy for now"). Owner also authorised creating missing expressions and requested a talking direction using the node speakers/microphones, without speech-to-speech as the objective. Implementation plan and bounded audio extension are recorded in `tasks/node-platform/plan.md`. The owner subsequently approved proceeding with flashing all nodes. Implementation and fleet deployment are authorised; record physical visual/audible acceptance separately from automated deployment success.

## Objective

Replace the normal rotating commissioning screen with a useful visual representation of each independent 64×64 Flockinator node. Define states independently of their artwork so faces, iconography and dynamic interfaces can express the same information. Show node identity, observed operational health, communication activity and explicitly supplied experiment state. Retain diagnostics and both existing wireless firmware update paths. Reuse selected artwork from the separate Doom Guy project as an initial test theme, without importing its application, financial logic, credentials or build system.

Owner clarification, 15 October 2026: Doom's progressive injury imagery is useful for testing but may be unsuitable for some scenarios. Idle attention should feel calm: look left/right and return ahead, without appearing panicked. Future themes may include a fruit-fly character. Theme-specific appearance must not determine the underlying node-state vocabulary.

Further owner clarification: use an animal's observable condition as the organising analogy—sleeping, calmly watching, alert, busy working, frightened, happy and more or less communicative. The primary view should make these behaviours readable at a glance; detailed engineering diagnostics remain a secondary view. These are expressive representations of experiment state, not claims about subjective experience.

This is one display capability, including its small media pack and state-selection interface. It does not introduce a general media server, inference engine or new swarm protocol.

## Assumptions for review

- The state view is the default page after boot. The owner can still select the existing diagnostic pages locally and remotely.
- Use the full native 64×64 canvas, with compact overlays; do not reduce the display to 8×8 or 32×32.
- Default brightness remains 25%, with the existing hard ceiling of 50%.
- Use a healthy neutral face for normal operation. Injury imagery is disabled by default, including for hardware warnings, and available only in an explicitly selected injury-enabled Doom test profile. A compact warning icon/label works in either profile.
- Owner-selected first release: Doom Guy only. Procedural symbols support missing expressions and status overlays; a standalone icon theme and fruit-fly theme are deferred. Preserve a theme-independent state contract without implementing a general theme engine now.
- Bundle the initial pack in firmware and provision a verified copy to available SD cards automatically. A missing or faulty card must not prevent the face, diagnostics or OTA from working.
- First control/verification uses the existing authenticated host Wi-Fi interface. LilyGo ESP-NOW deployment remains functional; a new LilyGo face-control screen and new ESP-NOW expression messages are deferred.

## Inspected sources and reusable material

Source root: `/Volumes/devops/doomguy/doomguy/` (read-only during this work).

| Source | Observation | Proposed use |
| --- | --- | --- |
| `assets/faces/64x64/` | 42 PNG files, all 64×64; 299,389 bytes total; 40 distinct decoded RGB images | Initial local prototype face pack |
| `firmware/doomguy/faces_64.h` | Existing RGB565 arrays | Reference for conversion and colour parity |
| `firmware/doomguy/face.cpp` | 8 FPS timing and ambient glance behaviour | Behavioural reference, not a drop-in module |
| `tools/art/doomguy_face_64.png`, `doomguy_face_blink_64.png` | Alternative generated pixel artwork | Optional later visual style |
| `assets/sd/` and other audio assets | Existing sound/media material | Audition candidates for a later bounded talking increment; no automatic startup chatter |
| `NOTICE` | Identifies game-derived artwork and original project attribution | Retain provenance with selected copies; no claim that game imagery is newly authored or freely licensed |

Important correction: old documentation labels picture groups 1–5 as idle/look-left/look-right/pain/anger. Visual inspection shows damage levels across groups and different expressions within each group. For example, `picture1-1.png` is heavily damaged and `picture5-1.png` is healthy. Do not reuse those old group labels as animation semantics. Build an explicit, visually reviewed mapping of individual frames. Duplicate wake images must not be presented as a genuine two-frame animation if their pixels are identical.

The raw pack is 42 × 64 × 64 × 2 = **344,064 bytes (336 KiB)** before metadata. The small pack does not require live streaming from SD. Source dimensions are 64×64, but the old project's documentation says its artwork was resized from earlier source images; native canvas size does not imply new artwork detail.

## Visual state vocabulary

Keep the following dimensions separate. A node can be listening, receiving a message and experiencing a storage fault at the same time; collapsing these into a single mood loses useful information.

| Dimension | Initial vocabulary | Meaning and visual treatment |
| --- | --- | --- |
| Lifecycle | starting, running, maintenance | Boot mark, normal avatar, or maintenance/progress overlay |
| Operational health | unknown, nominal, degraded, fault | Small status symbol and diagnostic reasons; nominal means monitored checks only, not completed manual acceptance |
| Activity | sleeping, idle, listening, processing, waiting, speaking | Primary pose or icon: closed eyes, calm eyes, ear, moving dots, pause/hourglass, sound-wave symbol |
| Attention | calm, attentive, urgent | Gaze/focus and restrained timing changes; explicit input with source and expiry, never inferred from traffic volume alone |
| Mood | neutral, curious, content, frightened | Expression/posture distinct from activity; content represents happy/comfortable and frightened is not a synonym for hardware failure |
| Communication | local TX, local RX, confirmed delivery, quiet/occasional/frequent traffic, stale link | Brief overlay marks and a smoothed indication of communication frequency; directions are TX/RX, not invented spatial routes |
| Experiment condition | optional vitality level 0–4 | Experiment-defined condition, clearly marked EXP; absent by default and independent of measured hardware health |

Activity and attention may come from a real subsystem event when available, or an explicitly declared experiment/demo input. Mood comes from an explicit experiment/demo input in this milestone; the display does not invent fear or happiness from CPU utilisation, errors or traffic. Each carries its provenance. This firmware does not acquire listening/ASR, inference or speech functionality merely by displaying the corresponding icon. Idle scanning is decorative; actual sensing activity has its own indicator.

Use readable combinations rather than force every animal condition onto a single alertness scale. For example: content + idle + calm is a relaxed creature; curious + listening + attentive is investigating; neutral + processing + attentive is working; frightened + idle + urgent is alarmed. Sleeping sets a resting pose and suspends ambient scanning. The first interface rejects sleeping with attentive/urgent attention, frightened mood or an active listening/processing/speaking activity; a wake transition must select a compatible awake state.

Sleeping is a visual/experiment state in this milestone, not ESP32 deep sleep: management, health reporting and OTA stay available. A sleeping avatar with live management traffic is valid. Offline, an expired experiment-state lease, and missing telemetry must not be represented as sleep. Busy working must come from a declared task/subsystem state, not simply a high processor load.

Communication frequency describes measured events over a rolling window (proposed five seconds), with smoothed transitions and a cap on visible pulse frequency. Preserve exact TX/RX rates in status. Track experiment/application traffic separately from management heartbeats and firmware transfers where instrumentation can distinguish them; otherwise label the available total and report experiment traffic as unavailable. Routine health polling must not make the creature appear socially chatty. Quiet communication and a broken link need different indicators. Final rate thresholds are explicit configuration, calibrated against actual traffic in the implementation plan.

Do not invent a numerical hardware health score. If an experiment supplies a vitality level, document its meaning for that experiment; it is not a battery, RAM or SD-wear percentage. The Doom injury-enabled profile can map its five damage tiers to these five levels. A nonviolent theme could express the same levels with five pips or a condition gauge. Abrupt reported faults need not progress artificially through every injury level.

Trust, exclusion and rogue-node classifications are reserved for later experiments that supply explicit evidence/state. Do not infer them from a missing packet or represent them as injuries by default.

## Theme contract

State selection produces a theme-independent snapshot; a theme maps it to frames, icons, timing and overlays. No control command names a Doom filename, a blood level or a fruit-fly body part. Theme manifests map semantic expressions to bounded frame sequences; unsupported expressions fall back to a neutral avatar plus an explicit icon/label, never an unrelated expression.

| State | Doom test theme | Nonviolent icon theme | Possible future fruit-fly theme (concept only) |
| --- | --- | --- | --- |
| Calm idle | Healthy face glances, returns ahead | Quiet eye/attention symbol | Subtle antenna movement |
| Sleeping | Closed-eye overlay or SLEEP mark if no suitable sprite exists | Closed eyes with slow breathing-like motion | Resting pose, folded wings |
| Attentive | Forward-focused gaze and attention mark | Focus brackets | Antennae orient toward stimulus |
| Curious | Glance plus curiosity mark | Eyes orient with a small question mark | Antenna/head orientation |
| Content / happy | Suitable healthy expression or contentment icon | Soft smile and relaxed movement | Relaxed pose and gentle wing movement |
| Frightened | Suitable alarm expression or fear icon; no injury required | Wide eyes and restrained recoil | Recoil or tucked posture |
| Processing | Neutral face plus moving dots | Bounded dot animation | Small orbiting dots |
| Waiting for input/result | Neutral face plus WAIT indicator | Pause/hourglass | Still pose plus waiting mark |
| Speaking | Expression plus output indicator | Animated sound-wave icon | Output indicator beside avatar |
| Degraded/fault | Neutral face and warning mark by default | Warning/status symbol | Warning/status symbol beside avatar |
| Explicit experimental vitality | Damage tiers only when injury profile enabled; otherwise condition pips | Condition pips/gauge | Condition gauge; no injury art required |

The icon and fruit-fly columns are future design examples, not first-release deliverables. Initial fallback symbols use inexpensive procedural shapes/text without requiring SD artwork. Dynamic interface elements are local overlays and small animations, not a general UI scripting engine. Future themes must expose the same underlying status and diagnostic access without changing experiment behaviour or health classification. The frame manifest records that a scene contains injury imagery; the nonviolent profile must never select those frames, including during automatic demos or fallback.

Generate additional Doom Guy expression artwork when the existing sprite set cannot clearly express the approved states. Use the existing healthy face as the visual reference, preserve the 64×64 composition/palette/identity, and review sleep, contentment, fear and mouth-open/closed candidates at actual panel resolution. Generated pixels do not replace the original source assets. Keep source references, generation provenance and selected-frame hashes. A talking loop should vary mouth aperture, not cycle injury or weapon expressions.

Use posture/expression for mood, gaze and movement cadence for attention, a small task cue for activity, and brief peripheral marks for communication. Avoid a permanent wall of text or an icon for every dimension at once. Keep node identity and genuine warnings readable. Use minimum expression dwell and eased/stepped transitions to avoid visual chatter; warnings and explicit wake events can interrupt decorative motion promptly. A frightened pose should be visually distinct from curious attentiveness without rapid flashing. Exact source frames for contentment, fear or sleep remain subject to visual review; use icons where the Doom sprite set cannot express them clearly.

## Display behaviour

Render the face over the full canvas. Reserve a small dark-backed top overlay for the node label and a concise state label; use bottom/corner indicators for links, activity and media fallback. Overlay pixels may cover artwork but must not rescale or crop the source face. Colour must be accompanied by a symbol or short label for faults, stale commands and simulated states.

| Condition | Face / indicator behaviour |
| --- | --- |
| Starting | Short startup expression and `BOOT`; transition once initial observations are available |
| Normal local operation | Healthy neutral expression with occasional subtle glances; `IDLE` does not certify every manual test |
| Active communication | Brief TX/RX indicator pulses from actual local traffic counters/events; do not replay every packet as a whole animation |
| Confirmed degradation | Warning icon and `WARN`, with precise reasons on the diagnostic page and in status JSON; no automatic injury imagery |
| Wi-Fi unavailable | Wi-Fi indicator reports loss; do not mark the whole node offline if ESP-NOW remains usable |
| No recently observed peer/manager | Distinct waiting/stale link indication; local face continues independently |
| Updating firmware or maintaining SD | Explicit maintenance state; animation may pause and the last frame may remain while flash operations run |
| Explicit experiment state | `EXP` marker plus requested alertness/expression until its lease expires; hardware warnings remain visible |
| Missing/invalid SD face pack | Bundled face continues, with reported media fallback rather than a black screen |

Hardware severity is derived from explicit current check results, with a short grace period/hysteresis for startup and transient connectivity. Manual visual/audio acceptance pending, unset RTC time, incomplete historical full-capacity SD tests and absent optional equipment must not be converted into hardware failures. Preserve reason codes and freshness instead of inventing a health percentage. A powered-off node cannot display its own offline state; the controller/host reports that condition.

Priority: maintenance indication → genuine operational warning → unexpired experiment state → normal ambient behaviour. Communication indicators are independent overlays. Experimental 'health' or mood must never overwrite the reported measured hardware health.

Default animation cadence is at most 8 FPS, using elapsed time rather than blocking delays. This is a rendering ceiling, not eight expression changes per second. Proposed calm idle timing: hold forward for 2–5 seconds, glance left or right for 0.4–0.8 seconds, then return forward. Do not cycle every expression in a sprite row or oscillate continuously between left/right. Use a separate slower blink if suitable frames exist; do not fabricate it from injury frames.

Ambient glance timing varies per node so all sixteen do not move in lockstep after a shared power-on. Keep cosmetic randomness separate from experiment randomness and expose its seed for reproducible previews. An explicit urgent state may shorten dwell times but must not cause rapid full-panel flashing. Ambient movement is cosmetic, not evidence of inference, communication or awareness. Coalesce traffic bursts into bounded visible pulses; distinguish local send activity from application-confirmed delivery.

BOOT and existing remote `next_page` retain access to all diagnostic pages. Enter diagnostics on user request, retain them for a bounded review interval, then return to the face. Long-press sound behaviour remains available. Exact page-return interval is a plan-level choice (proposed 60 seconds).

## Media storage and rendering

1. Generate a deterministic RGB565 little-endian, row-major pack from the selected PNGs, with schema version, dimensions, frame table, source hashes and pack SHA-256. Preserve source paths and attribution in a local asset manifest.
2. Include the initial pack in the application image so the first OTA install can display immediately and seed the SD without USB/card handling. Check actual application size against the existing OTA partition limits.
3. Store the pack only under a Flockinator-owned, digest-qualified directory, proposed `/flockinator/media/faces/<pack-digest>/`. Publish a completion manifest only after length/hash verification. An interrupted or invalid copy must never become the active pack. Retain unrelated files and previous complete packs.
4. Seed missing packs using the storage worker with bounded chunks when neither formatting/testing nor OTA owns storage resources. A valid matching pack is not rewritten on every boot. Do not auto-format, restart capacity tests, or block management while seeding.
5. Prefer the verified matching SD pack, loading it into a bounded PSRAM cache. Animation performs no per-frame card reads/writes. On card/pack/PSRAM problems, render the compiled pack directly and report the fallback reason. Clear/overwrite the entire frame before composing overlays to avoid trails from black pixels.
6. Limit the initial implementation to the bundled pack format and bounds. Arbitrary file uploads, runtime PNG/GIF/video decoding, audio playback, arbitrary paths and automatic deletion of old packs are outside scope. New artwork can initially travel with the normal firmware image.

## State control and observability

Extend the existing authenticated `/v1/control` path and target-bound USB command dispatcher with bounded display commands. Preserve existing authentication, target identity, replay checks and queue ownership. Network callbacks enqueue validated requests; they do not draw or read SD directly.

- `display_auto`: clear a temporary expression and resume measured state.
- `display_state`: provide activity (`sleeping`, `idle`, `listening`, `processing`, `waiting`, `speaking`), attention (`calm`, `attentive`, `urgent`), mood (`neutral`, `curious`, `content`, `frightened`), optional experiment vitality (integer 0–4) and a required finite lease of 1–300 seconds. Activity is required; attention defaults to calm, mood to neutral, and omitted vitality clears the previous value. Validate the whole request and the sleeping compatibility rule before atomically replacing the temporary state. Reject unknown fields/enums, incompatible combinations, missing/out-of-range leases and malformed inputs. These are declared experiment states, not evidence that ASR, speech or inference is running. Communication rates remain observed telemetry; demo animation of traffic is labelled DEMO and does not alter real counters.
- `display_profile`: choose `doom-calm` (default) or `doom-injury-test`. Profile selection is volatile; reboot returns to `doom-calm`. Report the active profile in status. Switching profiles must not reset the experiment lease or alter measured state. Other avatars are not selectable in the first release.
- `display_demo`: finite preview of the supported states, visibly labelled `DEMO`, ending automatically in measured state. No sound or other physical action is triggered by this command.
- `display_random` (owner clarification, 16 October 2026): enable autonomous cosmetic expression selection on each node. Choose among healthy idle/curious/happy, sleeping, listening, working, waiting, silent talking and frightened states, holding each for a locally chosen 3–7 seconds and avoiding consecutive identical choices. Use a node-specific deterministic cosmetic seed, independent of experiment randomness. Label output `DEMO`, expose random-mode/selection-count status, and make no sound or storage writes. Continue locally without host traffic until `display_auto`, an explicit state/demo command or reboot. Invalid commands leave the mode unchanged; diagnostics and genuine warnings retain their existing priority. The 21-second sequential demo remains separate. Enabling again restarts the local sequence. Ordinary boot remains calm.

This is an extension of the approved display module in response to the owner's explicit request that each node choose expressions. Verify local scheduling across timer wrap, no immediate repeats, valid sleeping combinations, stopping/command override and visible progress without continuing host commands. Clear expired stored expression leases when observed, preventing their reactivation after a complete timer cycle. Deploy the tested image through the existing Wi-Fi updater, first A1 then the remaining nodes; no repeat of the unchanged media/renderer's full 30-minute soak is required for this policy-only increment.

Overrides are volatile and clear on reboot. Expiry uses monotonic time; stale remote commands cannot leave a node looking permanently busy. No new persistent identity or partition migration.

Status JSON reports view, theme/profile, activity, attention, mood, optional experiment vitality, state source (`observed`, `experiment`, `demo`), underlying observed health and reasons, override time remaining, Wi-Fi/peer freshness, measured communication rates/window/scope, media source/digest/verification/provisioning result and animation timing/drop counters. Simultaneous health warnings and experiment states remain separately observable even when one has visual priority. Avoid writing animation state to NVS or SD. Expose unsupported or unavailable observations explicitly.

This spec defines a small display input contract only. Routing inference, trusted/untrusted membership, acoustic communication, per-peer directional glances, synchronised choreography and ARGB pathways require their own later experiment contracts.

## Requested talking extension

The owner wants to see and hear the swarm talking, with S2S explicitly outside the objective. Deliver the visual firmware first, then a bounded audio increment using short pre-rendered utterances. Existing Doom Guy clips are candidates only: audition content before selecting them; financial advice, gunfire or death effects are not substitutes for a neutral utterance. Do not assume files named `wake_here` or `processing` contain the intended words until listened to. If unsuitable, source or generate separate short neutral lines; no live TTS service or cloud credentials are required on the ESP32.

Use 16 kHz signed 16-bit mono PCM/WAV assets converted on the host, with the node output adapter duplicating samples into the existing stereo I2S format. First clip limit: three seconds, 96,000 PCM bytes each, four clips maximum (384,000 PCM bytes plus metadata). Validate size, format and digest before playback. This avoids adding an on-device MP3 decoder for the first demonstration. Keep assets in a separate verified speech pack on SD with bounded RAM caching; selected short clips may be bundled for the same OTA provisioning path. An unavailable clip produces a reported error and no sound.

Drive mouth aperture from the level of outgoing audio at the playback cursor, with smoothing and a closed mouth during silence. It is approximate audio-envelope synchronisation, not phoneme lip-sync. A commanded visual speaking demo is explicitly labelled simulated. Microphone levels can show sound being heard, but must not directly trigger speech or be used as the mouth-sync source. Do not assume the existing codec configuration performs acoustic echo cancellation.

Playback uses a nonblocking worker, one active clip per node, no unbounded queue, conservative existing output level and a minimum five-second gap between accepted utterances. Authenticated `say` starts one allowlisted clip; `silence` stops playback and clears queued audio. No automatic speech at boot, no raw microphone loopback, no automatic acoustic replies and no sound from the ordinary visual demo. OTA and destructive storage work preempt playback and close/release its media resources.

A finite host-driven chatter demo first exercises one node, then four, then the fleet, with an explicit maximum concurrency and duration. Initial fleet ceiling: two simultaneous speakers for at most 30 seconds; the owner can later raise this to explore the intended chaos. Commands expire locally and each clip has a hard time limit, so a disconnected host does not leave autonomous chatter running. No phase-aligned choir or precise inter-node audio clock is promised.

## Tech stack and project structure

Retain the working ESP-IDF 5.5.4/PlatformIO node build and existing double-buffered HUB75 driver. Do not import the separate Doom Guy Arduino application or change the LilyGo toolchain.

- `firmware/node-platform/`: display state machine, renderer, storage-worker integration and bounded control handling.
- `firmware/node-platform/test/`: native state/pack/renderer tests alongside existing policy tests.
- `assets/node-state/`: selected sources, generated pack and provenance manifest; keep this local game-derived prototype material out of public release packaging.
- `tools/node-commissioner/`: uv-managed conversion/preview support and authenticated display commands/tests.
- `docs/validation/node-state-display/`: previews, canary measurements, fault tests and fleet rollout evidence.

## Commands

Existing commands, from `/Volumes/devops/flockinator`:

```sh
$HOME test --project-dir firmware/node-platform --environment native
$HOME run --project-dir firmware/node-platform --environment waveshare-s3
uv run --project tools/node-commissioner python -m pytest tools/node-commissioner/tests -q
```

Run PlatformIO test/build sequentially for the same project. The implementation plan must specify exact asset generation, preview and authenticated control CLI syntax before implementing those new commands; they do not exist yet.

## Code style

Follow the existing C++ adapters and host-testable models: four-space indentation, explicit limits, fixed/bounded buffers, checked allocation and monotonic elapsed-time comparisons. Python uses uv, type annotations and structured errors. Rendering consumes a snapshot rather than querying network or storage on the draw path.

Illustrative contract, not implementation:

```cpp
enum class StateSource { Observed, Experiment, Demo };
struct DisplaySnapshot {
    StateSource source;
    uint32_t override_remaining_ms;
    bool wifi_connected;
    bool peer_recent;
    bool media_fallback;
};
```

## Testing and success criteria

- Visually review a contact sheet of all selected frames and a labelled native-64×64 preview before firmware rollout. Healthy idle must not accidentally select a damaged face; animations must not cycle between damage levels.
- Preview each semantic state in the Doom theme, plus simultaneous cases (processing with RX, listening with a storage warning, waiting after experiment-input expiry). Profile switches must preserve underlying state and lease expiry. The nonviolent profile must exclude injury imagery in normal, warning, demo and fallback paths. Record missing expressions and review generated candidates before selecting them.
- Confirm calm idle spends most of its time facing ahead, returns ahead after each glance and is visibly distinct from explicitly requested urgent attention. Verify supported experiment vitality levels separately from measured hardware health.
- Preview sleeping, relaxed/content, curious/listening, busy/processing and frightened/urgent as recognisable combinations. Verify sleeping keeps management/OTA alive, rejects incompatible requests and expires normally. Verify quiet application traffic remains visually quiet during management polling and that lost connectivity never silently selects sleep or fear.
- Native tests cover priority, lease expiry/timer wraparound, independent link conditions, activity coalescing and bounded frame indices. Renderer checks cover overlays within 64×64, full clearing and brightness limits.
- Host tests cover deterministic conversion, exact pack sizes/endianness/hashes, malformed control requests and node identity binding. Pack loader tests reject truncated, corrupt, oversized or unsupported packs.
- On A1, install over Wi-Fi, prove changed boot/partition and correct image hash, verify first-boot validation plus retained management receiver. Show the face and all declared demo states for owner visual review.
- Verify SD seeding and a second boot without rewriting a valid pack. Exercise missing/corrupt/incomplete pack and allocation-failure paths; retain a usable face and authenticated maintenance access. No SD reformat or destructive capacity test is required.
- Run a 30-minute canary soak with face animation, sensor polling and health traffic. Require no unexpected reset, watchdog event or monotonic heap loss. Record dropped frames and compare authenticated status latency to the same node's baseline; aim for p95 below one second on this LAN and investigate any significant regression.
- Verify another OTA and ESP-NOW receiver operation with the face firmware before fleet rollout. Animation must yield to updates; a deliberately paused display during flash writes is acceptable and documented.
- Audio increment: prove finite playback, allowlisted clip/digest validation, cooldown/busy rejection, silence, silence-gap mouth closure and preemption by OTA/storage. Require owner audible acceptance and approximate mouth-sync confirmation on one node before four/fleet chatter. Microphone response to neighbours may be observed but must not trigger a feedback/reply loop.
- After owner acceptance of the physical A1 appearance, roll out to the other fifteen, verifying identity, firmware, media digest/source and recovery to the default face. Report actual per-node results; do not claim visual acceptance from software alone.

## Boundaries

- **Always:** preserve identity, both OTA paths, rollback, diagnostic access, resource arbitration, brightness cap and evidence. Keep the Doom Guy source project unchanged. Prioritise management over animation.
- **Ask first:** materially different state semantics or aesthetic, new dependencies with significant footprint, destructive storage changes, partition changes, or public distribution of game-derived artwork.
- **Never:** infer intelligence from an animation, silently turn simulated distress into a hardware failure, erase cards to install media, expose credentials, import unrelated Doom Guy financial/cloud behaviour, or label all nodes healthy merely because they render a face.

## Review decisions

Approved display direction: animal-like expression built from independent activity, attention and mood; nonviolent Doom face with calm glances; truthful link/health overlays and measured communication frequency; temporary explicitly marked experiment states and optional vitality; bundled pack plus verified SD copy. Sleep remains a visual state with management available. Injury imagery is an explicit Doom test option. The owner has requested generated missing expressions and talking; the plan stages finite speech after the visual firmware. Alternative themes and richer experimental trust/social semantics remain future work. Review the implementation plan and proposed audio bounds before implementation under the selected spec-driven workflow.

## Approved deployment increment — scripted HUD (2026-10-16)

User approval: “that looks great, now deploy to the swarm”, including a handheld
scenario launcher and live node status. The accepted visual contract is
`previews/recon-hud/DESIGN.md`. This increment runs that fictional presentation
locally on each panel, without external inference or real aircraft commands.

- Firmware 0.8.0 renders procedural 64×64 HUD frames at 8 FPS, brightness 25%,
  with the existing 50% cap. Ten motion treatments, forward-only takeoff,
  20 seconds of deployment before sightings, CAM/WH/BH/NV modes, compass,
  scripted message borders, endings and five-second fleet gap are retained.
- Handheld presets: Mixed outcomes, Survey & return, Link disruption. Goal:
  Observe, Compare reports, or Recovery. Goals select presentation sequences,
  not operational targeting/navigation. Survey length 64 or 96 seconds, repeat
  optional. Simulated labels must remain distinct from actual hardware health.
- All nodes share a run ID and deterministic seed. Start is scheduled against a
  handheld deadline, with per-recipient relative delay. Acknowledgements indicate
  acceptance; authenticated node health verifies actual run/state. Missing or
  incompatible nodes remain visible and are never counted as confirmed.
- Start and stop use the existing per-node HMAC identity plus a fresh node
  challenge. Byte-identical retries are idempotent; changed/replayed requests
  cannot restart the presentation. Commands are bounded and validated.
- Stop returns to a ready HUD. Reboot does not resume an old run. Wi-Fi OTA,
  ESP-NOW image transfer, identity, SD files and diagnostic pages remain usable.
- Console reports last-observed simulation state separately from stale/offline
  health, refreshing active status at approximately five-second intervals.
- Validate portable scheduling/rendering and protocol bounds natively, build
  both firmware targets, deploy A1 first and verify actual boot/run/stop, then
  deploy the remaining fifteen. Save evidence and release manifests.

### Overview telemetry correction (2026-10-16)

Node 0.8.1 reports a five-state aircraft summary over HTTP and authenticated
ESP-NOW. The summary is computed on the node from its current simulation and
retains terminal outcomes throughout BLANK, independent of which animation
frames the remote happened to observe. See SPEC-management-console.md for
READY/OM/KIA/MIA/CHARGING semantics and the compatible reserved-byte extension.
The 64×64 renderer, brightness, media files and mission command format are
unchanged. No flight, navigation or real target-selection functions are added.
