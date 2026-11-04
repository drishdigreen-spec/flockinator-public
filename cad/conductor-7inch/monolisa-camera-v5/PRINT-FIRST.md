# FLOCKINATOR retro enclosure v4

Dark beige housing with dark brown raised lettering in the preview. Filament colours are selected in Bambu Studio; STLs do not encode them.

## Changes

- Rounded 4 mm outer plan corners and 0.8 mm top perimeter edge roll.
- Rounded screen-opening corners (3 mm radius); print the updated aperture gauge first because it differs from v3.
- Extended rounded front slots across the case and a longer rounded side speaker grille.
- FLOCKINATOR in rounded bold lettering, raised 0.8 mm above the inclined upper bezel.
- Flat-board, permanent rear port bay, removable base and deferred sensors retained.

## Printing options

**Single colour embossed:** use `UpperHousingEmbossedSingleColour.stl`, plus the base. Text is fused to the housing as one solid.

**Two colours:** import `UpperHousingForMulticolour.stl` and `FLOCKINATORColourPart.stl` together as parts of ONE object. They share assembly coordinates; retain their alignment and assign separate filaments. The housing has a matching shallow recess; letter and housing volumes do not overlap. The eleven disconnected letter solids are intentional. Do not independently drop the text to the bed or auto-arrange it. This is a multicolour print part, not a separately glued plaque with assembly clearance. Use either housing option, not both.

The base and screen gauge are separate prints. Current exports retain assembly orientation: bottom flat, housing upright. The upper housing starts at Z=3 mm; Bambu Studio should place the combined object on the bed. Keep the multicolour assembly together during any rotation or bed placement. Review supports under the inclined roof and around letter details; the former v3 face-down printing instructions do not apply automatically. No sliced project, printer profile or G-code is provided. Check all overhangs and first-layer contact in your chosen orientation.

A 0.4 mm nozzle and 0.20 mm layers are starting points, not a validated profile. Use the actual material's settings. Housing is approximately 195 x 132 mm in plan; confirm usable bed size. Prototype mounts and holes are unchanged from v3: M3 clearance base holes and 2.6 mm pilot bores in the housing towers, requiring suitable fastener trial before use.

## Verification and remaining fit work

All exported meshes passed FreeCAD mesh solid checks; BRep validity checks passed. Single-colour housing is one solid; multicolour lettering contains eleven solids. Geometry checks include no housing/base or housing/bare-LCD overlap and no two-colour housing/letter overlap.

**Hardware fit remains unverified:** full touch assembly and its retention, actual v1.6 PCB mounting and port positions, speaker cradle and wiring, connector access, cable reach, physical print and slicer supports. No claim of a ready-to-install complete enclosure. Print the inexpensive gauge before the full housing. See checks.json for dimensions and limitations.

FreeCAD and STEP retain the aligned two-colour assembly. The bare LCD is a visual reference and excluded from the STEP and STLs. Font outlines were generated locally using Arial Rounded Bold; the font file itself is not redistributed.

## V5 supersedes font and camera details above

Text now uses the owner's installed **MonoLisa Code Regular**, not Arial Rounded Bold. Original font O outline is enlarged uniformly to surround the camera aperture; the second O stays normal. A circular **10.6 mm aperture** is cut through the upper shell, centred inside the first O in FLOCK. This assumes a **10 mm lens**, with **0.3 mm radial clearance**. Actual lens barrel dimensions, sensor position/retention, field of view and vignetting are not established. Do not print expecting an unmeasured camera to fit. `camera-aperture.json` records aperture geometry and assumptions. Black lens in preview is a reference only, excluded from print files.

Text remains 0.8 mm raised with a 0.15 mm inset; both fused embossed and aligned multicolour options are provided. The local MonoLisa font file is not included or redistributed. Generation requires access to the owner's font installation. Font contour faces are reconstructed for coherent solids; tessellated coincident vertices are welded at 0.000001 mm coordinate precision. All exported meshes passed solid checks. Camera aperture clears the enlarged O lettering geometrically. All other v4 prototype/printing limitations still apply. Model names now end `monolisa-camera-v5`.
