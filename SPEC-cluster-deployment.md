# Cluster deployment: flexible sources, initial LilyGo ESP-NOW path

Status: **approved by owner**, 13 October 2026 ("proceed you have my approval"). Depends on the authenticated commissioning link in `SPEC-flock-network.md` and the working node-platform OTA slots. Initial proof is A1, then sequential deployment to the fleet.

## Objective and scope

The LilyGo streams externally compiled application images from its SD card to a selected node's inactive flash slot. It verifies activation through the node's post-boot identity and digest. The USB station remains initial bootstrap/recovery; existing authenticated Wi-Fi OTA remains an additional fallback. This is application-level image delivery, not ROM/PXE boot.

Every compatible experimental build must include the maintained management/update receiver and first-boot validation. Two slots alone do not recover a running application that refuses management; arbitrary third-party images cannot be advertised as preserving wireless recovery. A protected recovery application/physical entry design would be a separate future requirement.

## Architecture clarification — 13 October 2026

LilyGo SD-backed deployment remains a required portable capability, alongside host Wi-Fi OTA for development and other authorised external deployment sources. Transfer source, transport, image storage and activation are distinct concerns. Keep one validated node installation/rollback path reusable by these adapters. Deployment is exclusive per node; future managers must coordinate ownership rather than race two image writers.

Optional later node-SD staging: retain media, data, logs and cached application images locally. A complete authenticated, compatible image may be staged as a verified file, then explicitly copied into inactive internal flash using the existing OTA path. Revalidate at installation; card swap/truncation/stale content must not select a bad image. Receiving or discovering a file does not authorise installation. SD is not required for the initial direct transfer path and a staged image is not executed from SD.

Select experiment configurations, remote brain assignments and assets without reflashing when supported. Persistent SD/NVS schemas require compatibility rules: application rollback does not restore externally modified data. The first proof below remains two real LilyGo ESP-NOW updates; adding storage/transport possibilities does not claim them implemented. See `docs/design/embodied-experiment-platform.md`.

## Transfer contract

- Common wire codec and maximum 250-byte frame envelope from flock-network. Reuse per-node authority through domain-separated session authentication; experiment messages never authorise updates.
- Establish a fresh authenticated session bound to console/node identities, nonce, image digest and protocol version. A manifest names hardware target, application/project identity, image length, digest and required management protocol. Reject incompatible or oversized images before erase/write.
- First implementation transfers to **one node at a time**, reading bounded chunks from SD. Start with 128-byte image chunks to leave envelope/authentication headroom. No whole-image RAM allocation, fleet multicast, delta compression or cross-reboot partial resume is required.
- BEGIN validates prerequisites and selects only the inactive application slot. DATA carries session ID, sequence and offset. Acknowledgements reflect validated data written to the intended offset, not a radio send callback. Duplicate chunks are acknowledged idempotently; changed duplicates, gaps and unexpected offsets reject. Bound retries and timeouts, and expose their reason to the UI.
- COMMIT requires exact length, streaming SHA-256 match and ESP-IDF image validation before changing boot selection. Abort/disconnect/timeouts leave the previous application bootable. Retrying an interrupted transfer starts a new authenticated session and overwrites only the inactive candidate.
- During transfer suspend conflicting peripheral polling if required, retain sensible static diagnostics and never treat a receive timeout as permission to reboot into an incomplete image.
- New firmware marks itself valid only after the reviewed core-health checks. Peripheral absence does not force rollback. On a failed first boot, existing bootloader rollback restores the prior valid image.
- Completion requires an authenticated post-boot report with the expected label, factory MAC, application digest, valid OTA state and active receiver capability. Transfer complete, reboot pending and deployment verified are distinct states.

The console remains awake during an active deployment. If it restarts or loses power, it reconciles the node's actual build before offering a retry. Keep e-paper refresh coalesced and separate from the transfer worker; no frame-rate progress animation. No throughput promise before measurement on the two actual boards.

## Storage, structure and style

Keep image files/manifests in a dedicated Flockinator directory on the existing console SD volume without formatting or changing unrelated files. Private authorisation material belongs in provisioned console NVS, not in public manifests. Validate lengths, identifiers and digests before reading/sending. The host prepares manifest plus image from a verified build; console compilation is unnecessary.

Node receiver: `firmware/node-platform/src/`; SD sender and deployment state: `firmware/management-console/src/`; shared codec/state-model tests: `firmware/shared/commissioning/`; packaging/provisioning: `tools/node-commissioner/`; evidence: `docs/validation/cluster-deployment/`.

Use explicit states and bounded buffers, four-space indentation and separate transport from flash I/O:

```cpp
enum class DeploymentState {
    Idle, Preparing, Transferring, Verifying, RebootPending, Verified, Failed
};
// A radio acknowledgement cannot advance RebootPending to Verified.
```

## Commands and testing

Build/test with the same two device and two native environments documented in `SPEC-flock-network.md`; run host tests with:

```sh
uv run --project tools/node-commissioner python -m pytest tools/node-commissioner/tests -q
$HOME run --project-dir firmware/node-platform --environment waveshare-s3
$HOME run --project-dir firmware/management-console --environment lilygo-s3
$HOME test --project-dir firmware/node-platform --environment native
$HOME test --project-dir firmware/management-console --environment native
```

Native state-machine tests cover reordered/lost/duplicate/changing chunks, wrong session/target/authentication, oversize/truncated/bad digest, timeout, replayed commit and sender restart. Test these behaviours before real flash writes.

Success requires **two successive real A1 updates from LilyGo SD over ESP-NOW**, with digest/identity/receiver verification after each; an interrupted transfer; an invalid image; a deliberately failed first boot and rollback; and console loss/restart reconciliation. Record duration and retry counts. Only then set `espnow_deployment_verified` for the tested node/build path. Other nodes require their own reported receiver/link checks, and per-node deployment evidence when updated.

## Boundaries

- Always: preserve running slot until validation, identity partition, Wi-Fi fallback and unrelated SD files; verify physical USB identities before bootstrap; reject unsupported images.
- Ask first: card formatting, eFuse/security-policy changes, bootloader/partition migration or removing maintenance support from an experiment image.
- Never: enable unauthenticated erase/write, replace a running slot mid-transfer, claim a checksum proves publisher authority, or infer deployment success from a functioning radio.

Source: [ESP-IDF 5.5.4 OTA documentation](https://docs.espressif.com/projects/esp-idf/en/v5.5.4/esp32s3/api-reference/system/ota.html). Flockinator's existing Wi-Fi OTA/rollback evidence proves the node flash path; it does not yet validate this ESP-NOW sender/receiver.
