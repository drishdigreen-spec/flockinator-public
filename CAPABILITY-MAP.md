# Capability Map: Flockinator

Current baseline, 4 November 2026: the sixteen panels run 0.10.2-journal and the
Korvo runs the standalone 0.9.0 web host, planner and communication lab. The fleet
is stopped at the owner's request; desktop hosting and USB bridge services are
disabled. [Standalone verification](firmware/korvo-monitor/validation/standalone-0.9.0/README.md).
Learning currently runs centrally on the Korvo. Local per-node learning,
continuous review/build/evaluation and controller self-OTA remain future work.
The proposed extension is in [the experiment laboratory capability map](CAPABILITY-MAP-experiment-lab.md).
It is pending review. The module responsibilities below remain the index;
historical approval and build-order notes follow.

| Module id | Responsibility | Depends on |
|---|---|---|
| node-platform | Node hardware access, identity, lifecycle, independent display, sensors, audio and SD storage | — |
| flock-network | Discovery, messages, connectivity and communication event reporting | node-platform |
| agent-runtime | Local/remote/hybrid brains, observation/action adapters, runtime state and explicit body/brain bindings | node-platform, flock-network |
| cluster-deployment | Deployment from LilyGo or authorised external tools, manifests, transport adapters, optional SD staging, activation and recovery | node-platform, flock-network |
| management-console | LilyGo handheld interface and optional external management integrations, node health, experiment controls and deployment management | flock-network, agent-runtime, cluster-deployment |
| communication-lighting | Future separate controller consumes events and animates node outlines and paths | flock-network |
| physical-assembly | FreeCAD models, mounts, diffuser grid, access, wiring and power enclosure/distribution | — |
| experiments | Defined behaviours, configuration, observations and reproducible evaluation | agent-runtime |

Dependency arrows mean software/provider prerequisites. Physical assembly consumes hardware constraints and lighting geometry but is not a firmware dependency. Shared sensor ingestion is currently scoped within node-platform and flock-network; review whether it merits its own module once devices are selected.

Proposed build order: validate hardware and physical constraints; node-platform → flock-network → agent-runtime and cluster-deployment → experiments and management-console. Communication-lighting can follow flock-network later. Physical design develops alongside hardware validation.

Transport, framework and experiment selections remain open. The management console is not intended to be a mandatory intermediary for all agent messages.

On 9 October 2026 the owner reaffirmed ESP-NOW firmware deployment from the handheld as a core use case. This selects the intended deployment transport; experiment messaging transport remains open. The first deployment proof targets one real node and two successive image changes before fleet rollout. See the follow-on requirements in SPEC-management-console.md.

## Current focus: handheld bring-up

The user selected LilyGo work while filament is on order. [SPEC-management-console.md](SPEC-management-console.md) scopes an initial hardware/diagnostic and explicitly simulated UI milestone. It can be developed before the provider modules; live telemetry, agent controls and deployment still depend on them. The owner approved this first milestone with “proceed” on 9 October 2026. Its firmware is built and uploaded; this does not approve the remaining module scopes.

## Current focus: node commissioning

On 13 October 2026 the owner approved [SPEC-node-platform.md](SPEC-node-platform.md), including the host Wi-Fi OTA gate before fleet release. A1 is attached and identified. This does not mark the LilyGo deployment milestone complete. Implementation plan and tasks: `tasks/node-platform/`; existing console acceptance items remain open.

## Commissioning and handheld integration — 13 October 2026

Owner clarification: flash/identify/inventory at the host, then move each controller to its panel for visual checks. Physical acceptance no longer gates handing off a programmed controller or beginning the next label. Wi-Fi settings are provisioned privately into NVS as part of station setup.

The existing module boundaries remain: `node-platform` owns the station and device lifecycle; `flock-network` provides the authenticated node/console link; `cluster-deployment` provides the ESP-NOW image sender/receiver; `management-console` displays live observations and deployment state. For this milestone the live console depends on flock-network, and its deployment controls additionally depend on cluster-deployment; agent-runtime is not needed for commissioning.

Review package: `SPEC-flock-network.md`, `SPEC-cluster-deployment.md`, and the live commissioning addendum in `SPEC-management-console.md`. Build order after review: finish the already approved station workflow; live A1↔LilyGo link; one-node ESP-NOW update/recovery proof; then the same protocol for all sixteen. Station and console builds may be developed independently, but hardware writes must always be tied to verified identities.

## Flexible body/brain roles — 13 October 2026

The owner clarified that LilyGo is a portable controller/image store, not the sole management system or a required inference relay. Brains can run on remote GPU/CPU systems while nodes supply sensing, physical output timing and local storage. External web management and logging are optional deployment roles. Preserve transport/configuration flexibility and distinguish management, observation/action, bulk/logging and experimental peer traffic.

Existing module IDs are retained; this clarification does not introduce a mandatory server or select the brain backend. The candidate sixteen-fly-brain experiment, storage modes, controller arbitration and latency requirements are captured in `docs/design/embodied-experiment-platform.md`. The owner approved the detailed link/deployment specs on 13 October 2026. The initial LilyGo ESP-NOW path is implemented and has passed real A1 update/recovery trials; broader experiment transports remain open. See docs/validation/cluster-deployment/README.md.

## Proposed reconnaissance presentation — 16 October 2026

The owner proposed a military-style simulated drone swarm to visualise reconnaissance, HQ/peer communication, disrupted messages and a deceptive node. [Design concept](docs/design/reconnaissance-swarm-experiment.md) proposes a fictional beacon-survey scenario, per-node drone avatars and a presenter view separating ground truth from local beliefs. It reuses node-platform, flock-network, agent-runtime and experiments; later console/lighting integrations remain distinct consumers. This is a capability/scope proposal, not approval of an experiment protocol or a replacement for currently running 0.7.0 random expressions.
