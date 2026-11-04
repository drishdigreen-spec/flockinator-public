# Open Decisions and Verification

Current priorities and operating state (19 October 2026): [development baseline](development.md).
Historical entries below retain their original checkpoint dates.

No choices below are silently approved by this research baseline.

## Current handover — 16 October 2026

The table below is the original research checklist, not a current completion
report. Commissioning, cross-toolchain health/OTA integration, SD formatting and
handheld operation now have hardware evidence. Read [the handover](../HANDOVER.md)
and [decision register](decisions/README.md) first. Outstanding priorities are
campaign spec review, exact incoming controller model, optional pixel-contact
firmware port, game presets, physical diffuser/speaker tests and future lighting
and sensor integration. Eleven installed cards have full passes; five have short
passes after interrupted full tests, as recorded in the handover.

## Historical checklist

| Decision or uncertainty | Evidence needed |
|---|---|
| Capability boundaries | Human review of CAPABILITY-MAP.md |
| First experiment and definition of distributed inference | Candidate: sixteen isolated fly-derived models with ESP32 bodies. Select model, sensory/action mappings, plasticity, baseline controls and measurable communication outcomes |
| Firmware framework/toolchain | Node ESP-IDF 5.5.4 and console Arduino 2.0.17 builds exist; live cross-toolchain radio integration and combined workloads still need validation |
| Body/brain loop | Sensor capture-to-actuation latency/jitter/loss budgets; clock uncertainty; observation/action adapters; disconnect policy; one/two/sixteen-instance benchmarks |
| Multiple managers | Per-node/output ownership, authenticated takeover and exclusive deployment; concurrent observation without conflicting writes |
| SD staging and log retention | Direct OTA retained; staged-image validation/install semantics; card failures, quotas/rotation and persistent-data rollback compatibility |
| Wireless transport(s) | Sixteen-node delivery, latency, topology, coexistence and deployment measurements |
| LilyGo console adequacy | SD mount/read tests, UI responsiveness, telemetry and OTA workload |
| 128 GB filesystem | Actual formatting, driver/build configuration and sustained read/write tests |
| OTA continuity | Every experimental image retains update/management support; partition and recovery design |
| Persistent agent memory | Card capacities, schemas, wear/write policy, restart semantics and failure handling |
| Shared sensors | Device/interface, processing location, observation schema and timestamps |
| Expansion pins | Schematic pin allocation and conflicts with enabled peripherals |
| Lighting controller and protocol | WLED/custom choice, event mapping, strip voltage/type/count and routing |
| Track geometry | Inspect supplied purchased files and licence, clear opening versus pitch, diffuser dimensions |
| Mounts and spacing | Panel drawings, PCB clearances, acoustic/sensor access and visible diffuser area |
| Conference transport | User selected one rigid assembly; verify total weight, structural lifting points, protective cover/case and mounting. No routine quadrant disassembly requirement |
| Handheld LilyGo | Verify battery/runtime, charging and SD access, enclosure fit, status reconnection and interrupted deployment recovery; remote is separate from the display |
| Rounded hive appearance | Validate outer track curvature, small panel-aperture corner radii, honeycomb tile phase and printable seam locations on a local prototype |
| Local and outsourced print configuration | X2D full 64 × 64 diffuser plus segmented border first; Wobbl3D H2C/H2D sample before batch production; record and compare actual nozzle/profile, optical/opaque filaments and tolerances |
| Distinct node appearance | Compare white/semi-translucent faces with removable white, black or coloured trim; evaluate lit/unlit boundaries and light leakage |
| Shared-channel semantics | Two-node test: distinguish individual node state from activity on a shared rail; determine whether separate optical lanes are necessary |
| Rogue-node and trust experiments | Define attempted/delivered/accepted messages, observer-specific trust and exclusion, optional ground-truth overlays, and management/observation continuity during disruption |
| Power budget | Panel/controller measurements at the required 50% brightness ceiling, separate LED budget and simultaneous peak demand |
| Power enclosure | Rear mounting and one 240 V inlet preferred; verify both supplies, internal usable space, frame attachment, earthing/protection, cable entries and heat rejection |
| Stand or white wooden feet | Weigh the complete assembly, locate its centre of mass and validate tipping resistance and frame/foot joints; rendered feet are provisional |
| Bambu optical material | Compare Basic Jade White 10100 and optionally Matte Ivory White 11100 at the same 0.3 mm thickness; record batch, plate, nozzle and layer plan |
| Full pixel-grid registration | Original linked 160 mm model measures 2.4920635 mm pitch; exact-P2.5 local grids supplied, but actual LED datum, slicing and physical fit remain to be checked |

Research is not hardware verification. Future specifications should turn selected items into concrete acceptance criteria and executable validation commands.
