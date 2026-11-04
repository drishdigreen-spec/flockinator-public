# Fully enclosed perimeter speaker — prototype v2

User authorization, 11 October 2026: proceed with a fully surrounding speaker enclosure, acoustic fibre behind the speaker, 50% gyroid infill and five wall loops. This updates the existing approved speaker-mount direction; a bare carrier does not meet it.

## Design contract

- Preserve the complete physically fitting panel T interface by importing the original v2 STEP. Do not alter panel holes.
- Use an independently constructed rounded shell and honeycomb grille, removable for speaker service. The downloaded lual shell remains a reference; its mesh is not incorporated in these solids.
- Surround all sides and rear, with only intentional front acoustic holes and a small cable passage. Cable passage must be padded/sealed after routing; do not claim a hermetic printed box.
- Hold the rigid speaker casing between padded front lip and removable rear retaining frame. No load on either diaphragm; no reliance on the approximate 6 mm holes or unverified flange depth. Validate actual casing seating before batch printing.
- Design for owner body 98 × 44 × 20 mm and allow the reference 99.5 × 44.8 × 21.3 mm envelope. Internal cavity 104 × 50 mm. Replaceable foam shims accommodate tolerance.
- Outer module 116 × 62 × 40 mm. Rear cover at +5 mm relative to panel mounting plane, nominal whiteboard +12 mm: 7 mm nominal geometric gap, actual hardware to verify. Front grille projects to −35 mm.
- Speaker front envelope at −29 mm; up to 21.3 mm depth. Grille inner face −32 mm: 3 mm nominal diaphragm-envelope clearance. Retainer front −6 mm with foam shim to speaker rear. Open central rear space permits a loose approximately 5 mm fibre pad; do not pack into vents or against moving parts.
- Two singles plus one twin per side. Twin module centres 118 mm apart, providing a 2 mm shell gap; nearest single-to-twin shell gap 5 mm with centres 140/261/379/500: 121 − 116 = 5 mm.
- Each module uses four M3 through screws and captive rear hex nuts; starting fastener length M3 × 40, verify actual washer/engagement stack. Panels retain their existing appropriate hardware.
- Stock speaker lead 150 mm. Provide cable exit and external strain-relief points. Centre four and any perimeter route too long use owner-authorized soldered extensions.
- Print process requested: gyroid 50%, five wall loops. Geometry does not encode printer-specific G-code. Narrow grille webs may be solid and contain fewer paths; slicer preview governs achievable walls. Record support requirements and part orientation.

## Verification

Generate with FreeCAD bundled Python, export STEP/STL/FCStd, check all parts are valid solids and meshes are watertight. Check original T preservation, six panel bores, body/cover/grille/retainer interference, speaker envelope and diaphragm clearance, twin spacing, rear clearance, nut pockets and cable passage. Independently inspect exported meshes and render assembled/exploded views. Physical fit, strength, acoustic response and slicer validation remain prototype tests.

Acceptance: one single enclosed module can be printed, padded, wired and assembled for fit and listening comparison; no unsupported claim of increased bass from surrounding an already housed speaker.
