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
