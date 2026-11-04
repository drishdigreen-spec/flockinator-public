# Continuous speaker border — revision 3

Updates the already authorised enclosure design to the owner's requested continuous overlapping border (11 October 2026). Replaces v2's two singles plus twin per side. This is a first-fit prototype for the touching 640 × 640 mm array, not the future spaced diffuser grid.

## Contract and assumptions

- Sixteen independent forward-facing speaker chambers: four per side, at 80/240/400/560 mm from the adjacent array corner. Sixteen identical 160 mm pitch straights plus four identical rotated corner sections.
- Nominal outer border 780 × 780 mm, 68 mm radial width, 2 mm panel-edge gap; rounded outer corners R20. Every speaker remains connected to its own ESP32.
- Actual straight body length 159.6 mm creates 0.4 mm joint clearance. Front shiplap overlaps 4.2 mm with 0.3 mm depth clearance. Replaceable rear snap bridges locate joints; M3 panel mounts support weight.
- New per-panel mount uses verified P2.5 edge holes: ±45 mm along the panel edge from centre, 7 mm inboard. This is a different interface from the previously fitted seam T; do not copy its seam coordinates. Retain all existing T/X files unchanged.
- Two rear mounting tabs per straight; corner braces share the nearest two edge screws. Recessed mounting-seat depth remains unknown: provide 1/2 mm spacer coupons and require a supported physical fit before batch printing.
- Preserve fully surrounding enclosure, removable honeycomb guard, closed rear cover, padded rigid-casing retention, small padded cable outlet and fibre reservation. No contact with diaphragms. Do not depend on uncertain speaker lug dimensions.
- Allow 99.5 × 44.8 × 21.3 mm speaker reference envelope; owner measured 98 × 44 × 20. Central cavity 104 × 50. Grille inner surface is 3 mm ahead of speaker envelope; rear fibre reservation 80 × 26 × 5 mm.
- Front Z = −35, main rear cover +3 relative to panel rear contact plane. Rear snap posts reach +7.3; corner brace +6.3 before hardware. User's 12 mm standoffs do not establish clearance until physically assembled.
- White bodies/corners and optional charcoal/black grilles; user chooses after first sample. Requested 50% gyroid and 5 wall loops. Thin walls/grille webs can be solid; slicing determines toolpaths. No printer job is sent.
- Identical straight parts are under 170 mm long. Corner/brace parts under 120 mm; fits the official X2D 256 mm main-nozzle XY envelope. Slicer selection and actual installed printer remain user controlled.
- Snap action, strength, screw engagement, recessed seats, board clearance, cable reach, acoustics and magnetic retention remain unverified physical properties. No promised bass improvement.

## Plan and tasks

1. Generate solid CAD and assembly with explicit dimensions; export manufacturing STEP/STL/FCStd and reference-only preview meshes.
2. Validate exported solids, watertight meshes, hole coordinates, speaker/fibre clearances, adjacent shiplap, corner/straight/brace clearances and clip seated geometry. Include two snap-throat options and a small coupon before large prints.
3. Render actual geometry, write assembly/print instructions and package a first-fit set plus complete source archive.

## Commands and structure

Build: `/Applications/FreeCAD.app/Contents/Resources/bin/python /Volumes/devops/flockinator/cad/perimeter-speakers/border-v3/build_border.py`

Verify/render: `uv run --with trimesh --with scipy --with networkx --with matplotlib /Volumes/devops/flockinator/cad/perimeter-speakers/border-v3/verify_render.py`

`parts/` contains printable exports, `preview-meshes/` assembly-coordinate references, `validation.json` geometry evidence, `README.md` physical acceptance checks. Python uses millimetres and named geometric helpers, e.g. `cylinder(x, y, z, radius, height)`.

Always preserve proven panel geometry sources and label untested fit. Ask before changing panel spacing or sending print jobs. Never treat a render or static snap-clearance check as a physical fit/strength test. Downloaded third-party speaker-box mesh is reference only and is not incorporated.
