# FreeCAD fit assembly

## Current physical build checkpoint — 28 October 2026

[Consolidated design and measurements](../docs/design/physical-build-checkpoint-2026-10-28.md)
is the current resume point. Use the [raised acrylic-node concept](acrylic-node-concept/README.md)
for appearance and [speaker fit guides revision 2](speaker-fit-guide/revision-2/FIRST-PRINT.md)
for the owner-tested 92 × 36 mm / D5.6 mounting pattern. The historical concepts
below are retained references. No complete panel-box fabrication release exists yet.

## Rounded hive presentation concept

See [presentation/README.md](presentation/README.md) for the revised 200 mm-pitch appearance model, native FreeCAD/STEP/GLB files, interactive lighting/angle viewer and eight renders. It uses one rigid rounded backing, rounded track corners, continuous honeycomb styling and a separate handheld LilyGo. The user superseded the quadrant transport proposal; its previous package is preserved in `archive/Flockinator-modular-concept.zip`. This separate concept uses custom channel envelopes and procedural honeycomb appearance; it does not replace the purchased-mesh fit study or constitute printable geometry. Mass figures are explicit planning allowances.

## Current compact candidate

`Flockinator-compact-fit.FCStd` is the current candidate, created in the existing normal FreeCAD session. Each 160 mm panel is centred on its cell. Pitch is 199.8 mm, clear opening 164 mm and nominal clearance 2 mm on each side. Backing envelope is 875 mm square including the trial border.

This compact arrangement requires forty 49.8 mm connecting spans (orange placeholders) and shortened tee stems. The tee track/skin meshes are clipped to 75 mm arms for layout inspection; those cuts are open meshes, not fabrication-ready adaptations. Purchased source files remain unchanged. Exact seamless hex phase and joints require design work. The earlier 250 mm candidate is retained as a comparison.

Open `Flockinator-grid-fit.FCStd` in FreeCAD. The full 4 × 4 study uses actual purchased track and seamless MatteHex meshes, sixteen confirmed 160 × 160 mm panel-face envelopes and a backing envelope.

The assembled candidate has 250 mm junction pitch, a nominal 214.2 mm clear opening and 27.1 mm clearance per panel side. Backing is approximately 1075.8 mm square, including a trial 20 mm perimeter margin beyond nominal track width. Panel rear faces are at a trial 48 mm above the backing; panel thickness is a trial 6 mm. These depth values are not measurements.

## Interpretation

- Pale meshes: actual purchased diffuser covers, correctly paired with track families. Pattern phase and seam closure remain to be checked and are visibly imperfect in this first assembly.
- Dark squares: panel face envelopes, not detailed panel electronics or mounting-hole models.
- Orange blocks: twelve **42.9 mm connecting-span placeholders**, requiring custom or trimmed parts. They are not printable track geometry.
- Hidden `RearSpace` group: trial 140 × 140 × 45 mm volumes for concealed hardware. These are not actual speaker/controller dimensions.
- `Dimensions` sheet records trial dimensions and the 185.8 mm compact target pitch. The compact target is recorded only, not assembled here.

Mesh inspection corrected the earlier assumption that all junction arms are 75 mm: the tee stem extends 132.1 mm from its true intersection. Consequently this uniform 250 mm grid uses 28 stock 100 mm straights and twelve shorter spans, rather than forty stock straights. Nine crosses, twelve tees and four corners are represented. Couplers and fasteners are not modelled.

## Validation performed

The saved native file was reopened using FreeCAD's runtime. It contains 16 panel solids (all valid), 53 track meshes, 53 diffuser meshes and 12 adaptation placeholders. Top preview was inspected visually. Panel-face spacing is 90 mm; there is no adjacent panel-face overlap. This validates the face/layout concept, not a fabrication-ready fit.

M3 hole locations, screw engagement, panel/controller thickness, speaker dimensions, USB and power connector bend clearance, stand-off mounts, thermal/acoustic access, couplers and the exact honeycomb seam phase still require detailed modelling or physical measurement.

`build_grid.py` generates the native document through FreeCAD's bundled runtime. `show_grid.FCMacro` assigns presentation colours and opens it in FreeCAD. The purchased sources remain unchanged. Generated model embeds purchased meshes and is retained locally for this prototype.

## Local optical validation

See [print-validation/README.md](print-validation/README.md) for the full 64 × 64 exact-P2.5 grid, removable diffusion sheets, original purchased channel samples, measured reference model and local test sequence. Bambu materials remain candidates pending physical tests.
