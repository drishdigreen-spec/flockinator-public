# Speaker fit guides — revision 2

## Physical result — 28 October 2026

Owner reports the 92 × 36 mm, D5.6 guide is a **perfect fit**. All three
lug-gap gauges fit; 2.0 mm is the tightest but still possible. Adopt the tested
post pattern/diameter as the next cradle baseline. Use 2.1 mm as a proposed
starting capture gap for removable clips; flexible clip geometry and retention
remain untested. See `physical-fit-observation.json` for the exact report and scope.

The instructions below describe the completed gauge test and remain for reproduction.

Based on owner's 28 October feedback: lengthwise post spacing increased from
90 to 92 mm, width retained at 36 mm, post diameter retained at 5.6 mm. This is
a trial spacing, not a newly measured hole pattern. Body measured on this speaker:
99.6 × 44.5 × 21 mm; mounting lugs 1.9 mm thick. Original files are preserved.

## Print first

- `Speaker_post_guide_92x36_D5p6_v2.stl`
- `Speaker_lug_gap_2p1_v2.stl` (0.2 mm nominal clearance over measured lug)
- `Speaker_lug_gap_2p2_v2.stl` (0.3 mm nominal clearance, comparison)

An optional `Speaker_lug_gap_2p0_v2.stl` provides only 0.1 mm nominal clearance.
Do not force this onto the speaker; it may print too tight.

**All four STLs are already oriented on the bed. Do not rotate the gap gauges
as instructed for revision 1.** Import in millimetres at 100% scale. No supports
are intended. Inspect actual sliced layers and gaps before printing. Use the
same printer/nozzle, filament and settings as the first guides for comparison;
the earlier starting profile was 0.2 mm layers, 0.4 mm nozzle, five wall loops,
50% gyroid where space permits. Small sections may be entirely solid.

Post-guide envelope: 102 × 44 × 20 mm. Seat height remains 15 mm, with unbarbed
posts and a tapered lead-in. The extra length moves each end pair outward 1 mm;
there is no intentional change to width or grip diameter. Check all four posts
enter without bending and whether the larger shoulder columns touch the casing.
If shoulders rather than shafts interfere, report that before further changes.
Do not press on or load a diaphragm. These are alignment gauges, not final mounts.

Gap-gauge envelopes: 18 × (6 + gap) × 12 mm. Mark each printed part with its
gap value using a pen and keep it associated with its source file. Slide a rigid
lug edge into the opening without force. Report the smallest gap that enters
comfortably and whether there is noticeable play. No snap strength is tested yet.

The native CAD and dimensional manifest accompany the STLs. validation.json records
independent mesh checks, including four-post centre recovery and jaw-gap geometry.
No print job or G-code has been generated. Source reference attribution remains
Francois Stander / Printables 1274311 / CC BY 4.0; new gauge geometry continues
the project's GPL-3.0-or-later convention.
