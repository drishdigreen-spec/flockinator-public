# Flock network: live commissioning link

Status: **approved by owner**, 13 October 2026 ("proceed you have my approval"). This scopes the existing `flock-network` module to node health and maintenance discovery; inference/experiment traffic remains future work.

## Objective

Each installed, provisioned node reports genuine identity, health and update capabilities to the handheld LilyGo without a host remaining connected. The host's job is initial/fallback flashing, identity and credential provisioning, and inventory. The handheld's absence must not stop diagnostics or experiments.

## Architecture clarification — 13 October 2026

### Owner clarification — 14 October 2026

Management must remain local to the display and independent of remote experiment/GPU hosts. The owner has ordered ESP32-P4+C6 PoE hardware, but it is not available yet; continue on the existing Waveshare nodes, LilyGo and host tools. Migration is optional and requires a demonstrated benefit. Proposed future gateways must preserve node identities, authenticated control, local firmware staging, health and recovery. Heavy inference remains an external service; its failure or overload must not remove management access. No P4 capability or combined camera/radio workload is accepted merely from a product description. The next implementation remains the already approved node SD maintenance pass, not an unrequested migration.

The handheld is one authorised management endpoint. Nodes may also report to an external server for web management/logging and exchange observations/actions directly with remote brains. This first link remains the LilyGo health proof; it must not make the console a mandatory broker, sole log sink or holder of all experiment state. See `docs/design/embodied-experiment-platform.md`.

Separate management health polling from low-latency observation/action streams and bulk transfers. The 250-byte frame limit and five-second polls below apply to this commissioning protocol, not to every experiment transport. Future Wi-Fi/USB/BLE/acoustic adapters require their own capability advertisement, measurements and interface review. Define observation timestamps, action deadlines/session ownership and disconnected behaviour in the future body/brain contract. Multiple controller arbitration is an explicit future requirement; do not accidentally permit simultaneous conflicting writers.

## Assumptions and interface

- Both device types use their already validated toolchains: node ESP-IDF 5.5.4, console Arduino 2.0.17. Do not migrate the e-paper driver to achieve networking.
- Provision the same private Wi-Fi settings to both over identified USB connections. Initial integration uses one 2.4 GHz AP/channel. Credentials persist in NVS and are excluded from source/release images/reports.
- Carry commissioning discovery, authenticated health and acknowledgements over ESP-NOW so the transport used for future image transfer is exercised. Wi-Fi association synchronises the initial channel and retains the existing host OTA fallback.
- Begin with A1 and the console. Sixteen node records fit in a fixed table, with no dynamic allocation in receive callbacks. The console has its own role and identity, not a fictitious A1–D4 label.
- Load the console's authorised label/MAC roster and per-node keys privately over USB from the host inventory. Never derive authority from a broadcast label/MAC or share one fleet-wide signing key. Key rotation is outside this first scope.

Version 1 messages are explicitly encoded bytes, with exact length validation and no compiler-dependent struct layout. Maximum **250 bytes including authentication** for compatibility with the older console stack. Header includes protocol version, message kind, sender/recipient identities and freshness context; HMAC-SHA256 covers header and body. Discovery can be unsigned but cannot create a trusted health observation or authorise control.

The console polls each registered node with a fresh random challenge. A node's authenticated reply binds that challenge, its boot session and sequence; repeated, expired or wrong-target replies cannot refresh health. Polling and replies provide periodic live reports without needing a static console IP address. Status includes label, actual MAC, application version and digest, boot count, uptime, reset cause, core health, per-peripheral PASS/FAIL/PENDING flags, Wi-Fi/channel information, and update-receiver capability/version. Extended data may use separate bounded messages rather than exceeding the frame limit.

Target cadence is one health exchange per node every five seconds, staggered across the sixteen records. After 30 seconds without an authenticated observation show STALE; after 90 seconds show OFFLINE. Unseen nodes remain UNKNOWN. Use receipt time, not an untrusted remote wall clock, for freshness. A duplicate label or unexpected MAC is a conflict, never a replacement.

Radio callbacks validate framing and enqueue bounded work only. Network processing remains independent of e-paper refresh. Queue overflow, retransmission exhaustion and channel loss are observable. Wi-Fi reconnect uses bounded backoff without blocking local hardware diagnostics. Report channel changes explicitly and re-establish fresh sessions after reconnect.

AP-free conference operation is a subsequent configuration mode, not inferred from this first same-AP proof. Do not silently switch an associated node to another radio channel. The transport must leave room for an explicit shared fallback-channel policy later.

## Readiness semantics

Keep these separate: `wifi_ota_supported`, `espnow_receiver_supported`, `console_link_verified`, and `espnow_deployment_verified` (bound to build/receiver protocol and evidence). A healthy radio or acknowledged health packet does not prove image reception. The pre-integration 0.3.2 node had Wi-Fi OTA and node probes only. Node 0.4.2 now has an authenticated receiver and real A1 deployment evidence; per-node/build readiness must still be established rather than inferred from radio startup.

## Structure, style and commands

Shared wire codec and native tests: `firmware/shared/commissioning/`. Node adapter: `firmware/node-platform/src/`; console adapter: `firmware/management-console/src/`. Host private roster provisioning: `tools/node-commissioner/`. Evidence: `docs/validation/commissioning-link/`.

Use bounded records, explicit lengths, four-space indentation, and wrap-safe elapsed-time arithmetic. Hardware adapters own radio calls; UI consumes immutable snapshots. Example acceptance rule:

```cpp
bool may_refresh_health(const Reply& reply, const PendingPoll& poll) {
    return reply.authenticated && reply.target_matches &&
           reply.challenge == poll.challenge && !poll.consumed;
}
```

From `/Volumes/devops/flockinator`:

```sh
$HOME run --project-dir firmware/node-platform --environment waveshare-s3
$HOME run --project-dir firmware/management-console --environment lilygo-s3
$HOME test --project-dir firmware/node-platform --environment native
$HOME test --project-dir firmware/management-console --environment native
uv run --project tools/node-commissioner python -m pytest tools/node-commissioner/tests -q
```

## Tests and success criteria

Native tests cover wire golden vectors shared across both toolchains, truncation/oversize, HMAC failure, replay, wrong target, duplicate labels, boot/session changes, ageing and timer wraparound. Host tests cover private roster provisioning, exact device selection with both USB devices present, and credential redaction.

Real A1 and LilyGo must establish authenticated bidirectional contact on their actual toolchains. The live console displays A1's measured version/health; unplugging A1 produces stale/offline transitions and reconnect restores current data. Console restart/sleep/wake must not turn retained observations into fresh ones. A deliberately replayed health reply must not refresh status. Capture a continuous ten-minute radio/UI test with no unexplained reset or unbounded heap decline. Fleet scaling requires sixteen real records over time; simulated fixtures remain labelled tests.

## Boundaries

- Always: preserve existing Wi-Fi OTA fallback, identity, SD contents and console touch/display behaviour; record real evidence; keep callbacks short.
- Ask first: destructive card changes, new required infrastructure or deliberate key replacement. Routine uploads to the two verified devices and private credential provisioning are within the requested integration scope after this specification is approved.
- Never: embed passwords in shared firmware, present demo data as live, equate send-callback success with application delivery, or allow inference trust scores to grant maintenance authority.

Sources: [Espressif ESP-NOW 4.4.7](https://docs.espressif.com/projects/esp-idf/en/v4.4.7/esp32s3/api-reference/network/esp_now.html) specifies 250-byte payloads, same-channel peers and application acknowledgements; the current repository provides the node/console hardware basis. Timing and authentication above are Flockinator design choices to validate.

### Scripted presentation management extension (2026-10-16)

The deployed HUD launcher uses authenticated FLK2 kinds 12/13 for mission
presentation start/stop, with a consumed fresh node challenge and duplicate
acceptance cache. Health may extend to 128 bytes while legacy 96-byte reports
remain readable. Exact fields are in SPEC-management-console.md and
`firmware/shared/recon/model.h`. This management traffic is distinct from the
scripted TX/RX pixels: experimental peer-report messaging is still future work.

Overview summary extension (2026-10-16): health bytes 116/117 now carry schema 1
and the five-state node-authoritative summary defined in SPEC-management-console.
Payload remains 128 bytes; old receivers ignore the reserved extension. A new
receiver rejects unknown summary versions/values for Overview without discarding
otherwise valid diagnostic telemetry. Polls are paced at 125 ms across 16 nodes.
