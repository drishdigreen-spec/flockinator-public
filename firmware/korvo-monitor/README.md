# Korvo monitor bring-up

ESP32-S31 Korvo touchscreen fleet monitor and standalone web host, version 0.9.0. Shows a square
4×4 physical panel overview with row/column coordinates, status counts and a
selected-panel inspector. Tap a panel for firmware, reported uptime, free RAM and
reading age. The selected panel has a white outline; colours always have text labels. The provisioned controller hosts the web interface, learning lab, tabletop planner,
scripted fleet controls and SD exercise archives. Drishdi only needs a browser.
The USB bridge described in [bridge instructions](../../tools/korvo-monitor/README.md)
is retained for recovery to older firmware. The owner confirmed the original 0.1.0
display and touch test worked before this fleet-monitor update.

## Standalone operation — 0.9.0

Open the address shown on the controller's Learning lab screen. At deployment it
is [http://192.168.1.10/](http://192.168.1.10/). Fleet missions are at `/`, the
tabletop editor at `/planner`, and the communication experiment at `/lab`.
Fleet and planner writes ask for the six-digit operator PIN shown on the Korvo.
The PIN changes after reboot. Scripted starts have a one-minute countdown to
allow all sixteen authenticated commands and their readbacks to complete.

The Korvo owns the simulation clocks and world state. Closing every browser does
not stop a run. Mission settings and the planner persist in NVS. The learning
experiment checkpoints every eight rounds and reconstructs its seeded memory on
restart. Network time restores absolute mission timing after reboot. When network
time is unavailable, an authenticated web action can set the clock from the
browser. ESP-IDF's [SNTP service](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/network/esp_netif_programming.html)
starts after the station acquires its address.

Planner archives live under `/sdcard/flockinator/runs`. Each contains sixteen or
fewer unit JSONL journals plus separate director truth, with ZIP download from the
editor. Delivery to physical panels is asynchronous. A receipt appears only after
the Korvo reads the panel's SD copy back and compares every byte. Health polling
gets a complete sweep between deliveries. The migrated historical archive retains
its previously verified receipts.

The sixteen management keys were provisioned over the MAC-verified USB connection
with the owner's explicit approval. They reside in the controller's NVS, never in
the firmware image or browser assets. They retain maintenance privileges. Do not
run the old desktop poller or USB bridge concurrently with standalone control,
because the panel authentication challenges are shared.

These remain simulated agents and board-game energy units. The learning lab runs
on the Korvo; panel journal receipts prove storage, not learning on each panel.
Training larger external models and compiling replacement firmware still require
a development computer. The existing physical panel firmware remains
`0.10.2-journal`.

The previous desktop plan and archives are retained on Vivek. The original plan
was copied to the controller as a draft ready to rehearse. The 0.8.0 recovery image
is retained on Drishdi in `~/.local/share/flockinator/korvo-release/0.8.0.bin`.
Recovery must flash only the application at `0x10000`, preserving NVS and SD data.
Re-enable the old LaunchAgents only after restoring the older firmware.

For USB roster provisioning, use
`tools/korvo-monitor/provision_fleet.py --port /dev/cu.usbserial-210` on the USB
host. Supply all sixteen identity-bound records through stdin. Never place keys
on the command line. Its output includes the operator PIN and must be redirected
to a private file. An empty JSON array retrieves the current PIN without changing
credentials.

The portable model checks run from the repository root.

```sh
c++ -std=c++17 -Wall -Wextra -Werror firmware/korvo-monitor/tests/lab_model_test.cpp firmware/korvo-monitor/main/lab_model.cpp -o /tmp/korvo-lab-test
/tmp/korvo-lab-test
cc -c firmware/korvo-monitor/main/vendor/blake2s-ref.c -o /tmp/korvo-blake.o
c++ -std=c++17 -fsanitize=address,undefined -g -I firmware/korvo-monitor/main firmware/korvo-monitor/tests/board_model_parity.cpp firmware/korvo-monitor/main/board_model.cpp firmware/korvo-monitor/main/lab_model.cpp /tmp/korvo-blake.o -o /tmp/korvo-board-parity
uv run firmware/korvo-monitor/tests/compare_boards.py /tmp/korvo-board-parity
```

Hardware identified over USB on 30 October 2026: MAC `00:11:22:33:44:55`, 16 MiB
flash, 16 MiB PSRAM, 800 × 480 RGB display, GT1151-family touch controller.
The owner authorized removing the factory demo; all flash was erased and its digest
verified against 16 MiB of `0xff` before this application was prepared.

## Build

This target requires ESP-IDF 6.1, not the existing S3 PlatformIO environments.
Upstream sources used:

- ESP-IDF release/v6.1: `9a97f6c54ec638111ce55cd36581b3c192f15207`
- esp-dev-kits: `bd4d4ac18657e73583af3d7c0b0a23c3cddf3735`

The unmodified Korvo BSP comes from the pinned esp-dev-kits checkout. Its component
manifest resolves display, touch and other board dependencies. Camera and audio
are not started by this application.

```sh
export IDF_PYTHON_ENV_PATH="$HOME/.espressif/python_env/idf6.1_py3.12_env"
source "$HOME/esp/esp-idf-s31/export.sh"
export KORVO_SDK_PATH="$HOME/esp/esp-dev-kits-s31"
idf.py --preview build
idf.py --preview -p /dev/cu.usbserial-20130 flash
idf.py --preview -p /dev/cu.usbserial-20130 monitor
```

Run from this directory. For a new machine, check out the pinned sources and use
`uv run --python 3.12 tools/idf_tools.py install --targets esp32s31` and
`uv run --python 3.12 tools/idf_tools.py install-python-env` inside ESP-IDF.
The latter manages ESP-IDF's own runtime. CMake and Ninja must also be available.

## Acceptance

Build, flash and observe a stable heartbeat without resets. On the physical screen,
confirm readable text, increasing uptime, and a touch counter that increments once
per tap. Serial startup alone cannot verify visible rendering or touch accuracy.

Fleet telemetry uses authenticated host status reads and a bounded USB protocol.
Readings expire after 20 seconds; LIVE denotes a fresh response, not all-hardware health.

### Network-mounted workspace

For this SMB workspace, use a local build copy to avoid slow metadata operations:

```sh
mkdir -p "$HOME/.cache/flockinator-korvo/source"
rsync -a --exclude build --exclude '._*' ./ "$HOME/.cache/flockinator-korvo/source/"
cd "$HOME/.cache/flockinator-korvo/source"
idf.py --preview build
idf.py --preview -p /dev/cu.usbserial-20130 flash
```

Keep source edits in the repository and repeat the sync before each build. Sync the
resolved `dependencies.lock` back if dependency resolution changes it. Build artifacts
remain in the local cache; the repository is the source of truth.

## Verified on 30 October 2026

Built successfully with the pinned SDK and flashed the attached MAC
`00:11:22:33:44:55`; esptool verified the written data hash. The captured
[boot log](validation/boot-2026-10-30.log) identifies application 0.1.0, passes the
PSRAM memory test, initializes display and touch, and reaches 20 seconds uptime
without a reset during the 25-second capture. Free internal RAM remained 254 KiB,
free PSRAM 13396 KiB. The touch callback reported 26 events; event count alone does
not prove one event per physical tap or visual correctness. Those checks remain
for the operator. Fleet connectivity is not yet implemented.

## Fleet monitor 0.2.0 validation

The screen and touchscreen were physically accepted by the owner on 30 October.
The subsequent fleet build compiled and flashed with a matching readback hash.
A bounded live bridge run returned identity-checked status from all sixteen nodes,
all on firmware 0.10.1; see [poll evidence](validation/fleet-2026-10-30.log).
The native protocol test covers malformed/range-invalid frames and the 20-second
staleness boundary. Python tests cover identity mismatch, malformed status,
authentication failure, network timeout and long uptimes. Visual acceptance of the
new tile layout and a physical disconnect/stale test remain operator checks.

The older 0.1.0 log above is retained as historical bring-up evidence; its final
statement about missing fleet integration describes that older version only.
The ongoing bridge also captured the Korvo's receipt acknowledgements for all
sixteen live node frames, confirming the USB data reached the firmware parser;
see [USB receipt evidence](validation/usb-received-2026-10-30.log).


## Physical overview 0.3.0

The map uses the inventory layout: row A at the top through D at the bottom,
column 1 at the left through 4 at the right. It represents panel arrangement,
not mission-space positions or inferred movement. Each panel has a 76×76 touch
target. The right inspector updates immediately on selection and once per second
for freshness. Header counts separate LIVE, NO REPLY, ERROR, STALE and WAITING.
No simulated mission data or control actions were added.

The 0.3.0 build and flash readback hash passed. The on-device LVGL check reports
`overview_layout=PASS`, with all tile state labels at most 66 pixels wide inside
76-pixel tiles. See [boot evidence](validation/overview-0.3.0-boot.log).
The tile uses the shorter `NO DATA` caption for a failed poll; the header and
inspector retain the more explicit no-response wording. Protocol and bridge
regression tests pass. These checks do not replace visual acceptance of the new
layout or confirmation of the physical orientation by the owner.
After restoring the bridge, the new firmware acknowledged live updates for all
sixteen nodes; [fleet receipt evidence](validation/overview-0.3.0-fleet.log).


## Speaker and controls — 0.4.0

Touch remains the primary interface. Open **Controls** at the bottom right for
volume up/down, mute, test sound, screen sleep and Back to fleet. Tapping a panel
plays a brief tone; normal telemetry updates remain silent. Speaker playback runs
on a separate task, and rapid taps coalesce rather than queue a delayed sequence.
Tones have a 50 ms fade envelope. The microphone is not opened.

| Board button | Shortcut |
| --- | --- |
| VOLUP | Raise volume 5 percentage points and unmute |
| VOLDOWN | Lower volume 5 percentage points and unmute |
| MODE | Sleep/wake the screen |
| SET | Home: wake, close Controls, select A1 |

Volume is bounded to 0–100%; startup is 50%, with a short confirmation tone.
Volume and mute are session settings and reset on reboot. Mute silences all UI
tones, including Test sound until unmuted. Screen sleep uses a black overlay;
the BSP has no backlight-control GPIO, so this is not a power-saving display-off
mode. Touch anywhere on the blank screen to wake; monitoring continues underneath.

The BSP uses its software-calibrated ADC ladder for the four hardware buttons.
Registration success does not prove the physical mapping; press each labelled
button to confirm. Audio initialization/write success does not prove audibility;
use Controls > Test sound to check the attached speaker.

Control tests:

```sh
cc -Wall -Wextra -Werror firmware/korvo-monitor/tests/controls_test.c -o /tmp/korvo-controls-test
/tmp/korvo-controls-test
```

The onboard WS2812 and light guide show fleet response status at low brightness:
steady green when all 16 reports are fresh, amber while any are waiting or stale,
and red when any latest poll has no response or a validation error. The LED is a
summary of telemetry freshness, not proof of complete hardware health. It stays
active when the screen is blanked. Physical colour and brightness need visual
confirmation through the light guide.

## Mission view 0.5.1

Tap **Missions** to show a north-up scripted-world map and mission parameters.
Tap Scenario, Goal, Duration and Repeat to cycle the supported choices, then
START or STOP. Back to fleet and the hardware Home button return to the physical
layout. Positions come from each node's identity-checked `panel.world` report,
not the physical panel layout. Reports outside the map extent or older than 20
seconds are hidden. Only `scripted_mission_shared_world` reports are displayed.

The Mac USB bridge sends authenticated commands to the sixteen nodes, pauses its
polls during dispatch, and checks each node's mission run and state afterwards.
The screen reports verified and failed counts. A timeout is an unknown result;
check the fleet before retrying. Nodes respond independently, and the 3-second
start delay is best-effort rather than a guarantee of simultaneous launch. Mission
controls alter the scripted presentation; the separate survey bridge is not started.

On 30 October 2026, a direct bridge-dispatch hardware test verified STOP on all
16 nodes followed by START on all 16. A first attempt showed that immediate
status reads can predate an accepted command, so the dispatcher now retries
readback for up to eight seconds. The running mission uses the Mixed outcomes /
Observe / 64 seconds / repeat parameters. Firmware 0.5.0 built, flash verification
passed, and all 16 nodes supplied scripted-world position frames. The owner confirmed the mission map is visible and its moving designations update.
Touchscreen START and STOP requests were each verified on all 16 nodes;
[control evidence](validation/mission-0.5.1-touch.log).

Version 0.5.1 fixes the Missions button being drawn above the mission screen.

Version 0.5.1 fixes the Missions button being drawn above the mission screen;
the owner confirmed the button no longer overlaps and the screen stays open.


## Scripted mission cues — 0.6.0

The map now colours node labels using their identity-checked reported mission
state: SHARE blinks green, ENGAGE/KILL are red, FRIEND is blue, SEEN/TARGET are
amber and LOST/NOLINK/CRASH are muted red. These are scripted states, not verified
radio traffic, target classifications or real-world events. The map legend gives
the key. Status arrives about every five seconds, so short states can be missed.

Short, distinct tone frequencies accompany observed transitions into TAKEOFF,
SEEN, FRIEND, TARGET, ENGAGE, ASSIGN, SHARE, R2B, CRASH and KILL. Cues are
rate-limited to one every three seconds across the fleet, are suppressed while
muted or the screen is asleep, and are not played on first contact or after a
stale gap. They use the existing volume setting. UI click tones remain separate.

The existing node status does not provide target, friend, foe or waypoint world
coordinates. No such map markers are fabricated. Adding them requires a source
that reports their coordinates and provenance. The browser preview's fixed report
markers are explicitly illustrative and are not node observations.

On 30 October 2026 the firmware build and flash verification passed, and the
bridge supplied state-bearing frames for all 16 nodes. The board logged a
successful 940 Hz event tone; see [event evidence](validation/mission-0.6.0-events.log).
Physical colour and audibility still require user confirmation.

## SD-card speech — 0.7.0

The onboard card is mounted at `/sdcard` using the Korvo BSP with formatting
explicitly disabled. Default spoken samples are generated locally with macOS
`Karen` (Australian English) at 175 words per minute, then attenuated to 20% and
converted to raw signed 16-bit little-endian, mono 16 kHz PCM. On first boot the
firmware copies missing defaults into `/sdcard/flockinator/audio/` using exclusive
staging files and rename. Existing samples and existing staging files are not
overwritten. A failed copy is removed only if this boot created its staging file.
The firmware reads samples in short chunks, converts them to the codec's 48 kHz
stereo format, and runs playback on its existing audio task. The queue coalesces
rapid events and allows mute or a newer cue to interrupt a sample.

| Scripted state | File | Spoken phrase |
| --- | --- | --- |
| TAKEOFF | takeoff.pcm | Taking off |
| SEEN | seen.pcm | Contact spotted |
| FRIEND | friend.pcm | Friendly identified |
| TARGET | target.pcm | Target designated |
| ENGAGE | engage.pcm | Target lock |
| ASSIGN | assign.pcm | Roles assigned |
| SHARE | share.pcm | Sharing update |
| R2B | rtb.pcm | Returning to base |
| CRASH | crash.pcm | Aircraft down |
| KILL | kill.pcm | Impact confirmed |

These are cues for scripted states, not factual declarations about a real target.
No “enemy located”, “bingo fuel” or waypoint speech is generated without a
corresponding reported state. Existing three-second event rate limiting, stale-gap
suppression, mute, screen-sleep silence and volume controls apply. `Controls >
Test sound` plays `seen.pcm`; an absent, unreadable or invalid sample falls back
to the prior tone. A sample must be 16 kHz mono signed 16-bit little-endian raw
PCM, even-sized and no longer than three seconds. To change a voice, power down,
edit the card in a card reader and replace the desired file. Firmware will keep
an existing file instead of overwriting it. Volume resets to 50% on restart.

The app partition is expanded to 4 MiB; NVS and PHY offsets are unchanged. This
is still a single factory app, not an OTA layout. The source PCM files are also
embedded for first-boot seeding; playback reads the card. On 30 October the card
mounted successfully and the board logged successful `rtb` and `takeoff` speech
reads; the owner confirmed that spoken samples play. The startup 50% volume was
confirmed in the reboot log. Flash verification, build and bridge regression tests passed.

## Controller-hosted learning lab · 0.8.0

The Korvo serves its communication lab directly over Wi-Fi. Open the address on
the small screen from Drishdi or choose **Open Korvo lab** on the existing
mission-control home page. The lab screen shows the seed, progress, comparative
recoveries and the latest sixteen unit outcomes. **Fleet overview** opens the
existing USB-backed fleet display; **Learning lab** returns to local results.

The embedded web page controls the seed, channel intervention, start, pause,
resume and held-out replay. The controller generates the private cues, trains
the sixteen listener memories in both conditions, freezes them and scores
32 matched test rounds. A hardware task advances one round per half second.
Only completed test rounds are exposed. Browsers render snapshots and can
disconnect or join mid-run. Starting a new experiment replaces the current
controller replay. Settings and pause/resume are saved immediately; during
normal progression the controller saves a checkpoint every eight rounds and
reconstructs the same seeded world after reboot.

The web service runs on the private LAN on port 80. Same-origin browsers on that
LAN can control this experiment. The USB provisioning tool checks the factory
MAC before sending Wi-Fi details over the physical link; the firmware stores
them in its NVS. No panel management keys are required. **Planner**, the
planner’s mission-request counterfactual, physical scripted mission dispatch,
and historical per-panel journal delivery continue to run on Vivek.

Build with the pinned ESP-IDF/board SDK above and the existing 4 MiB app
partition. Back up and verify the identified previous application before
writing the factory application at 0x10000. Provision with
`tools/korvo-monitor/provision_lab_wifi.py --port PORT` on the USB host,
supplying the private Wi-Fi JSON via stdin. Stop the USB prop bridge while
provisioning; restore it for live fleet telemetry afterward. The controller
reports its DHCP address on the LCD and over USB.

Native reference check from the repository root:

```sh
c++ -std=c++17 -Wall -Wextra -Werror firmware/korvo-monitor/tests/lab_model_test.cpp firmware/korvo-monitor/main/lab_model.cpp -o /tmp/korvo-lab-test
/tmp/korvo-lab-test
```
