# Forward-facing perimeter speaker carriers — first-fit prototype v1

**Current design: [Continuous speaker border v3](border-v3/README.md).** Four evenly spaced speakers per side, enclosed in overlapping 160 mm pitch sections with rounded clip-connected corners. Includes rear panel-edge M3 mounting tabs, shared corner braces, snap-fit coupons and a first-fit printing kit. CAD verified; physical fit and slicing pending. The [separate-box v2 option](enclosed-v2/README.md) and original v1 notes below are retained as history.

**Protection requirement:** the bare v1 carriers do not complete the requested speaker protection. See [the downloaded lual enclosure review](box-reference-lual/README.md) for a measured 113 × 48 × 23 mm snap-in shell with front grille. Its width conflicts with current twin spacing; do not batch print an enclosure/carrier combination before integration and fit checks.

## Latest hardware measurement — 11 October 2026

Latest mounting review: approximately 6 mm speaker openings are owner-reported; see [mounting and case review](mounting-and-case-review.md) for temporary M3 fastening, optional isolation and the recommended protective cradle. No new case geometry has been generated.

The owner's subsequent hand measurement is **98 × 44 × 20 mm (width × height × depth)**, with four mounting holes approximately 10 mm from the front/back fascia. This takes precedence over the earlier approximate agreement with the downloaded model. The 10 mm description appears to concern mounting depth, but its direction and flange-face/centre datum are awaiting clarification. The earlier 90 × 36 mm hole pattern has not been replaced by a new centre-to-centre measurement.

**The v1 CAD below remains unchanged and reference-based.** Its geometry checks still describe the exports, but its precise 3.85 mm clearance prediction is not established for the measured hardware. Resolve the mounting-depth datum and confirm the hole spacing before using that prediction or batch printing. The new body is 1.5 mm shorter, 0.8 mm narrower and approximately 1.3 mm thinner than the reference; these differences do not specify where its holes lie. See `speaker-reference/owner-measurements.json` for the measurement record. The dimensions and clearance in the original v1 notes below describe the downloaded reference.

11 October 2026. Printable prototypes are available; **physical carrier fit is not yet tested**. The owner confirmed the reference speaker body, mounting pattern and depths. The original, physically fitting revision 2 T bracket is retained in full, including all six panel holes and back-plate mounting options. The existing T and X files are unchanged.

## Parts and arrangement

| Part in `carriers-v1/` | Full array quantity | Printed envelope, mm | Speakers per carrier |
| --- | ---: | --- | ---: |
| Flockinator-T-speaker-single-left-v1 | 4 | 112 × 66.4 × 12 | 1 |
| Flockinator-T-speaker-single-right-v1 | 4 | 112 × 66.4 × 12 | 1 |
| Flockinator-T-speaker-twin-v1 | 4 | 212 × 66.4 × 12 | 2 |

Each part has STL, STEP and FreeCAD files. Use millimetres and 100% scale. The supplied STLs are rotated into a suggested print orientation, different from the assembly coordinates in STEP/FreeCAD.

There are three T junctions per side of the nominal 640 × 640 mm touching-panel array. One single at each end junction and one twin at the middle junction provide four speakers per side. Seen in the front-view preview, use single-left at the left junction and single-right at the right junction, then rotate that whole arrangement for the other edges. Speaker bodies extend approximately 59.8 mm beyond each panel edge, giving a nominal 759.6 × 759.6 mm envelope before wires and fasteners.

`speaker-layout-concept.png` shows the proposed node assignment with speaker body outlines to scale; mounting connectors and cable paths are schematic. `speaker-routing-proposal.csv` assigns every node exactly once. Centre-node extensions are B2 → top, B3 → right, C3 → bottom and C2 → left. Each speaker remains electrically connected to its own node. Measure cable lengths along the actual route and include service allowance.

## Supplied speaker leads

Each speaker has a **150 mm lead with its ESP32 connector**, reported by the owner on 11 October 2026. Keep the stock lead wherever it reaches comfortably. Plan soldered extensions for B2, B3, C2 and C3, and for any perimeter route that proves too long. The twelve edge-node leads have not been confirmed to reach.

Dry-fit the speaker and ESP32 before choosing extension length. Measure the cable route from the actual board connector to the speaker cable exit, including bends, retention and enough slack to unplug it without pulling the terminals. Panel-centre-to-speaker-centre distance is not a cable-length measurement. Keep each speaker with its assigned node, preserve conductor pairing/polarity, insulate each soldered joint separately and secure the cable so the splice and connectors carry no mechanical load. Avoid stacking splices in the limited rear clearance. Label both ends with the node ID. Cable-exit orientation should influence the future cradle design.

## Speaker interface and orientation

- Owner-confirmed body: 99.5 × 44.8 mm, approximately 21.3 mm total depth; four hole centres on a 90 × 36 mm rectangle; approximately 9 mm rear projection from the reference flange's lower face.
- Each carrier uses the two holes along the speaker edge closest to the panels, 90 mm apart. The speaker body is 15 mm beyond the panel edge.
- **The printed pads sit in front of the speaker mounting lugs.** Seat the front flange face against the rear face of the pads, with the cones facing the audience. The front flange face is 3 mm forward of the panel mounting-contact plane. Mounting on the opposite side changes clearance and is not the arrangement evaluated here.
- Printed speaker holes are 4 mm clearance. Provisional fastening is M3 with broad washers appropriate to the actual lugs/grommets. The reference mesh has approximately 6.3 mm flange openings; this is not an M6 thread specification. Verify washers bridge the openings, and select screw length from the actual assembled stack.
- A pair of 3 mm lacing holes in each carrier's crossbar provides a small cable-tie point. Restrain the lead separately from the speaker terminals and preserve a service loop.

The modeled flange thickness is 2.15 mm; this and the opening diameter were read from the reference mesh, not separately confirmed by the owner. The model predicts a rear speaker extent of 8.15 mm behind the panel mounting-contact plane. **If the whiteboard is 12 mm behind that exact plane, nominal clearance is 3.85 mm.** Standoff length alone does not establish the installed plane; check the actual assembled clearance, including leads and fasteners.

## First print and acceptance checks

Print **one single and one twin first**, before the full set. The stepped geometry **requires supports** in the supplied STL orientation: inspect support coverage under the raised plate and speaker carrier in the slicer. No slicer profile, print time or filament estimate is validated. Use the successful panel-bracket material/settings as a starting point, then confirm layer bonding and support removal on these parts.

1. Remove supports without enlarging holes or altering contact surfaces. Confirm the original panel holes fit without forcing screws.
2. Fit the speaker to the front-side pads with appropriate washers. Check cone/surround and screw access, lug seating, and lead exit clearance.
3. Check the real speaker-to-whiteboard clearance, including screw ends and cable routing, with no load transferred through the speaker against the board.
4. Check the twin carrier for flex, rotation, cracking and audible vibration with both speakers attached. Keep strain off terminals.
5. Verify standoffs still seat correctly and the expanded assembly remains retained during the intended temporary use. The user's existing clearance observation is not a load rating.

Record results before printing four of each variant. These parts serve the temporary touching-panel whiteboard assembly, not the final spaced diffuser-grid design. Relocating speakers changes acoustic locality, particularly for the centre four nodes; retain the node-to-speaker map in experiment records.

## Geometry validation

`carrier-validation.json` records valid single CAD solids; complete preservation of the original T solid; exported STEP mounting-hole centres; and watertight, consistently wound, single-body STLs. Independent mesh sections recover the eight 4 mm holes in each single and ten in the twin, with centre error below 0.000001 mm relative to design. Those counts exclude the two 3 mm cable-tie holes.

The generator also checks panel-front intrusion, a 7 mm rear access envelope at panel holes, simplified speaker cone envelopes and front screw access. These are geometry checks, not physical strength, fit, fatigue or acoustic tests. The multi-part source mesh is a visual reference and is not treated as a manufacturing drawing or a verified full-depth screw bore.

Regenerate with FreeCAD's bundled Python (no safe-mode GUI launch):

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/python /Volumes/devops/flockinator/cad/perimeter-speakers/build_speaker_carriers.py
uv run --with trimesh --with scipy --with networkx --with matplotlib /Volumes/devops/flockinator/cad/perimeter-speakers/verify_carriers.py
uv run --with matplotlib /Volumes/devops/flockinator/cad/perimeter-speakers/layout.py
```

## Sources and licensing

The carrier imports `../panel-hole-review/Flockinator-T-joint-v2.step`; its panel interface derives from the Waveshare P2.5 drawing and was physically confirmed by the owner. Carrier files and generator are GPL-3.0-or-later; see `LICENSE-GPL-3.0.txt` and the original bracket documentation.

Speaker reference: **Francois Stander, [Waveshare 8Ω 5W Speaker, Printables #1274311](https://www.printables.com/model/1274311-waveshare-8o-5w-speaker/files)**, licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). `speaker-reference/speaker-reference-original.stl` is an unchanged copy of the downloaded mesh, SHA-256 `3386c9d7bedcbb09c19a3ba0a2b28d56195bd3548722fc4494701590587fe068`. Dimension diagrams and speaker-envelope previews are our simplified adaptations of that reference; attribution is retained here. Dimensions were measured from the mesh and the primary dimensions confirmed by the owner, rather than taken from an official Waveshare mechanical drawing. Reference data is in `speaker-reference/dimensions.json`.

The [Waveshare product listing](https://www.waveshare.com/product/esp32-s3-rgb-matrix.htm) identifies the kit's 8 Ω, 5 W speaker. The electrical rating does not establish mounting dimensions.
