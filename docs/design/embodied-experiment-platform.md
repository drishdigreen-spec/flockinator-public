# Flexible bodies, brains and controllers

13 October 2026. Captured owner direction, with proposed engineering consequences. This is an architecture/experiment note, not a claim that the integrations exist or an approved implementation specification for remote inference.

## Roles and ownership

The Flockinator is a reusable experimental display made from sixteen independently addressable bodies. Each body owns its sensors, native 64×64 display, audio, radio interfaces and SD storage. Its decision-making can be local, remote, or hybrid. No requirement makes the LilyGo the sole controller or routes every observation through it.

| Role | Responsibility | Availability requirement |
| --- | --- | --- |
| ESP32 body | Sample sensors; timestamp observations; buffer/validate actions; maintain display/audio timing, identity, local storage and update/recovery services | Required for its physical node |
| Local or remote brain | Transform selected observations into decisions/actions; retain model state according to experiment | Configurable per node/run; remote GPU/CPU process allowed |
| LilyGo handheld | Portable controls, genuine health/status, SD image catalogue and deployments; bounded local log collection | Can sleep/disconnect without making healthy nodes stop; an active transfer requires interruption handling |
| External host/server | Optional inference, web management, orchestration, large image/media catalogue, analysis and central logging | Needed only by experiment roles assigned to it |
| Lighting controller | Render communication events as grid/path animations | Independent device; WLED/custom choice remains open |

An external host may perform several roles, but the software interfaces keep those roles distinguishable. A1's hardware identity is independent of its current brain, position, experiment role and firmware version. Record mappings explicitly. A remote process may move hosts without renaming the physical node.

Multiple authorised managers may observe concurrently. For a given node/output domain, a proposed explicit controller lease/session determines who can issue actions; reject expired sessions and conflicting deployments. Do not use silent last-writer-wins when both the LilyGo and server are present. Operator intervention is explicit and logged. Do not copy an unrestricted fleet-wide key to every client as the solution to multiple managers; authority provisioning and takeover semantics require their own implementation review.

## Separate traffic by purpose

1. **Management:** identity, health, configuration, experiment selection, firmware installation and recovery. LilyGo or external tooling can originate it through authorised interfaces.
2. **Observations and actions:** direct node↔brain streams with experiment-specific latency/quality requirements. They do not depend on an e-paper refresh or five-second health poll.
3. **Bulk data and logs:** images, media, checkpoints and bounded log uploads. Schedule or throttle them so they cannot accumulate unbounded queues or silently disrupt the measured real-time stream.
4. **Experimental communication:** only channels the experiment grants to agents, including optional packet or acoustic communication. Keep hidden management traffic and operator ground truth out of agent observations unless explicitly part of the experiment.

Use common versioned meanings above transport adapters, not one packet size or delivery policy for everything. The proposed 250-byte ESP-NOW commissioning envelope is specific to that protocol/toolchain pairing; it must not impose 128-byte chunks or five-second updates on Wi-Fi audio and action streams.

Candidate paths are Wi-Fi IP for remote brains/bulk transfer, ESP-NOW for direct lightweight links and handheld deployment, BLE for appropriate experiments/configuration, and USB serial for bootstrap, recovery or controlled wired trials. Acoustic communication is a separate experimental adapter. Support is advertised per installed build; availability in the chip is not implemented compatibility.

The ESP32-S3 shares its radio between Wi-Fi/BLE activities; these paths are not independent simultaneous radios. Benchmark co-enabled features and channel changes under the actual workload. [Espressif coexistence reference](https://docs.espressif.com/projects/esp-idf/en/v5.5.4/esp32s3/api-guides/coexist.html).

## Body/brain contract and latency

Observations identify node, experiment run, sample sequence, sensor/source, capture time, units/encoding and validity. Actions identify the current controller session, target node/output, sequence, intended execution time or deadline, and referenced media asset where appropriate. Brain simulation time and wall-clock time are separate fields/concepts. Clock offset and uncertainty must be measured before using cross-device timestamps as one-way latency evidence.

Keep panel refresh, audio playback buffers and basic hardware supervision local. A remote brain can issue a drawing primitive, colour, animation parameter or SD asset reference instead of streaming a complete framebuffer every refresh; raw frames remain available when an experiment requires them. Reject stale actions rather than replaying a long backlog after reconnection. Each experiment selects its loss-of-brain behaviour: pause, silence, a bounded hold, or a local policy, with a visible/logged disconnected state. Local panel brightness limits still apply regardless of which brain is active.

Measure capture→uplink→brain queue/compute→downlink→actuation, reporting median, p95/p99 latency, jitter, drops and queue depth. A fast ping is not a measured sensor-to-action loop. Choose numerical targets once the first model and modalities are selected; benchmark one, two, then sixteen simultaneous bodies before sizing a GPU cluster.

Illustrative payload budgets, not measured throughput: 16 kHz × 16-bit × two microphone channels is 64,000 bytes/s per node, or **8.192 Mbit/s for sixteen nodes in one direction**. Raw RGB565 64×64 frames at 30 fps require **31.45728 Mbit/s across sixteen nodes**. These exclude packet overhead, retries, output audio, logs and management. Use these calculations to choose features versus raw samples, not as a promise that the shared WLAN can sustain the combined workload.

## Storage and deployment

Owner intent: use node SD cards for large media, logs, node-specific data and optional cached firmware; use the LilyGo SD for portable image/media catalogues and selected logs; allow an external server as another source/sink. Collection policies, quotas, rotation and transfer priority are configurable. Missing/full/bad cards must report degraded capability without losing device identity or preventing an update path that does not require SD.

Two image delivery modes remain distinct:

- **Direct:** transfer validated application data to an inactive internal flash slot. This is the existing Wi-Fi update route and the proposed first ESP-NOW route; it works without node SD storage.
- **Staged, optional:** receive/download to a temporary SD file, validate length/digest/authorisation/compatibility, then mark it available. On an explicit install command, revalidate the file and copy it through the same inactive-slot OTA writer. A cached file is neither running firmware nor automatic permission to install. Loss of SD/power leaves the current application bootable.

Executable firmware still runs from the ESP32's configured flash application slot in this design; an SD image is a staging source. The same final validation/activation/rollback rules apply regardless of transport. [ESP-IDF OTA reference](https://docs.espressif.com/projects/esp-idf/en/v5.5.4/esp32s3/api-reference/system/ota.html).

Prefer changing experiment configuration, brain endpoint, media or model assignment without reflashing when the resident body interface is sufficient. Flash when code/drivers genuinely change. Include compatibility versions for persistent data and management services: application rollback does not automatically roll back SD/NVS data migrations. Do not make an incompatible data migration silently invalidate the previous application.

## Candidate experiment: sixteen fly-derived brains

The owner's proposed experiment assigns sixteen isolated model instances to sixteen physical bodies. The model/dataset/backend, GPU requirement, time step, learning/plasticity and real-time factor remain unselected and unmeasured. A sandbox/process boundary alone does not define which information agents can share; enforce that through the experiment's permitted observation channels and routing.

There is a published connectome-based Drosophila model that predicts selected sensorimotor responses, plus original source using leaky integrate-and-fire neurons and Brian2. These are useful starting points, not evidence that sixteen real-time instances will spontaneously discover one another or learn a communication code. [Shiu et al., 2024](https://doi.org/10.1038/s41586-024-07763-9); [original model source](https://github.com/philshiu/Drosophila_brain_model).

Required experiment adapters:

- **Observation encoding:** decide how microphone features/waveforms, temperature/humidity and permitted radio events stimulate model inputs. Audio/temperature/radio are not interchangeable with biological sensory neurons. Record every mapping, gain, temporal filter and noise model.
- **Action decoding:** map chosen model activity to tone frequency/envelope, panel patterns/colour, or authorised experimental packets. A stationary panel has no fly locomotor body. Outputs and feedback are designed mappings, not biological equivalents.
- **Sensor truth:** a panel emits light but the present per-node configuration has no camera. A later shared vision system needs explicit attribution. Wi-Fi/BLE packet/RSSI observations are limited radio observations, not a general electromagnetic-field sensor.
- **Isolation:** maintain separate model state/random seeds and prevent the host from supplying neighbour identities/state outside allowed channels. Keep management heartbeats, visualisation annotations and log aggregation from becoming an unintentional side channel.
- **Interpretation:** define measurable communication before claiming emergence. Synchronised tones may follow a common stimulus, echo or preset oscillator dynamics. A decoder placed in firmware is engineered communication; distinguish it from behaviour generated by the model.

Suggested progression: one model/body with recorded stimulus and measured latency; two isolated bodies with acoustic exchange only; ablate/mute one output, disrupt feedback or replay time-shuffled recordings; then sixteen. Compare against a simple oscillator/controller and disconnected/shuffled controls. Vary delay/jitter, distance, volume, noise, input mappings, connectivity, initial states and any explicitly implemented plasticity/reward rule. Record successful influence on another agent separately from tone synchronisation or packet delivery.

Lighting displays observed experiment events, with attempted/delivered/accepted categories where measurable. It does not assert a physical multi-hop path or intent merely because an animation joins two nodes.

## Consequences for current work

Proceed with the approved USB flash/identity/inventory procedure and preserve the working Wi-Fi OTA fallback. Extend the pending LilyGo/link/deployment specifications to support these roles without making the handheld a compulsory central relay. Do not select a brain implementation or build remote-inference infrastructure merely from this candidate experiment. The live link and ESP-NOW deployment specifications remain pending review; this clarification is not recorded as approval of their detailed wire protocol.
