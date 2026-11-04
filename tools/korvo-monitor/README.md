# Korvo fleet telemetry bridge

Polls the existing authenticated node status API and sends a compact projection
to the Korvo display over USB. Mission start/stop can be requested from the
touchscreen; no other node control or simulation endpoint is called. Credentials remain in host memory, resolved through the commissioner's
1Password provider. The Korvo contains no Wi-Fi or node management credentials.

From the repository root:

```sh
uv run --with pyserial python tools/korvo-monitor/bridge.py
```

Use `--port` to change the serial port, or `--seconds 30` for a bounded validation.
The bridge checks the Korvo's factory MAC before sending telemetry, and a local
file lock excludes another instance. Opening this USB port resets this board.
Do not run a competing serial monitor. Stop with Ctrl-C; no firmware changes are
made by the bridge. The screen requires this host process and USB connection.
It is not an autonomous Wi-Fi controller and does not start automatically on login.

The sixteen node MACs and reserved IPs come from `docs/inventory/nodes.csv` and
`network.csv`. Every status response must match both the expected MAC and label.
Polling repeats five seconds after the previous request completes, independently
per node. No-response means a failed network read, not proof that power is off.
Authentication, identity and credential errors are shown separately.

## USB protocol v1

A newline-terminated ASCII frame, at most 127 bytes:

```
F1 index state firmware uptime_seconds free_internal_KiB
```

`index` is 0–15 in A1…D4 order. `state` is 0 (no response), 1 (validated status),
or 2 (credential, server or validation error). Firmware is 1–16 ASCII letters,
digits, dots, underscores or hyphens. Counters are unsigned 32-bit integers.
No response/error frames use `- 0 0` for the last three fields. The receiver drops
malformed, oversized and NUL-containing lines without updating its timers.

Each node becomes STALE more than 20 seconds after its last accepted frame,
including error frames. Nodes with no frame since boot show WAITING. “LIVE” means
a fresh, identity-checked response, not that every sensor or peripheral passed.
Tap a tile for reported firmware, uptime, free RAM and reading age. Uptime is the
node's last reported value, not an extrapolated counter. No historical inventory
value is displayed as live telemetry.

USB is a trusted physical input: the bridge authenticates network requests, but
this small display protocol has no cryptographic signature. Only attach trusted
hosts. Mission start and stop are exposed on the display.

## Checks

```sh
uv run --with pyserial python -m unittest discover -s tools/korvo-monitor
cc -Wall -Wextra -Werror firmware/korvo-monitor/tests/protocol_test.c -o /tmp/korvo-protocol-test
/tmp/korvo-protocol-test
```

## Mission view and controls

The bridge also carries identity-checked scripted-world positions in `P2` frames (which include the node-reported scripted state)
and accepts bounded `MC1` requests from the physically connected Korvo. It sends
only supported mission start/stop commands; no image delivery or other maintenance
commands are exposed. A command pauses status polling until outstanding polls
finish, then dispatches to the fleet and returns verified/failed counts in `R1`.
Each node is read back after command acceptance, with a bounded retry for its
periodic status snapshot. Missing, mismatched, timed-out, or rejected nodes count
as failures; a timeout at the touchscreen means the final result is unknown.
The USB link is physically trusted and does not authenticate host/device frames.
The mission data is a scripted simulation, not physical tracking.
