# Full-panel optical and stock-channel validation kit

Prepared 8 October 2026. These files support local X2D optical/fit experiments before commissioning Wobbl3D. They are not production release files or verified printer profiles. No print was started and no G-code was generated.

## Ordered materials

The owner has ordered one 1 kg refill each of Basic Jade White 10100, Basic Black 10101, Matte Ivory White 11100 and Matte Charcoal 11101. Delivery is not yet confirmed. Record spool batch and profile when received. These four materials allow controlled white-diffusion and black-grid comparisons; they are not a final production selection.

## First print sequence

1. Print one **full 64 × 64 black grid**, using `stl/Flockinator_64x64_P2p5_wall0p4_depth3_mm.stl`. Candidate material: Bambu PLA Basic Black **10101**. Use the actual X2D/nozzle profile, keep model scale at 100%, and inspect the sliced preview for all 4096 open cells and continuous walls.
2. Print one full white sheet from `stl/Flockinator_full_panel_diffusion_sheet_0p3_mm.stl` in Bambu PLA Basic Jade White **10100**. The part is 0.3 mm thick: explicitly reach that thickness with a suitable layer plan, such as 0.2 mm then 0.1 mm. Inspect actual layers; do not let a uniform 0.2 mm profile silently turn it into a different thickness. Keep the sheet separate/removable.
3. When the ordered Matte arrives, print the same 0.3 mm sheet in PLA Matte Ivory White **11100**. Compare the same geometry, plate finish and orientation. Use the same Basic Black grid beneath both white sheets. Then print the identical full 3 mm grid in Matte Charcoal 11101 and compare each white sheet over it, changing only one component at a time.
4. Only if useful after the first test, compare the **6 mm-deep grid** and/or **0.5 mm Basic white sheet**. More depth or thickness is a test variable, not an assumed improvement.
5. Print a purchased corner track, two 100 mm straight tracks, matching skins and two splice blocks from `purchased-original-samples/`. The local files are unchanged source copies. Choose the matching corner skin hand after checking the seam orientation in the slicer/CAD; LH and RH are provided for comparison, not because both belong on one corner. The guide specifies two M3 × 6 mm flat-head screws per splice block. Verify fit on the actual parts before tightening.

The stock samples provide a corner with two legs alongside a full panel, not a complete 200 mm-pitch closed border. This deliberate first test checks the purchased cross-section, rounded corner, hex appearance and fit without pretending that the 50 mm spans and shortened tees are already printable.

## Grid dimensions and registration

The generated grid has **4096 square 2.1 mm apertures**, exact **2.5 mm centre pitch**, **0.4 mm walls**, and optional 3 or 6 mm depth. To retain a full 0.4 mm perimeter wall without moving the aperture centres, its outer size is **160.4 × 160.4 mm**, extending 0.2 mm beyond each edge of the nominal 160 mm panel. The removable sheets match this 160.4 mm envelope. This remains inside a 164.2 mm opening, subject to actual tolerances.

In generator coordinates, the panel reference is 0..160 mm and grid/sheet boundaries are −0.2..160.2 mm. Nominal cell centres run 1.25..158.75 mm, a 157.5 mm span. **Measure the actual panel's first LED centre and LED package height before fixing the grid position or depth.** Do not assume the panel's 160 mm edge dimensions establish the LED datum. Do not press walls onto LED packages.

The explicit cells are geometry, not an infill-percentage approximation. Import each STL as millimetres. Use a plate/orientation suitable for the filament; keep the grid flat and inspect first-layer expansion, thin-wall continuity and flatness. Default 0.4 mm-nozzle settings are only a starting assumption; actual nozzles are not yet confirmed. Walls must survive slicing at their intended widths. Avoid support material inside the cells.

Both grid meshes are watertight, consistently wound, single connected bodies; source geometry contains all 4096 holes. This proves geometry integrity, not successful slicing or printing. `part-manifest.json` records the checks.

## Linked Printables model

The original [Adafruit 64×64 grid by nlapenn](https://www.printables.com/model/252635-adafruit-64x64-led-matrix-grids) was downloaded through the normal website. It is retained under `../../references/adafruit-64x64-grid-252635/` with creator attribution and CC BY 4.0 provenance.

Although labelled 160 mm/P2.5, its measured centre pitch is approximately **2.4920635 mm**, with 157.0 mm between first/last centres. A centred exact-P2.5 array differs by 0.25 mm at each edge. It may still be usable after a physical check, but is not adopted as an exact registered grid. See the reference folder's measurement report. Our comparison grids were generated independently, not by silently rescaling the creator's file. Do not uniformly scale the original to correct pitch: that also changes its outer dimensions and wall widths.

The creator suggests an infill-based alternative for print speed. Their historical percentage and time estimates do not establish 64 correct cells, registration or timing on the X2D. If an infill version is later tested, verify the first/last centres and every row/column in the sliced output.

## Additional full-resolution infill reference

The newly supplied [CJ raster guide](../../references/matrix-raster-1135471/README.md) explicitly describes a full 64 × 64 infill-generated grid: one perimeter, no top/bottom layers, Grid infill at 27.3%, 0° angle and zero maximum infill-anchor length in its Prusa profile. Its listed model is **192 mm**, so those settings are not a verified recipe for our 160 mm P2.5 panel or Bambu printer. The described optical stack uses diffuser paper behind acrylic.

Add a slicer-generated full-panel candidate to the comparison once the actual printer/nozzle is known. Use a solid volume for that candidate; do not apply this recipe to the explicit-hole STL. Validate all 64 cells per axis, exact 2.5 mm pitch, 157.5 mm centre span and phase against the real LEDs before printing. The explicit grids supplied here remain the measured geometry baseline; this addition does not claim a tested Bambu infill profile.

## Purchased Duality skin setup

The supplied `guide.pdf` calls for a **0.3 mm white diffusion membrane**, with a layer-height adjustment to reproduce it, and a colour change at **0.5 mm** for the subsequent pattern when using contrast. Start with an all-white skin for the user's preferred hive appearance; compare the guide's contrasting pattern only as a separate variant. Preserve the white membrane in either case. Do not assume the 0.5 mm colour-change height means the membrane itself is 0.5 mm thick.

The guide/product PDF recommends **Hatchbox White PLA**, identified by its link to ASIN B00J0GMMP6. Bambu Basic Jade White is a candidate substitute, not a proven optical match. The original parts were designed around a 10 mm-wide, 60 LED/m strip. Use the actual proposed strip for the channel test; its LED spacing and distance from the cover differ from the P2.5 panel.

Source STL axes are not necessarily build-plate axes: the track height is along source Y. Orient the track with its base down and skin with the intended flat optical face down; do not print the source import upright merely because it appears that way. Follow the original guide for the purchased geometry. The existing files are not pre-sliced for X2D.

## Existing-channel feasibility

`stock-geometry-report.json` records the actual stock 150 corner and LH honeycomb skin. With the verified source transform and a centred 160 mm panel at 200 mm pitch, projected mesh-to-panel overlap is **0 mm²**. This is a useful footprint check, not a verified mating/LED/clearance assembly.

The current compact full grid is not obtainable from unchanged stock sections alone: 75 mm corner/cross arms leave **50 mm straight spans** at 200 mm pitch, while the stock tee stem extends 132.1 mm. Retain the purchased cross-section and mating features while adapting lengths; finish and validate tee cuts as closed geometry. Honeycomb phase at these new joins must be checked. The presentation's custom 35.8 mm corner radius is not a measured stock-corner radius.

`Flockinator-optical-test-layout.FCStd` shows the full panel, grid and sheet next to one purchased corner and two 100 mm legs. The 2 mm gap above its reference panel face is a placeholder for measured LED height. Do not print this assembled document as one part. Original track geometry embedded in the local layout remains subject to the purchased licence; nothing has been uploaded to a supplier.

## Evaluate and record

Use the same panel, same test patterns, same room lighting and fixed camera exposure. Keep panel brightness at or below the required **50% cap**.

- Inspect light transmission, colour cast, hotspots, pinholes and unlit appearance.
- Display isolated RGB pixels, checkerboards, one-pixel rows/columns, white fields and text across the entire panel.
- Check bleed into neighbouring cells, corner-cell registration and front/30°/45° views. Compare 3 versus 6 mm depth only if needed.
- Test channel skin diffusion with the actual strip, including corner and straight seams, both with the panel lit and unlit.
- Check skin retention, panel/trim clearance, sheet flatness, removal and reassembly.
- Measure temperatures during a representative prolonged run at the cap with display/audio/radio active. Inspect deformation/creep before choosing structural materials.

Print matching stock channel skins in both ordered whites for comparison. Record results in `results.csv`. Before commissioning, lock **filament product + colour/SKU + batch, nozzle, layer plan, line widths, optical thickness, plate finish, orientation and the reviewed slicer project**. Supply the accepted physical sample as Wobbl3D's appearance reference. Do not substitute a different white on colour-name alone.

## Rebuild

```sh
uv run --with trimesh --with shapely --with mapbox-earcut --with scipy cad/print-validation/build_test_parts.py
uv run --with trimesh --with shapely cad/print-validation/inspect_stock.py
/Applications/FreeCAD.app/Contents/Resources/bin/python cad/print-validation/build_preview.py
```
