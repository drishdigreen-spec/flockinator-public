# Node platform: commissioning and resident hardware diagnostics

Status: **approved by owner**, 13 October 2026 ("Approve the commissioning specification"). Implementation is authorised. The management-console prototype is separate. A1 runs bring-up firmware 0.3.2 with verified identity, two Wi-Fi OTA updates and tested rollback; physical hardware acceptance remains pending. Progress is recorded under docs/validation/nodes/A1 and tasks/node-platform/.

## Objective

Give each Waveshare ESP32-S3-RGB-Matrix a persistent A1–D4 identity, a documented hardware record, an independently running 64×64 diagnostic display and a repeatable host commissioning process. Flash once over USB, then fit the controller/panel/speaker/card and complete visual, audible and network checks without repeatedly dismantling the assembly. Keep speaker-case redesign parked during this work.

This is one node-platform capability with a host commissioning client. Its network probes and host maintenance operations are limited commissioning facilities; it does not implement the swarm inference protocol or LilyGo deployment user interface.

## Assumptions for review

- Sixteen P2.5 64×64 panels with the previously researched Waveshare ESP32-S3-N32R16 controllers; confirm each board before writing it. A USB descriptor alone cannot prove the board model.
- Assign front-view positions in order A1…A4, B1…B4, C1…C4, D1…D4. The same common firmware image serves all nodes; identity lives in internal NVS, independent of SD card.
- Use the owner's existing **8–64 GB cards**. Target one FAT32 partition. Do not require buying matching cards. A 64 GB card must be validated after explicit FAT32 formatting; capacity does not imply existing filesystem or compatibility.
- Proposed default is Wi-Fi management plus a separate ESP-NOW peer test. Wi-Fi credentials are supplied locally and redacted from reports. ESP-NOW-only operation remains usable for diagnostics if no network credentials are supplied; Wi-Fi management tests then remain pending.
- Initial display brightness is 25% of the driver's full scale, with an enforced maximum of 50% across boot, patterns and configuration. The panel requires its intended external 5 V supply; USB-only controller programming does not establish panel power or permit declaring the panel faulty.
- Speaker sound and panel pixel correctness require owner observation. Firmware can test interfaces but cannot claim to have seen a working panel or heard a speaker.

## User workflow

1. Connect one controller by its USB data port. The host lists candidates and binds the owner-selected physical board to the expected eFuse identity. Never silently choose the first port or confuse the LilyGo with a node.
2. Read chip model/revision, factory MAC and flash identification/capacity. Save a verified original flash backup before the first replacement unless the owner explicitly waives preservation; keep backups private and never display their contents. Record protection/encryption state; stop writing if it prevents the reviewed provisioning path.
3. Install the validated shared bootloader/partition/application build, provision label and management credentials, and reboot. Never burn eFuses or erase unrelated devices. Routine repeat application flashes preserve identity; partition migration/full erasure requires a separate recovery procedure.

Owner instruction, 14 October 2026: skip original-flash backups for the remaining fresh fleet controllers (A3–D4). Use `provision --skip-backup` and record the waiver in the bound transaction before writing; resume retains that decision. Identity/geometry/protection checks, flash verification, credential provisioning, reboot readback and inventory evidence still apply. Preserve A1/A2's existing backups. Evidence must distinguish a waived backup from a verified backup.
4. Confirm the installed build digest and identity after boot, run available automatic checks and atomically record the result before offering the next label. Host interruption or disconnect must not advance the successful-node count.
5. Fit the controller to its panel, connect speaker and insert the card with power off. On boot the installed diagnostic loop resumes automatically; no SD assets are required to display status or generate its test tone.
6. Review the named panel, hear a short identification/test sound, inspect microphone and sensor pages, and record manual acceptance by node label/MAC from the host. A short BOOT-button press changes pages; it does not silently certify every test.
7. Repeat for the next node. A1 is the first complete bring-up fixture; A2 provides the first real ESP-NOW partner. Perform per-node checks for all sixteen, retaining explicit failures/pending items.

## Identity and evidence

Extend `docs/inventory/nodes.csv` without losing existing rows. Store detailed per-node JSON and timestamped test runs under `docs/validation/nodes/<label>/<run-id>/`. The source of truth binds node label to eFuse/base MAC, with actual Wi-Fi STA and ESP-NOW interface addresses recorded separately.

Record: chip family/revision; readable board revision as owner-supplied or unknown; flash JEDEC ID and measured size; PSRAM detected size and bounded memory-test result; firmware version, application SHA-256, bootloader/partition digests and dependency lock; reset reason and uptime; boot counters; current label; SD CID/card serial/manufacturer/capacity where available, partition/filesystem/free space; connectivity and test results with timestamps.

Do not invent a factory serial number where the device exposes no separate serial. Distinguish the removable card's serial from the board identity; a MAC/CID is an identifier, not proof of management authority. Capacity reported by a card is not proof that every sector is genuine or healthy.

Every test result includes test ID, status, observed value, error/detail, run/build ID and evidence source. Status vocabulary: **PASS, FAIL, PENDING, NOT_PRESENT, UNSUPPORTED, STALE**. Use separate provisioning, automatic-test and human-acceptance states rather than a single premature “all passed”. Reassignment is explicit and retains history; duplicate label/MAC conflicts block writing. Maintain atomic inventory updates and an append-only event history, with resumable recovery after host interruption.

Credentials, management keys and original flash backups are excluded from public reports/version control. Use a private per-project credential store with restricted file permissions; reports carry key identifiers only.

## Resident diagnostic suite

| Check | Automatic evidence | What remains manual or conditional |
| --- | --- | --- |
| Boot / identity | Correct persisted label, MAC, firmware digest, reset cause; watchdog/reset counters | Printed physical label agrees with panel position |
| Internal flash / NVS | Measured capacity; own-namespace read/write/readback; reboot persistence | No destructive whole-flash stress test |
| PSRAM / heap | Detected size; bounded allocated-buffer patterns; free/minimum internal and DMA-capable heap | A sampled buffer pass is not a full-memory certification |
| HUB75 display | Driver starts and produces frames without allocation/refresh errors | RGB order, scan mapping, all 4096 pixels and orientation require inspection |
| Speaker | Codec/amp setup and finite generated tone/identification sequence | Owner confirms output, gross distortion and rattles; register ACK alone is not audible PASS |
| Microphones | Separate intended microphone-channel capture, sample counts, clipping/noise metrics and live level bars | Tap/speech response and correct channel mapping; echo-reference slot must not be mislabeled as microphone two |
| Temperature/humidity | SHTC3 read/CRC/status with live values | Plausibility vs room conditions; no calibration claim |
| IMU | QMI8658 identity and changing acceleration/gyro samples | Response to movement while convenient; fixed installation can remain pending for motion acceptance |
| RTC | PCF85063 responding, advancing clock and validity flags | Unset clock is TIME UNSET; battery-backed retention not tested without a battery/power-cycle test |
| BOOT button | Debounced runtime press event | Owner presses it; reset/programming role retained |
| SD | Card enumeration, CID, capacity, filesystem; isolated small create/write/close/reopen/read/checksum/delete test | No card = NOT PRESENT; unmountable card is not auto-formatted; no full-capacity stress claim |
| Wi-Fi | Radio scan separately from configured association, DHCP/IP/RSSI/channel | No credentials = PENDING; internet and cloud not required; host reachability is a separate round trip |
| ESP-NOW | Initialisation plus nonce/sequence request-and-reply with a real identified peer, RTT/loss/timeouts | No second node = NO PEER/PENDING. A send callback does not prove application delivery |
| Maintenance | Authenticated remote status/test invocation and Wi-Fi image update with correct post-boot identity | LilyGo-initiated ESP-NOW deployment is a later cluster-deployment milestone |

Tests have bounded timeouts and independent failures. A missing/bad SD or unreachable AP must not prevent local diagnostics. Do not continuously write the card or NVS in the display loop. Run integrity checks at boot/on request, retain a bounded in-memory history and rate-limit persisted events. Preserve unrelated card files and any pre-existing diagnostics directory entries; create a uniquely owned test file and only remove that file.

No automatic microphone-to-speaker live loopback: it can produce feedback. Generated sound has a conservative fixed level, short duration and rests; a brief boot cue can be disabled, while recurring audio tests require an explicit test-mode selection. Audio tests are not ASR/AEC quality validation. Unused expansion pins, USB host capability, BLE peer links and external sensors are not declared passed without fixtures.

## 64×64 screen behaviour

Keep the assigned node label visible in the dashboard and on each test page. Use actual pixel-fit checks, not an assumed text layout. Show a large A1/D3 label, compact build ID and paged status; full identifiers and error details remain available via serial/network.

Proposed pages: summary; panel patterns; audio levels/tone; live sensors/RTC; SD; Wi-Fi/ESP-NOW; identity/build/reset diagnostics. Rotate automatically with a short-button page override and bounded pause. Use text/symbols as well as colour for status. Long MAC/IP/error strings receive their own page or bounded scrolling, never illegible compressed text.

Panel tests cover R/G/B/white/black, row/column scans, checkerboards, corner coordinates and a moving marker at native 64×64 resolution. Maintain an identity overlay for most patterns and provide a brief full-field phase to expose pixels otherwise covered by it. All patterns retain the brightness ceiling. Summary distinguishes PENDING from FAIL and shows whether the results are live or from a previous boot/run.

## Networking and avoiding repeat USB handling

Commissioning state and test controls use a versioned bounded protocol over USB serial and authenticated Wi-Fi. ESP-NOW discovery/probes carry no erase/update/configuration authority. Keep packets compatible with the planned older console stack (at most 250 bytes until cross-version transport validation). Wi-Fi and ESP-NOW share the radio/channel: while associated, peer tests use the AP's channel; without Wi-Fi, use an explicitly displayed/configured common test channel. Do not promise simultaneous different-channel operation.

Provision a per-node management credential by USB. Mutating wireless requests are authenticated, freshness/replay checked and scoped to a specific board; discovery labels/MACs cannot authorize writes. Expose no unauthenticated format, arbitrary-flash or shell endpoint.

Install a reviewed partition table with NVS, OTA metadata and two equal application slots sized for the selected measured 32 MB device and foreseeable base firmware. Enable boot validation/rollback. Future images must preserve the identity namespace, partition contract and maintenance service or explicitly migrate them. A failed peripheral alone must not cause an endless rollback loop; distinguish application health from test outcomes.

**Approved adjustment to the earlier inventory rollout gate:** prove two successive host-initiated Wi-Fi OTA updates on A1, retained identity, rejected invalid image and interrupted transfer/failed-first-boot recovery before releasing the common commissioning image to the fleet. This allows initial hardware commissioning without waiting for the LilyGo deployment UI. LilyGo SD-backed ESP-NOW image delivery remains required later and is not marked complete by this host test. If Wi-Fi is declined, resolve the update proof before fleet rollout rather than claiming future USB-free updates without a tested path.

## SD cards: FAT32 and explicit remote maintenance

**Owner approval, 14 October 2026 (after D3 commissioning):** once all sixteen nodes have been commissioned, wipe/reformat the SD cards installed in fleet nodes A1–D4, run basic write/read tests, verify capacity and report measured performance so the owner can replace broken, dead or slow cards. This is explicit fleet-wide erasure approval for that maintenance pass; do not ask again for each node. It excludes the LilyGo's management SD card and host disks. No erasure begins before D4 is commissioned. Identify each responding card and bind the operation to its node MAC and current card identity before destructive work; a changed card during an operation invalidates that operation. Record replacement cards and their own results separately.

The maintenance report must distinguish reported physical capacity, formatted filesystem capacity and the extent actually written/read back. A short test cannot certify full capacity: use a complete usable-volume write/read pass with address-dependent data to establish tested capacity, marking incomplete/interrupted passes explicitly. Capture bytes, durations, throughput and errors; do not equate successful formatting with media health, or infer remaining flash endurance from a basic test. Measure speed through the actual node interface and distinguish interface limits from suspected card faults. No-response cards remain undiagnosed until seating/reader/card substitution checks; do not automatically label them dead. First implement and validate the explicit maintenance operation; firmware 0.4.2 cannot format cards remotely.

Support the owner's 8, 16, 32 and 64 GB cards as test targets, with actual capacity recorded. Use one MBR FAT32 partition as the common format; 64 GB SDXC cards often arrive as exFAT and will need explicit conversion if incompatible. No requirement that all cards match. Initial firmware uses FAT32 and reports unsupported/unknown formats honestly; do not infer format from macOS's “FAT” label or card size.

Mount with automatic formatting disabled. Provide an explicit USB/authenticated Wi-Fi maintenance operation that first reports **node label, immutable board identity, current card CID/serial and capacity, and the entire-card destructive scope**. Execute only under explicit owner authorisation for that target (the fleet-wide approval above already covers this A1–D4 pass); recheck the same card before changing its partition table/filesystem. Stop normal logging/audio-file access and close/unmount before formatting; report progress, errors, remount and readback verification. The command must support an enumerated but unmountable card, not depend on an existing usable FAT volume.

Formatting may recreate the MBR/partition and FAT32 volume using supported FatFs/disk primitives; force the intended FAT32 layout rather than letting a default formatter silently select exFAT. Validate on a real representative 64 GB card. Separate filesystem reset from any later deletion of only Flockinator-owned data. **Formatting is not guaranteed forensic secure erasure** on flash media; no secure-wipe claim is made. A mount failure, boot, card swap or test retry can never authorize erasure. Power failure during requested formatting is reported and recoverable by an explicit retry; never claim atomic preservation of a deliberately reformatted card.

## Technical basis and project structure

Proposed framework: ESP-IDF 5.5.x, initially target 5.5.4 available in the host's PlatformIO packages, using the Waveshare 5.5.2 examples as attributed hardware references. Pin the working toolchain and component versions during implementation and save the lock. Do not change the working LilyGo Arduino toolchain. Use ESP-IDF audio codecs, SDMMC/FatFs, networking, NVS/OTA and the S3 HUB75 driver. Keep vendor checkouts untouched. Local builds/caches should live on the local Mac disk where appropriate, excluding SMB AppleDouble files.

`firmware/node-platform/`: embedded project, custom N32R16 board configuration, partition table, HAL adapters, diagnostic model, transport handlers and host-testable logic.

`tools/node-commissioner/`: uv-managed Python host CLI, serial discovery/protocol, provisioning transactions, report generation and tests.

`docs/inventory/`: human label register and history; `docs/validation/nodes/`: immutable per-run observations/manifests; private backups/credentials outside public evidence. `SPEC-node-platform.md` is the acceptance contract.

### Intended executable interfaces (not implemented yet)

From `/Volumes/devops/flockinator`; these commands describe the deliverable interface and are not commands to run against hardware now:

```sh
$HOME run --project-dir firmware/node-platform --environment waveshare-s3
$HOME test --project-dir firmware/node-platform --environment native
uv run --project tools/node-commissioner python -m pytest tools/node-commissioner/tests
uv run --project tools/node-commissioner python -m node_commissioner list
uv run --project tools/node-commissioner python -m node_commissioner provision --label A1 --port "$FLOCKINATOR_NODE_PORT"
uv run --project tools/node-commissioner python -m node_commissioner status --label A1
uv run --project tools/node-commissioner python -m node_commissioner test --label A1 --suite hardware
uv run --project tools/node-commissioner python -m node_commissioner accept --label A1 --check panel --result pass
```

The provision command must identify/verify its target and manage backup/flash/readback as one resumable operation; it does not erase any SD card. Format/update command syntax is to be specified in the reviewed implementation plan, with explicit target and authorization semantics above.

## Code style and testing

Small C++ adapters expose bounded snapshots; rendering, protocol, test scheduling and hardware reads are separated. Four-space indentation, explicit timeouts and fixed/bounded buffers. Model results use stable machine-readable test IDs; elapsed-time arithmetic tolerates wraparound. Python uses uv, type annotations and structured errors; JSON is versioned and CSV updates transactional.

```cpp
enum class CheckState { Pending, Pass, Fail, NotPresent, Unsupported, Stale };
struct CheckResult {
    CheckState state = CheckState::Pending;
    uint32_t observed_at_ms = 0;
    int32_t error_code = 0;
};
// Starting a driver does not certify an attached physical device.
```

Host tests cover duplicate identities/labels, reconnection and disconnect at each provisioning stage, malformed/oversized messages, redaction, inventory recovery, state freshness, absent peripherals, invalid update images and rejection of unauthorised/replayed/wrong-card destructive operations. Test relevant failure behaviour, not implementation mirrors. Build tests record resolved dependencies, partition fit and image digests; UI fixtures render actual font/layout paths for pixel-fit inspection. First-device acceptance measures real identities/peripherals, including cold-boot persistence and representative card compatibility. Test a 30-minute combined panel/sensor/network/audio soak with bounded logging and no unexplained reset or progressive resource loss. Repeat a shorter per-node run across all sixteen; retain manual results separately.

## Boundaries and success criteria

Always verify the target, cap brightness, preserve card contents unless explicitly authorised, record actual evidence and keep all sixteen independent. Ask for target clarification on ambiguity and for an explicit target-specific destructive request; routine identified-board provisioning is within this project's requested scope once the specification is approved. Never automatically erase on mount failure, burn eFuses, expose credentials, call untested optical/audio/radio behaviour a pass, or silently replace the LilyGo firmware.

This milestone is complete when: A1 completes the full prototype checks and host OTA gate; A1/A2 demonstrate real peer request/reply; the shared build and host procedure can provision remaining nodes without per-node source edits; each commissioned node retains identity and standalone diagnostics after restart/card replacement; owner can see pending vs passed checks and record manual acceptance; 8–64 GB FAT32 handling and explicitly requested remote formatting are tested on available representative cards; inventory and immutable reports match actual hardware. The physical act of connecting all sixteen remains incremental and user-paced, not a reason to fabricate unconnected node results.

## Owner workflow clarification — 13 October 2026

The owner will move each programmed controller into its panel and perform visual hardware checks there. **Do not require panel/speaker attachment or visual acceptance at the USB commissioning station, and do not hold the next node for those checks.** USB commissioning is the initial bootstrap and fallback procedure, not the normal experiment deployment path.

The station completion condition is: verify the owner-selected physical target; preserve original flash; install the common build; persist the chosen label, Wi-Fi configuration and per-node management credential; reboot; verify actual label/MAC/build and core health; atomically record inventory plus immutable evidence. Record `commissioned_for_installation` independently of pending panel, audio, card or peer acceptance. Missing detachable peripherals must not prevent this handoff. A1's existing Wi-Fi OTA recovery proof applies to the common software design, not to untested physical peripherals on other boards.

Load the existing private Wi-Fi file automatically as part of commissioning. Store credentials in device NVS, which meets automatic connection after installation without embedding credentials in shared source/release binaries. Credential provisioning is authorised by the owner's request and prior local credential entry. Future compatible experimental images must retain this configuration and management identity. Firmware builds remain common across all sixteen labels.

Add separately measured readiness fields: installed Wi-Fi OTA support, ESP-NOW receiver protocol support, authenticated console contact, and verified deployment round trip. ESP-NOW initialisation alone cannot set the deployment-ready field. An incompatible future experiment image must not be offered as preserving USB-free maintenance.

The owner offers a second USB-C connection for the LilyGo. Identify both devices independently before upload; this does not authorise flashing whichever port enumerates first. The live reporting and ESP-NOW receiver additions are specified separately below for review.

## Present evidence and remaining items

- A1 runs 0.3.2, has 32 MiB flash and 16 MiB runtime PSRAM, and retains label/credentials across two successful Wi-Fi updates and tested rollback. See `docs/validation/nodes/A1/20261013-bringup/README.md`.
- Wi-Fi credentials are provisioned. Actual A1 STA/ESP-NOW MAC is 00:11:22:33:44:55. The existing ESP-NOW code implements node probes only; image reception is not yet present.
- Build pins are recorded: PlatformIO PIOArduino 55.03.38, ESP-IDF 5.5.4 and dependency lock. Host/native tests passed 18/5 at the 0.3.2 checkpoint.
- Board PCB revision, physical panel/speaker behaviour and per-node card compatibility remain separately observed acceptance items, not station blockers.
- Full resumable station automation remains implementation work under the approved node-platform scope. Remote SD formatting remains separately requested and card-specific; no formatting is authorised by this clarification.

Sources: [Waveshare reference repo](https://github.com/waveshareteam/ESP32-S3-RGB-Matrix/tree/4047e4e7e13b043ae9ddd4daaeff5582de044c80), [ESP-IDF 5.5.2 FatFs](https://docs.espressif.com/projects/esp-idf/en/v5.5.2/esp32s3/api-reference/storage/fatfs.html), [ESP-IDF OTA](https://docs.espressif.com/projects/esp-idf/en/v5.5.2/esp32s3/api-reference/system/ota.html), [ESP-NOW](https://docs.espressif.com/projects/esp-idf/en/v5.5.2/esp32s3/api-reference/network/esp_now.html). The local 5.5.4 FatFs headers expose SD formatting and partition primitives; that is API availability, not demonstrated 64 GB card compatibility.


## World-view display extension — 16 October 2026

The owner authorised porting the approved browser World view and uploading it to
all sixteen ESP32s. Firmware 0.9.0 adds a local seeded-world renderer at the existing
8 FPS target, 25% brightness, unknown unprovided telemetry and synthetic peer cues.
The existing authenticated display-control endpoint accepts `display_world` with
bounded action/sensor strings; command contract and evidence are in
`docs/validation/world-deployment/README.md`. No new transport endpoint, credentials,
identity migration or SD format is involved. Previous mission/avatar/diagnostic
modes and OTA recovery remain. Deployment follows `tasks/world-deployment/plan.md`:
A1 measured canary, then identity-checked fleet rollout. This is presentation-only,
not inference, operational flight control or combat-decision functionality.
