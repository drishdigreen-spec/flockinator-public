# Firmware build & test evidence (summary)

This page summarizes the firmware iteration record. It exists because
this repository's public history is a squashed, allowlisted snapshot
of a private working project: per-release build bundles, flash logs,
and validation notes live in the private tree (they contain device
inventory) and cannot be browsed here. Every count below is quoted
from those private records with its source named; where a number
could be re-verified from this public tree, the command is given.
No device identities, addresses, or keys appear on this page.

## Panel-node firmware (ESP32-S3 ×16, `firmware/node-platform`)

Release bundles are kept per version (`firmware/node-platform/releases/`
in the private tree), each with build/validation notes. The bundles
were consolidated into the private baseline on 2026-11-04, so
directory timestamps reflect consolidation, not original build
dates; the chain below is ordered by version, not claimed dates.

| Version | Purpose (from bundle names/notes) |
|---|---|
| 0.2.0–0.4.2 bringup | Board bring-up iterations; 0.4.3 adds SD inspection |
| 0.5.0 / 0.5.1 SD maintenance | Authenticated SD maintenance over Wi-Fi/USB/ESP-NOW relay; all 16 nodes commissioned |
| 0.6.0 avatar · 0.7.0 random expressions | Display/personality layers |
| 0.8.0 / 0.8.1 recon HUD · 0.9.0 world view | Mission visualisation |
| 0.10.0 survey · 0.10.1 mission-world | Survey mission presentation (deployed mission line) |
| 0.10.2-journal | Mission-journal HTTP endpoints; hash-verified journal copies on node SD so journals survive controller outages |
| 0.11.0 / 0.11.1 / 0.12.0 Patternflow trials | Display-trial line (acoustic/pattern experiments), deployed fleet-wide as trials with authenticated rollback to 0.10.1 |

Negative-test bundles are kept alongside releases and are part of
the evidence, not clutter: `invalid-checksum-0.4.2`,
`invalid-checksum-canary-0.4.2`, `rollback-test-0.3.2`,
`rollback-test-0.4.2` — OTA rejection and two-slot rollback were
exercised with deliberately bad images before the mission line
depended on them.

Test evidence quoted from bundle validation notes:

- **0.5.1 validation:** 102 host tests + 14 node native (Unity)
  tests + 25 management-console native tests = **141**, plus shared
  wire assertions and an HMAC regression; both firmware builds
  succeeded; all 16 nodes reported the expected image and valid OTA
  state; all 16 SD cards passed FAT32 format/remount and a 16 MiB
  write/read comparison.
- **0.11.x trials:** 43 node native tests passed (suite grew from
  14 to 43 across the line); host renderer passed ASan/UBSan.
- **Current tree (re-countable here):** 11 Unity suites under
  `firmware/node-platform/test/`; 97 pytest functions under
  `tools/node-commissioner/tests/` in this public snapshot
  (107 in the private tree); 13 tests under
  `tools/mission-host/test_*.py` (13/13 passing in the private
  2026-11-05 run; needs pyserial).

## Korvo controller firmware (ESP32-S31, `firmware/korvo-monitor`)

ESP-IDF project; built on the lab host, flashed over serial with
esptool write-hash verification, previous binary staged before each
flash (single factory partition, so rollback = serial reflash of
the staged binary).

| Version | Binary (bytes) | What changed |
|---|---:|---|
| 0.7.0 | 1,480,448 | Monitor UI + speech events |
| 0.8.0 | 2,210,880 | Lab host: fleet sweep, web commander |
| 0.9.0 | 2,546,608 | Planner twin (board model), journals to SD |
| 0.9.1 | 2,550,576 · sha256 `b26c651c…8087649` | Connectivity watchdog + `/api/health` counters (2026-11-05) |

0.9.1 exists because of a field fault found the same day: the
controller repeatedly entered an "associated-but-deaf" Wi-Fi state
(associated, IP held, data path blackholed both ways, no disconnect
event; heap/brownout/panic/app-hang excluded from ~68k lines of
serial telemetry). The watchdog converts that unbounded outage into
a bounded one: 300 s of fleet-sweep silence → forced reconnect →
120 s grace → logged restart (≤3/hour). Field tally on 2026-11-05,
counted from serial-log watchdog lines cross-checked against
`/api/health` counters: **12 episodes, 11 cleared at the reconnect
tier (~303–329 s silence, service back in ~2 s), 1 ended by operator
reboot; the restart tier has never fired** (a named design gap: any
single panel success clears escalation — residual R9 in
[`docs/results/README.md`](results/README.md)). The wedge trigger
remains unknown; the firmware contains no hard-coded SSID, password,
IP, or BSSID (verified in source and in the shipped binary's
strings; provisioning is NVS + DHCP).

## Commands (as recorded in the private build notes)

```sh
# Panel nodes — build + native Unity suites (PlatformIO)
pio run  --project-dir firmware/node-platform --environment waveshare-s3
pio test --project-dir firmware/node-platform --environment native

# Commissioner / host tooling tests
uv run --project tools/node-commissioner python -m pytest tools/node-commissioner/tests -q
uv run --project tools/mission-host python -m pytest tools/mission-host -q

# Korvo controller (ESP-IDF)
idf.py build        # firmware/korvo-monitor; flash via esptool with hash verify
```

## Honest limits of this summary

- Counts dated to their bundle notes; suites have grown since
  (native 14 → 43; commissioner 102 → 107 test functions private,
  97 in this snapshot). Current
  counts above were re-counted from the trees, not re-run end-to-end
  for this page, except where a 2026-11-05 pass is stated.
- Firmware builds are **not bit-reproducible** (embedded timestamps;
  some early builds predate clean-tree discipline). Deployed-source
  provenance is recorded per bundle, but a judge cannot rebuild a
  bit-identical 0.9.1 from source today; the sha256 above identifies
  the exact binary that was flashed and soaked.
- Which exact build each physical node runs today lives in the
  private inventory, not here.
