# Shared fictional survey

This is a host-coordinated exhibition model with invented world units and energy
points. It is not an aircraft battery model or distributed inference system.
The physical nodes render snapshots; they do not decide survey actions locally.

From the project root (see [current baseline](../../docs/development.md)):

```sh
node tools/survey-simulator/server.mjs --host 127.0.0.1 --port 8767
```

Open <http://127.0.0.1:8767/>. Select nodes and a site, then **Launch selected**.
Unselected nodes stay home. Survey completion or the fixed game reserve rule
returns a node to its own home. Return selected is an explicit early return.
Nodes land, charge and remain READY until selected again. Reset requires an
explicit browser confirmation. Export the replay before resetting.

The top-right three digits are distance to the current destination in invented
world units, capped at 999 (full value in browser details); D-- means none. E000
through E100 is fictional energy, not measured panel power or a real battery.
OK / LOW / RTN describes the game reserve rule. STALE means snapshot delivery
has stopped; the panel freezes rather than inventing continued movement.

The engine uses 100 ms ticks and the client/bridge polls at up to 2 Hz. Displays
render at their existing 8 FPS target, with bounded pose interpolation. Peer cues
come from actual simulated peers; the firmware receives at most three stable-ID
peers per snapshot, while the browser can consider all fifteen with a three-label
limit. TV/NV/WH/BH/IR are cosmetic palettes. The firmware currently retains its
selected local palette; browser palette selection affects the browser only.

## Physical bridge (explicit selection; firmware 0.10.0 or 0.10.1)

```sh
uv run --project tools/node-commissioner python tools/survey-simulator/bridge.py \
  --take-control --labels A1 A2 A3 A4 B1 B2 B3 B4 C1 C2 C3 C4 D1 D2 D3 D4 \
  --report /tmp/flock-survey-bridge.json
```

Run only one bridge for a given node. It checks the inventory's MAC and label,
requires a supported firmware version, and reads existing management credentials from 1Password into memory. Never run OTA
concurrently with a bridge for the same node. Stop that bridge before maintenance.
The report includes last successful delivery and periodic authenticated health.
No credentials are written to the report or served to the browser.

Keep both processes running on the selected host. They are not installed as login/reboot
services. If the host sleeps, exits or loses the link, nodes become STALE. Restart
of a node boots the existing local demo until fresh host snapshots arrive. The
host restarts a new session; only the monotonically increasing session ID is
persisted at `~/.local/share/flockinator/survey-session.json`. Browser reloads
preserve the existing host session. The 8766 preview remains independent.

LilyGo still runs its existing mission interface; it does not control this survey
session. The bridge yields permanently when it observes another display mode or controlling run.
Stop it before using legacy mission controls: firmware-enforced ownership is still pending. Use the new browser controls
for this mode until the handheld adapter is implemented.

## Replay and validation

```sh
node tools/survey-simulator/replay.mjs --input run.json --verify
node --test validation/survey-simulator/*.test.mjs validation/recon-hud/*.test.mjs
node validation/survey-simulator/browser-check.cjs
```

Replay version is `survey-2` (scenario version 1). Replay verifies accepted
commands, transition events and final state, including paused intervals.
Earlier development `survey-1` records are incompatible and rejected.
Browser tests operate the local test session, so do not run them during a live
presentation. Use `npm run test:browser` for portable checks against disposable services.

Limits: 32 recently used browser command clients per process, 128 cached command
results per client, 20,000 accepted commands, roughly 20,000 transitions and ten
hours of unpaused simulation per session. Rejected/evicted commands cannot be
reapplied with an old sequence. Session limit pauses the run for export/reset.
There is no cross-device clock synchronization, AI agent, observational classifier,
real sensor model, WLED integration or automatic task redistribution in this slice.

Browser registration resumes a tab token after reload. Least-recently-used clients
are evicted when necessary; IDs are never reused, so evicted envelopes are rejected.
Each new user command re-registers before submission. Failed commands are not
automatically retried. See the development guide for bridge ownership limitations.
