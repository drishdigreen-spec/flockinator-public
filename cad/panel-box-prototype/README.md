# One-node panel box prototype — 29 October 2026

Prototype for a single-node owner fit test. **Not a production print release.**

## Physical result — 29 October 2026

Owner printed the box base: the component board lines up perfectly with the
mounting holes, and the box bottom has ample space for additional components,
even the speaker or sensors from the expansion header. See
`physical-fit-observation.json`. Cradle/clips, riser seating, track tabs and
plugged-power clearance are not yet reported.
Built per the next-build-step in
[physical build checkpoint](../../docs/design/physical-build-checkpoint-2026-10-28.md).

## Contents

- `parameters.py` — all dimensions with sources; unmeasured values marked.
- `build.py` — FreeCAD build (headless-verified, FreeCAD 1.1.4).
  Run: `freecadcmd build.py` from this directory.
- `verify.py` — reopens the saved model and checks validity, speaker/controller
  clearance and clip gap. Writes `validation.json`.
- `Panel-box-prototype.FCStd` / `.step` — combined assembly for review.
- `stl/` — printable prototype parts: node tray (with eight fused M3 standoff
  bosses at the audited panel coordinates), 5 mm riser, speaker cradle,
  speaker clip (print 4×), track section with screw tabs.

## What is registered vs provisional

- Panel: audited 159.8 mm shell, eight M3 edge holes (±73/±45, ±45/±73) and
  four corner features (±72.5) from `panel-hole-coordinates.json`. The generic
  76 × 48 mm concept controller block is replaced by the real 50.01 × 42 × 1.6
  PCB outline, M2.5 mounts at 42.54 mm, and 8.5/5.6 mm face keep-outs.
- Controller XY is driven by `HUB75_CENTRE` in `parameters.py`, currently
  (0, 0). No retained source dimensions the HUB75 header on the panel, so
  this placement is **provisional** until measured on a real assembled node.
  Tray USB/SD cutouts follow the controller and are provisional with it.
- Speaker cradle reuses the physically proven guide geometry: posts at
  (±46, ±18), D5.6 shafts, 15 mm shoulders, speaker body 99.6 × 44.5 × 21.
  Clips are separate replaceable parts with a 2.1 mm capture gap over the
  measured 1.9 mm lugs (0.2 mm nominal clearance). Retention, release force
  and compliant pads are untested.
- The power-plug clearance box is a placeholder. It currently overlaps the
  speaker reference by 10,440 mm³ (see `validation.json`): the real VH4 plug,
  latch and cable-bend envelope must be measured before this layout is final.

## Tray rev 2 — vents (29 October 2026)

Owner tip after the first print: fine vents drooped over long unsupported
spans. Rev 2 keeps the stylised horizontal slots but segments them: 12 mm
slots with 4 mm vertical ribs (longest bridge 12 mm, under the 25 mm FDM
guideline), backed inside by a 1.6 mm vertical rib grid. Same tray file name;
re-exported and re-verified. Not yet printed — judge droop on the next print.

## Forward ToF pod (29 October 2026)

Owner direction: very small ~$7 laser ToF per node, looking directly forward,
powered from the node board's 3.3 V. `ToF_pod_PROTOTYPE` sits top-centre on
the riser with an open 14 × 8 window (no cover glass) and a generic slotted
carrier; `ToF_carrier_GENERIC` takes the module until a real unit is measured.

Electrical facts to design against, not yet proven on hardware: these modules
are I2C. One per node avoids address conflicts (VL53 default 0x29). The node
expansion header offers 3.3 V/GND/two GPIO (GPIO45/46 candidates), which carry
ESP32-S3 strapping constraints, and external I2C on that header is **not**
established — wiring must be proven on one node before fleet assumptions.
Range listings (50/200/400 cm) are different chips, not settings; FOV and
performance through any future cover are unclaimed. The earlier Waveshare
Mini candidate needs 4.3–5.2 V and does **not** suit the 3.3 V header.

## Verification

`validation.json`: all solids valid (17 with the ToF pod); speaker/controller keep-out overlap
0 mm³; cradle envelope 102 × 45 × 20 mm (matches the proven guide family).
Geometry validity only — no print, fit, thermal, acoustic or load claim.

## Next

1. Print the speaker cradle + four clips and the 5 mm riser; seat the panel
   and speaker on this tray and report fit.
2. Check the plugged VH4 envelope, USB-C/SD sweeps and track screw tabs on
   the printed assembly; update `parameters.py` if anything moves.
3. Only then consider batch prints or the acrylic order.
