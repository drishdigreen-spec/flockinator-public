# Management console: first LilyGo prototype

## Approved live commissioning milestone — 13 October 2026

### Approved regional refresh follow-up — 13 October 2026

Owner approved proceeding after the display-refresh research. Compare rendered pixels with the last displayed frame and clear/redraw the smallest enclosing changed rectangle, aligned to the vendor's four-pixel output groups. Preserve full-screen clears at startup, page transitions, explicit Refresh and sleep-status presentation. Identical frames cause no automatic display write. Keep existing vendor waveforms and the 15-second automatic coalescing interval; do not claim flash-free updates or introduce an unverified maintenance cadence. If regional buffers cannot be allocated, retain the working full-refresh path. Validate rectangle bounds, packed grayscale row copying, erasure as well as drawing, manual/full-refresh selection, and live health during regional refresh. Optical ghosting/contrast requires the owner's visual check.

Follow-up defect report: the owner saw a finished screen followed by another redraw. Touch actions must dispatch once per contact/release gesture using fresh GT911 reports; absent/error reads must not re-arm a held contact. Diagnostics is a snapshot updated on entry or explicit Refresh, so changing refresh counters cannot sustain automatic redraws. Overview and node detail retain live automatic updates. This corrects repeated updates within the approved refresh behaviour.

The owner now requests the handheld as the live health/status destination for newly commissioned nodes, with eventual verified ESP-NOW flashing. Owner approved this addendum on 13 October 2026 with "proceed you have my approval", alongside `SPEC-flock-network.md` and `SPEC-cluster-deployment.md`; the historical demo milestone below remains its own evidence record.

Owner clarification: the console is a portable remote, image/media catalogue and possible logging endpoint, not the exclusive manager or a mandatory node-to-brain relay. External GPU/CPU brains, web management and central logs can coexist. Preserve direct node↔brain traffic and independent operation when the handheld is asleep. Define exclusive deployment/action ownership before enabling conflicting external managers. Node/console SD storage and optional staging requirements are captured in `docs/design/embodied-experiment-platform.md`.

Replace the startup demo with a live 4×4 A1–D4 view sourced only from authenticated registered nodes. Unseen positions show UNKNOWN; nodes age to STALE/OFFLINE. A retained e-paper image after sleep must say status is frozen. Demo fixtures, if retained for developer tests, must never populate the live table. Refresh automatically only when dirty, coalesced initially to at most once per ten seconds; touch/manual refresh remains available. Validate that receive processing continues during full-screen refresh.

Each card shows label, health and last-seen state. Detail separates firmware/version, core hardware results, deferred visual/audio acceptance and update capabilities. Explicitly distinguish Wi-Fi OTA available, ESP-NOW receiver present, console link verified and an actual ESP-NOW deployment verified. The initial 0.3.2 node must not display “ESP-NOW ready” merely because its radio starts.

Provision Wi-Fi and the private label/MAC/key roster over the independently identified LilyGo USB connection. Preserve its working display/touch/SD configuration and existing 128 GB card. Host inventory remains authoritative; adding nodes updates the private roster without recompiling a per-node console image. Record the console's real factory MAC separately. The owner has offered a second USB-C connection, allowing both targets to be tested together.

Deployment controls consume the state machine in `SPEC-cluster-deployment.md`: choose a compatible SD image and node, show progress/failure, then show post-boot verification separately. The handheld stays awake during transfer; sleeping or absent at other times must not stop the nodes. No battery-runtime claims are introduced.

Acceptance adds live A1 reception, absence/reconnect and sleep/wake freshness, malformed/replayed/wrong-node rejection, responsive touch while receiving and two actual SD-to-A1 updates with recovery tests. Existing build/native-test commands and style rules below remain applicable. The two linked provider specifications define shared interfaces, implementation locations, tests and boundaries.

Status: first milestone approved by the owner's “proceed” on 9 October 2026. Scope is the first hardware/UI prototype of the `management-console` capability, not the completed networking or cluster-deployment system. Build and hardware evidence will be recorded separately.

## Objective

Turn the owner's LilyGo T5 4.7-inch S3 capacitive-touch e-paper device into a battery-powered handheld Flockinator remote/status display. The first milestone proves the display, touch, memory and installed 128 GB card, and provides a usable sixteen-node dashboard while the physical display is being printed.

The owner identified the connected device as V2.4 with glass touchscreen, powered by USB with no battery installed. The optional unsoldered expansion header is not needed for this prototype. A ROM probe confirmed ESP32-S3, 16 MB flash and 8 MB embedded PSRAM. A complete pre-prototype flash backup was saved before uploading. Hardware observations are recorded under `docs/validation/management-console/`.

## Assumptions for review

- Landscape 960 × 540 interface with a 4 × 4 node overview, matching the physical layout.
- First delivery is hardware diagnostics plus a clearly labelled, deterministic demo dashboard.
- Demo data exercises selection and presentation without implying real node connectivity or issuing commands to nodes.
- Radio/network protocols and OTA distribution are subsequent milestones. Keep their interfaces separable, but do not choose Wi-Fi versus ESP-NOW by implementing a fake live path.
- The existing card is preserved: initial filesystem operations are non-destructive, with no automatic formatting or repair.
- Physical-button wake is the baseline for the unmodified board; touch-to-wake is not promised.

## User-visible behaviour

1. On boot, display a diagnostic summary with build identity, detected heap/PSRAM and display/touch/SD results. Peripheral failures remain visible; an SD failure must not prevent the dashboard or touch diagnostics from working.
2. Show sixteen numbered cards in four rows and four columns. Each displays a textual state and a distinguishable monochrome marker. Every demo view, including node detail, visibly says **DEMO — simulated nodes**.
3. Tap a card to inspect its identity, simulated health, firmware version and sample age. Return using a large touch target. A fixed local fixture provides healthy, stale, offline and warning examples; no invented inference or trust result is presented as observed behaviour.
4. Diagnostics includes touch alignment targets at the corners and centre, SD mount/card/filesystem information available from the driver, and memory/refresh timing information.
5. Manual refresh redraws on request. Dirty-screen updates are coalesced; an idle static screen is not repeatedly refreshed. Initial acceptance records actual refresh time and ghosting before an automatic cadence is chosen.
6. Manual sleep draws a retained **SLEEPING — status frozen** label before powering down the display and sleeping. Wake through the physical button restores operation. No runtime claim or battery percentage is displayed without a validated measurement model. Battery voltage is shown only after the board revision and measurement path are verified; otherwise show unavailable/unverified.

The first milestone has no live deployment, experiment-start or exclusion controls. Those require real command/acknowledgement and recovery semantics in their provider modules.

## Tech stack and hardware basis

Use a separate PlatformIO Arduino project based on the pinned vendor S3 branch, not the workstation's installed Arduino 3.3.0-alpha1 core. The vendor platform is `espressif32@6.12.0`; resolve and record its actual Arduino/toolchain versions in the build evidence. The vendor documentation requires Arduino ESP32 below 3.x for this driver.

- E-paper driver: LilyGo-EPD47 commit `50224221fb81a8fcf9068532374b775af84a38d4`.
- Board profile: `T5-ePaper-S3`, 16 MB flash and 8 MB OPI PSRAM, subject to hardware confirmation.
- Touch: vendor GT911 example, SensorLib 0.3.1; scan its documented 0x14/0x5D addresses and apply verified orientation.
- Vendor library metadata currently declares Button2 2.3.2 and ArduinoJson 7.4.3. Pin dependencies consistently and verify resolved versions; the vendor example's looser JSON constraint is not a lockfile.
- S3 pin definitions: SD MISO16/MOSI15/SCLK11/CS42; I2C SDA18/SCL17; touch interrupt47; user button21; battery ADC14. Confirm against the actual V2.3/V2.4 revision before relying on electrical behaviour.
- Screen buffer is 259,200 bytes at four bits/pixel. Report internal heap separately from PSRAM and check allocation failures.
- Pin initial flash/partition layout from the vendor board. Future console self-OTA partition changes require their own review; this prototype does not establish cluster OTA compatibility.

References: [vendor README](https://github.com/Xinyuan-LilyGO/LilyGo-EPD47/blob/50224221fb81a8fcf9068532374b775af84a38d4/README.MD), [touch example](https://github.com/Xinyuan-LilyGO/LilyGo-EPD47/blob/50224221fb81a8fcf9068532374b775af84a38d4/examples/touch/touch.ino), [S3 pins](https://github.com/Xinyuan-LilyGO/LilyGo-EPD47/blob/50224221fb81a8fcf9068532374b775af84a38d4/src/utilities.h), and `docs/research/console-and-deployment.md`.

## Project structure

Implemented project structure:

```text
firmware/management-console/
  platformio.ini          pinned device and native test environments
  boards/                attributed vendor S3 board definition
  include/               bounded node state and board interface declarations
  src/                   main lifecycle, hardware adapters, display and touch UI
  test/                  host tests for hit testing, state and demo isolation
  README.md              build, identity verification, upload and diagnostics
docs/validation/management-console/
                         build manifest and hardware observation records
```

Preserve `references/repos/` as reference material. Keep passwords, device credentials and private card contents out of source files and logs.

## Commands

Build and validation commands, executed from `/Volumes/devops/flockinator`. The existing PlatformIO runtime is available at the path below; no replacement Python environment is required.

```sh
# Build the console, without uploading.
$HOME run --project-dir firmware/management-console --environment lilygo-s3

# Host-side behaviour tests.
$HOME test --project-dir firmware/management-console --environment native

# Inspect available ports without selecting or resetting a target.
$HOME device list

# Only after identifying the LilyGo; set the verified path for this session.
$HOME run --project-dir firmware/management-console --environment lilygo-s3 --target upload --upload-port "$FLOCKINATOR_LILYGO_PORT"
$HOME device monitor --port "$FLOCKINATOR_LILYGO_PORT" --baud 115200
```

Build and native-test commands have passed; the firmware has been uploaded to the owner-identified LilyGo. Never default upload to the sole enumerated serial device.

## Code style and state boundaries

Use small C++ hardware adapters and bounded storage for sixteen nodes. Keep touch coordinate mapping and demo-state logic independent of the e-paper library. UI rendering consumes a snapshot; acquisition and future networking do not draw directly. Distinguish unknown, stale, offline and simulated status explicitly.

```cpp
enum class DataSource { Demo, Live };
struct NodeStatus {
    uint8_t id;
    uint32_t last_seen_ms;
    bool has_observation;
};

// No observation must remain unknown, including immediately after boot.
bool is_stale(const NodeStatus& node, uint32_t now_ms, uint32_t timeout_ms) {
    return node.has_observation &&
           static_cast<uint32_t>(now_ms - node.last_seen_ms) >= timeout_ms;
}
```

Use descriptive names, four-space indentation, explicit ownership of buffers, and structured diagnostic lines. Handle millis wraparound for intervals shorter than the counter range. Do not log an SD directory listing or file contents simply to demonstrate that the card mounted.

## Testing and success criteria

Host tests must check all sixteen card centres and boundaries, out-of-range touches, rotation mapping, stale-state transitions including counter wraparound, and that demo controls cannot dispatch live commands. Test behaviour and edge cases, not rendering implementation details.

Build validation records the pinned reference commit, resolved dependencies, firmware size, partition information and compilation result. A successful build is not hardware verification.

Hardware acceptance, performed after target identification:

- Boot to a readable overview with all sixteen cards and a persistent demo label; no clipping or ambiguous card selection.
- Tap corner/centre calibration targets and each card; verify correct selection and return navigation.
- Detect PSRAM and report available internal heap plus refresh duration. Run repeated page navigation for at least ten minutes without reset or progressive memory loss.
- Test boot with the actual card and with no card, removing it only while powered down. An unsupported filesystem is a reported result, not a reason to format it. Initial access does not create or modify card files.
- Confirm physical-button sleep/wake on the actual board, and that the sleeping screen clearly states it is frozen. Measure battery operation separately; no inferred runtime or uncalibrated percentage.
- Save observations and explicit pass/fail/unverified results. Do not mark any live networking or OTA criterion passed using simulated data.

## Boundaries

- **Always:** preserve card contents; pin versions; label simulation; verify target identity; compile before upload; separate host checks from hardware observations.
- **Ask first:** destructive formatting/erasure, board modifications, credential provisioning, or changing the agreed first-milestone scope. A routine initial firmware upload is within the requested development scope once the target is identified and preservation constraints are settled.
- **Never:** flash an unidentified port, introduce a required cloud account, present demo nodes as connected hardware, bypass the node brightness ceiling in later integration, or make the remote a required intermediary for an autonomous flock.

## Open questions

- Confirm touch registration across the full display and physical-button sleep/wake. The owner has confirmed a clear, high-resolution image on the actual screen.
- Validate battery operation after a battery is installed. Board revision and USB identity are confirmed.
- The installed 128 GB card mounts successfully without formatting. Its filesystem type has not been identified; capacity alone does not establish the filesystem.
- Validate card-absent boot when the owner can power down and temporarily remove the card.

## Core follow-on use case: handheld firmware deployment

Owner reaffirmed on 9 October 2026: the LilyGo is also the portable deployment controller for changing node firmware and experiments over ESP-NOW. This is a core product requirement beyond the installed 0.1.0 demo. ESP-NOW is the intended deployment transport; the swarm's experiment transport remains a separate decision.

- Store externally compiled Waveshare application images and descriptive manifests on the LilyGo's 128 GB SD card. The handheld selects and transfers builds; compilation remains on the development workstation.
- Select a single node, a subset, or all sixteen; support different compatible builds for different experiment roles, including deliberately rogue nodes.
- Stream bounded chunks from SD, with per-node progress, retries and explicit failure states. Do not load a complete image into RAM or tie packet reception to e-paper refreshes.
- Validate board/partition compatibility, image length/digest and authorized provenance before activation. A checksum alone does not authorize an update. Report transfer completion separately from successful reboot and the node reporting the intended build.
- Provision each node initially over USB with compatible OTA partitions and an ESP-NOW update receiver. Every subsequent experimental image must preserve management identity, update reception and first-boot health checks, or use a separately validated recovery design. ESP-NOW provides transport; it is not an ESP32 ROM/PXE flashing service.
- Configure and test inactive-slot updates and boot rollback on the Waveshare nodes. A functioning but uncooperative experimental application is not automatically recovered merely by having two slots; watchdog/recovery-entry behaviour must be designed and tested. Retain USB recovery access.
- Keep management/update authority separate from experiment messages and trust scores. Simulated exclusion or malicious inference traffic must not implicitly authorize flashing or remove the owner's management path.
- Where existing firmware supports it, select experiment parameters or assets without reflashing. Firmware replacement and experiment configuration are distinct deployment operations.
- The flock continues its installed experiment when the handheld sleeps or is absent. The console must remain awake during an active transfer and accurately reconcile interrupted deployment state after restart.

The next deployment milestone should prove one real node receiving image A and then image B from the LilyGo SD card, reporting the expected build after each boot and retaining the ability to update again. Test interrupted transfer, invalid image, failed first boot and loss of console before expanding to sixteen. ESP-NOW component integration with the current Arduino 2.0.17 e-paper toolchain remains unverified; no fleet throughput claim is made.

Evidence: Espressif supplies an [ESP-NOW OTA initiator/responder example](https://github.com/espressif/esp-now/tree/c3b5f9be245f1a80db9cb938600566aa6a8dd1e5/examples/ota). Its existing data callback reads a flash partition; SD-backed reads are an adaptation to implement. [ESP-IDF OTA documentation](https://docs.espressif.com/projects/esp-idf/en/v4.4.7/esp32s3/api-reference/system/ota.html) explains application slots, validation and explicitly enabled rollback. These establish feasibility, not completed integration on Flockinator hardware.

## Approved mission launcher increment (2026-10-16)

The user requested deployment of the approved HUD and use of this remote as its
commander interface. Firmware 0.3.1-missions adds Missions to the toolbar; touch
alignment remains under Diagnostics. Tap Scenario, Goal, Survey or Repeat to
cycle settings; Launch schedules a new scripted run, Stop all returns reached
nodes to READY. The grid follows the photographed panel arrangement (A1 B1 C1 D1
across the top). Actual health stays visible independently of the last reported
simulation state. These are presentation controls, not aircraft control outputs.

Three scenarios: Mixed outcomes, Survey & return, Link disruption. Three goals:
Observe, Compare reports, Recovery. The duration setting is the survey phase;
orders, takeoff, twenty-second deployment and endings add to total run length.
Nodes execute locally and continue if the handheld sleeps. A new handheld boot
rediscovers node telemetry but does not silently issue a new mission.

Protocol: FLK2 authenticated kinds 12/13, using an existing OPEN/fresh challenge.
Twenty-byte versioned command contains action, scenario, goal, repeat, survey
seconds, run ID, seed and relative start delay. Identical retries return cached
acceptance. A shared run ID is checked in live health before showing confirmed
running nodes. Nominal start deadline is twelve seconds after Launch; RF retry
latency can introduce skew, so this is not a precision clock synchronization
service. Unsupported, stale or timed-out nodes remain failures, not successes.

Health extension: accept legacy 96-byte payloads or version-1 128-byte payloads.
Offsets 96 version, 97 running/waiting bits, 98 state, 99 sensor, 100 run u32,
104 elapsed ms u32, 108 cycle u32, 112 scenario, 113 goal, 114 variation,
115 repeat; bytes 116/117 are extended by the Overview correction below.
The original release used five-second polling and screen checks; the correction
below supersedes that timing. Stale/offline health remains explicit.

Firmware images still stage on SD and deploy through the existing authenticated
ESP-NOW receiver. This increment does not erase cards or replace identity keys.

## Overview correction requested 2026-10-16

Replace rapidly changing animation names with five node-authoritative simulation
statuses: READY (idle, scheduled, orders or reserve), OM (airborne including return
and landing), KIA (completed KILL countdown or crash aftermath), MIA (simulated
loss of contact or exhausted battery), CHARGING (returned and recharging).
Hold terminal outcomes throughout the blank intermission; reset on the next cycle
or Stop. These describe simulated aircraft, not ESP32 hardware condition.

Nodes report the summary in reserved health bytes 116 (schema 1) and 117
(status 0 READY, 1 OM, 2 KIA, 3 MIA, 4 CHARGING). Legacy/invalid summaries show
`--`, never guessed READY. Actual missing telemetry is a separate Stale/Offline
marker; after six seconds without an observation Overview suppresses the current
mission label. Detailed diagnostics retain raw animation and hardware state.

Poll each node every two seconds, paced across the fleet. Overview checks for
changes every second; unchanged pixels do not trigger an e-paper refresh. Leave
a touch-reading interval after refresh. Keep Diagnostics static. Target nominal
visible status latency below five seconds, with measured RF exceptions recorded.

Implementation/verification: shared summary semantics and boundary tests, wire
extension and UI tests, actual-font preview, sequential builds, A1 canary then
fleet OTA, identified console app-only flash, live comparison of remote reports
against node HTTP telemetry and display refresh logs. Preserve SD, identity,
rollback, command authentication and manual refresh behaviour.

Live verification refinement: two nodes intermittently missed consecutive health
polls. Retry an unanswered poll with the same authenticated challenge at 500 ms
intervals, at most twice before the next two-second poll replaces it. Pace retries
at least 40 ms apart globally. A consumed reply cannot refresh telemetry again.
Expose a retry counter for evidence; freshness still depends on received reports.
