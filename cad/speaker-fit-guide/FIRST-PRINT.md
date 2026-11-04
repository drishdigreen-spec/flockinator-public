# First speaker mounting fit prints

28 October 2026. Print test gauges only, not the complete concept enclosure.
No printer job has been sent and no G-code is supplied.

## Start with these two parts

1. `stl/Speaker_post_guide_D5p6.stl` — four 5.6 mm locating posts on the model's
   90 × 36 mm hole pattern. Flat rails on the bed, posts upward. No supports intended.
2. `stl/Speaker_lug_gap_2p6.stl` — a 2.6 mm lug-thickness gap gauge. Rotate this
   part 90 degrees onto one of its broad 18 × 8.6 mm side faces so the C opening
   is drawn in the bed plane. This avoids printing the upper jaw as an overhang.

Import at 100%, millimetres. Use the actual printer/nozzle/filament profile.
Suggested starting layer height 0.2 mm and 0.4 mm nozzle. Use available Basic PLA
for the fit check. Retain the owner's five-wall/50% gyroid preference where the
slicer has room; these small features will largely become solid. Check the
preview for separate posts and a clean open jaw gap before printing.

The post guide's 100 × 44 × 20 mm envelope fits the documented printer bed size.
The 15 mm shoulder height provides space for the reference speaker's rear
projection, but the frame is not an exact body cradle. Try the speaker with its
sound-emitting faces away from the base rails, bringing its flange toward the
four posts. Stop if any casing or moving surface touches the guide. Do not
press or flex the speaker to make it seat. The posts are intentionally unbarbed.

Test the thickness gauge on an accessible rigid lug edge away from diaphragms
and wires. It only measures usable capture space, not snap strength. If the
lug shape prevents entry, report that rather than forcing or modifying it.

## Alternatives, only if needed

- Post guide D5p2: more clearance if D5p6 is too tight.
- Post guide D5p9: less play if D5p6 fits but is loose.
- Gap 2p2 or 3p0: compare if 2p6 is loose or tight respectively.
  Rotate each gap gauge onto its broad side as above.

To identify the three guides without embossed labels: the two smaller shaft
diameters are 5.2 and 5.6 mm, the largest is 5.9 mm. Keep files/printed pieces
separate and mark their rails with a pen after printing. Mark gap gauges likewise.

## Report back

- Do all four posts enter simultaneously, without force?
- Which post diameter gives easy insertion with little play?
- Does the speaker rest on all four shoulders without body contact?
- Which jaw gap slides onto the lug with slight clearance?
- Does the lug edge provide room for a removable clip and a finger/tool release?

These answers set the removable clip and cradle dimensions before incorporating
them into the first panel box. No retention or structural load rating is claimed.

## Provenance and validation

Mounting pattern derives from Francois Stander's third-party Waveshare speaker
model (Printables 1274311, CC BY 4.0), SHA-256 recorded in the speaker reference
folder. Actual body measurement remains the owner's 98 × 44 × 20 mm.
Gauge geometry is new and retains the existing CAD project's GPL-3.0-or-later
convention. Physical hole size and lug thickness are precisely what these gauges
test. `validation.json` records independent mesh checks; it is not a slicing pass.
