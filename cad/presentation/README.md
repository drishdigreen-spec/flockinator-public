# Flockinator rounded hive concept — revision 3

Updated 8 October 2026. One rigid assembly, rounded tracks, provisional white timber feet, a rear steel power-box envelope and a separate battery-powered handheld LilyGo. The user superseded the four-quadrant transport proposal; the earlier package remains in `../archive/Flockinator-modular-concept.zip`.

This is a dimensioned appearance study, not manufacturing geometry or a structurally validated design. Existing purchased-track fit studies remain unchanged.

## Inspect the model

Open `http://127.0.0.1:8765/` while the local server is running. Orbit freely, choose daylight/warm/dim/unlit conditions, compare white/charcoal trim, inspect the rounded corner and handheld remote, or play an illustrative communication preview. `gallery.html` shows eight saved renders.

```sh
uv run --python 3.12 python -m http.server 8765 --bind 127.0.0.1 --directory cad/presentation
```

The viewer runs locally with vendored Three.js r180 and its MIT licence. No external resources are required at viewing time. CAD/source lengths are millimetres; GLB lengths are metres.

## Files

- `Flockinator-presentation.FCStd`: native FreeCAD model with rigid frame, independent nodes, rounded communication grid and handheld remote groups. All sixteen 64 × 64 baffle grids are present as compounds of intersecting strips.
- `Flockinator-presentation.step`: assembly envelopes, excluding detailed pixel baffles and rendered honeycomb texture.
- `Flockinator-concept.glb`: portable appearance model; all 65,536 pixels represented in sixteen 64 × 64 textures, not physical baffle meshes.
- `index.html`, `viewer.js`, `assembly.json`: interactive viewer and shared source geometry.
- `renders/`: eight views, including the separate remote and rounded corner detail.
- `mass-budget.json`, `cad-validation.json`, `render-validation.json`: labelled assumptions and checks.

## Geometry

| Parameter | Value |
|---|---:|
| Rigid display backing | 875.8 × 875.8 × 6 mm |
| Outer backing corner radius | 45 mm |
| Outer channel network | 835.8 × 835.8 mm |
| Outer track corner radius | 35.8 mm |
| Nominal aperture | 164.2 × 164.2 mm, 2 mm corner radii |
| Node pitch | 200 mm |
| Pixel face | 160 × 160 mm, full 64 × 64 |
| Panel clearance per side | 2.1 mm before trim |
| Trim outside panel edge | 1.2 mm |
| Straight trim-to-channel clearance | 0.9 mm nominal |
| Channel width between straight openings | 35.8 mm |
| Channel optical face | Z = 75.8 mm |
| Panel diffusion face | Z = 75.4 mm |
| Body depth including rear box/door | 257.8 mm |
| Overall envelope with feet | 875.8 W × 915.8 H × 500 D mm |
| Each provisional timber foot | 55 W × 40 H × 500 D mm |
| Rear steel-box nominal envelope | 300 × 300 × 150 mm |
| Handheld case envelope | 150 × 88 × 20 mm, unverified |

The full square pixel faces remain intact. With a 2 mm aperture radius, the nominal square trim corner still fits, but the diagonal clearance is smaller than on the straight edges and requires tolerance validation. Broad outer curves and subtle inner curves provide the organic form without masking corner pixels.

CAD and viewer use the same rounded profiles, sampled with 16 chords per quarter-circle. The selected radii are custom design candidates. They are not dimensions verified from purchased corner pieces. The honeycomb pattern is generated in common assembly coordinates and remains continuous across the communication network. It is a visual texture, not embossed printable tile geometry.

The network is shown as one connected shape to communicate the appearance; actual manufacturing still uses printable track/skin sections, with final seam locations, retention and strip routing to be designed. There are no transport splits or couplers in the current model. Channel bodies remain solid envelopes rather than hollow printable tracks. Panel hardware, speaker/USB clearances, backing ventilation, fixing points and the exact remote/battery fit remain provisional.

## Handheld controller

Battery operation is user-provided intent. The LilyGo is an independent handheld remote/status display; there is no display-mounted console bracket. The rendering places it beside the display only for scale and visual comparison. Its case and screen dimensions are placeholders, not a measured enclosure model.

Future specifications should address battery capacity/runtime, charging and SD access, sleep/reconnect behaviour, and deployment interruption. A running swarm should not depend on the handheld remaining awake. This criterion does not by itself establish that firmware can continue downloading from a sleeping or disconnected remote.

## Transport and weight

Move the assembly intact. Size remains below the user's approximate 1 × 1 m transport envelope. Handles/attachment points must transfer load to a verified structural backing/frame; printed optical covers are not lifting points. Protective packing and structural support remain open. The current model shows two white timber feet and a low rear-mounted power enclosure, superseding the separate-box concept. Foot joints, brackets, centre of mass and tipping resistance are unverified. Loads must transfer to a designed frame; the 6 mm backing alone is not established as adequate.

The illustrative subtotal is **13.68 kg for the display and timber feet, excluding the complete power assembly**, plus **0.30 kg allowance for the separate handheld**. The finished display mass is unknown. These are not measured masses. Backing mass is calculated from its rounded planar area and an assumed plywood density of 600 kg/m³; all other entries are allowances:

| Item | Planning mass |
|---|---:|
| Rounded 6 mm backing | 2.755 kg |
| Sixteen complete nodes, assumed 0.35 kg each | 5.60 kg |
| Printed parts | 2.00 kg |
| Frame and fasteners | 1.20 kg |
| Wiring and connectors | 0.80 kg |
| Two timber feet, assumed 600 kg/m³ | 1.32 kg |

Rear steel enclosure, both supplies, mains components and enclosure brackets are excluded pending measured masses, as are cases, foam, an alternative stand and spares. Weigh a complete node and real prints before selecting handles, mounts or cases. A 100 g change in actual node mass shifts the display total by 1.6 kg. Do not use the solid channel-envelope volume as a print-mass estimate.

## Power integration

One 240 V input to the rear enclosure and internal 5 V/12 V supplies is the current intent. The 12 V supply is unselected; neither two-supply fit nor total power/heat capacity is validated by this envelope. Have the mains integration reviewed and assembled by a qualified electrician. See `../../docs/research/assembly-and-power.md` for electrical, thermal and support constraints.

## Local optical validation

See `../print-validation/README.md` for full-panel exact-P2.5 meshes, removable sheets, original Duality corner samples and a separate FreeCAD test layout. These test parts do not make this appearance assembly manufacturing-ready.

## Rendering limits and validation

The geometry checks confirm valid envelope shapes, sixteen panels and sixteen optical grids. This does not prove manufacturability, mechanical fit or load capacity. Lighting is an artistic approximation and is not calibrated to the hardware's required 50% maximum brightness. Diffusion, colour and optical leakage require local physical tests.

Pink/amber/turquoise node imagery and communication traces are illustrative experiment content, not implemented trust behaviour. The illustrated feet and enclosure mounting are not engineered or load-tested. The remote is posed separately, not mounted to the structure.

## Rebuild

```sh
uv run cad/presentation/build_concept.py
/Applications/FreeCAD.app/Contents/Resources/bin/python cad/presentation/build_freecad.py
node cad/presentation/render.mjs
```

The native generator uses FreeCAD's shipped runtime without launching a GUI or safe mode. Rendering requires the local server and the bundled Playwright path recorded in `render.mjs`.
