# Spec: Patternflow audio-flocking experiment

Status: draft for review, 2 November 2026 (Australia/Sydney).
Module: `experiments`, using the existing `node-platform`, `flock-network` and
`cluster-deployment` responsibilities in [the capability map](CAPABILITY-MAP.md).
No firmware implementation, build or deployment is claimed by this document.

## Objective and owner direction

Build alternative firmware using [Patternflow](https://github.com/engmung/Patternflow).
Each of the sixteen independent nodes has microphone input, speaker output and
its own 64 × 64 visual patterns. Nodes influence one another through musical and
audio interaction. This is a new experiment alongside the existing mission
presentation, not a change to that presentation's meaning.

The owner authorised pursuing this firmware and confirmed the upstream source.
The behaviour and communication choices below are proposed defaults rather than
additional owner decisions. [The source review](docs/research/patternflow-waveshare-port.md)
records the exact revision and board-port requirements.

## Proposed first experiment: listen, answer, adapt

Each node owns its phase, tempo, pitch choice, activity envelope and random seed.
It hears room audio, extracts level/onset and frequency-band information, and
produces short enveloped musical phrases. Its musical state also drives the
Patternflow parameter lanes, so a node's visible activity reflects what it is
hearing and producing.

Start with an explicitly engineered oscillator/call-and-response baseline:

1. A node listens and updates its local audio features.
2. A detected onset outside its own playback/recovery interval can pull its
   oscillator phase by a bounded amount and schedule an answer.
3. Answers use a configurable small pitch set and bounded duration, amplitude,
   rate and queue size. Sound does not imply knowledge of the sender's identity.
4. Playback ends; the node returns to listening. Own-output exclusion and a
   configurable settling interval reduce immediate self-triggering. This is not
   acoustic echo cancellation and must be tested in the actual enclosure.
5. The same local state changes hue, movement, density and pulse intensity on
   that node's panel, through a named pattern mapping.

Proposed first mode: **acoustic coupling**. Radio continues to support explicit
management, telemetry and experiment configuration, but does not supply hidden
peer timing, phase or note state to the behaviour. Radio-assisted coordination
can be a separate, explicitly labelled comparison mode after the acoustic pair
works. A common start command alone is not evidence of acoustic cooperation.

No remote model, DAW or always-on host is required for this baseline. MIDI/OSC
integration can follow; it is not a substitute for producing sound on the node.

## Firmware boundary and preservation requirements

- Create a separate `firmware/patternflow-node/` target and build identity using
  pinned upstream source. Keep the reference checkout unmodified.
- Port Patternflow to the exact Waveshare N32R16 board. Retain its runtime and
  feature interfaces where feasible; isolate board-specific compatibility edits.
  Do not silently replace the requested firmware with an unrelated visual demo.
- Resolve the Arduino/ESP-IDF version, octal memory boot support, module storage,
  encoder-free control and display/audio pin ownership before release builds.
- Preserve provisioned identity, credentials, SD contents and recoverability.
  Reuse Flockinator's authenticated management semantics. Any partition migration
  requires its own concrete migration/recovery procedure before device writes.
- Default panel brightness to 25%; hard clamp to 50% after all pattern, console,
  restored-setting and remote-control paths.
- Cold boot and reset leave the speaker muted until the experiment is explicitly
  started. Stop cancels queued notes and mutes output. Control/configuration loss
  behaviour is explicit: a locally started autonomous run can continue; expired
  remote actions never play later after reconnection.

## Runtime and data ownership

One board audio service owns the shared full-duplex I2S0 channels and both codecs.
Use the existing physical MIC1/MIC2 configuration initially, at 16 kHz, 16-bit
stereo. Do not reuse Patternflow's PDM GPIO/driver initialisation.

Audio capture and output run outside the rendering/control loop with finite DMA
waits. Publish timestamped feature snapshots to behaviour and rendering. Carry
validity and freshness explicitly; failed or constant input must not become
synthetic evidence of a neighbour. Raw audio remains local and transient unless
recording is explicitly enabled in a later scope.

Behaviour produces bounded note events and normalized visual parameters, not
direct peripheral calls. The output worker owns synthesis, attack/release ramps,
mute and underrun handling. Rendering must not block on a note or microphone.

Telemetry includes firmware/upstream revision, node and run identity, seed,
coupling mode, audio validity/age, level and clipping, onsets, own-output exclusion,
notes scheduled/played/dropped, render timings, audio overruns/underruns and heap
headroom. Physical hearing, audible output and cooperation remain separate
acceptance results from successful driver calls.

## Structure and conventions

Proposed implementation locations (not yet created):

- `firmware/patternflow-node/`: pinned-source preparation, board port, build
  configuration, feature adapters, licence/provenance record and README.
- `firmware/shared/audio-flocking/`: platform-independent feature/behaviour and
  scheduling logic, with native tests. Do not extend commissioning wire records
  implicitly to carry experimental peer state.
- `docs/validation/audio-flocking/`: build manifests and separate bench results.

Use bounded storage, explicit units and monotonic timestamps. Separate PCM sample
time, local event time and remote timestamps. No dynamic allocation in audio
callbacks or per-sample synthesis. Reject non-finite/out-of-range controls before
they reach an oscillator. For example, an onset is eligible only when capture is
valid, fresh, outside the own-output exclusion interval and outside the response
refractory interval.

## Verification and success criteria

The first reviewable implementation must contain:

1. A reproducible exact-board image build with upstream commit, dependencies,
   configuration, image size and digest recorded. A build is not hardware proof.
2. Native tests using generated PCM: silence, DC, clipping, known tones/onsets,
   self-output exclusion, bounded response rate, stale observations, deterministic
   seeded behaviour, timer wraparound, queue overflow and stop/mute semantics.
3. A real Patternflow pattern connected to microphone features and musical state,
   with synthetic fixtures explicitly distinguished from live capture.
4. A single-node bench check: independent 64 × 64 output, physical microphone
   response and finite audible notes, working stop and authenticated maintenance,
   plus tested return to the previous image without identity loss.
5. A two-node check: perturb one node and observe the other's response. Repeat
   with speaker muted and coupling disabled; use independent initial phases.
   Log effects and timing rather than claiming emergence from synchrony alone.
6. Only after the pair passes, scale to sixteen and measure audio timing,
   clipping/feedback, frame delivery, CPU/heap and power under combined load.

Target a 30 fps visual loop and begin analysis with 512-sample windows (32 ms at
16 kHz). These are starting design targets; record measured missed frames and
capture-to-response latency before claiming musical timing quality. Exact note
limits and thresholds become test constants during implementation and are tuned
on one node before fleet use.

Existing regression commands, run sequentially from the repository root:

```sh
uvx --from platformio==6.2.0 pio test --project-dir firmware/node-platform -e native
uvx --from platformio==6.2.0 pio test --project-dir firmware/management-console -e native
uv run --project tools/node-commissioner python -m pytest tools/node-commissioner/tests -q
```

The new target's build/test commands must be added to its README once the runtime
choice has been demonstrated. No speculative command here is presented as a
currently working build. USB/OTA uploads are separate from compilation.

## Open decision

Confirm the first coupling mode: acoustic-only behaviour with radio management
(proposed), or radio-assisted exchange of musical state from the outset. The
board port and per-node audio work are common to both. Choice of scale, timbre,
pattern and response sensitivity can remain configurable defaults.

## Owner-selected visual milestone — 2 November 2026

The owner directed: “first try deploying the custom firmware so we can see the
visualisations happening.” This selects a visual-only deployment trial before
audio/cooperation implementation. The first slice adapts the actual upstream
Origin preset onto the existing commissioned firmware, with a separate
`patternflow-trial` environment and `0.11.0-patternflow-trial` identity. It is a
selective renderer integration, not a claim that the full upstream firmware has
been ported. Test one authenticated node first and record its actual boot/image
and rendering status. Audio coupling choice remains open for the later scope.

## Owner-selected catalogue milestone — 2 November 2026

The owner requested downloading/installing all patterns with randomisation and
synchronisation later. Release 0.11.1 installs all 34 available firmware artwork
presets on all sixteen nodes. The 14 explicitly browser-only patterns remain
outside this firmware catalogue because they have no firmware implementations.
Each node independently shuffles the catalogue, chooses bounded random parameter
settings and changes every 25–45 seconds. Audio coupling and sync remain future
work. See validation/patternflow/playlist-fleet/ for actual deployment evidence.
