# Temporary four-panel X connector — fit-test candidate

The owner confirms the eight printed John Turner edge brackets fit the actual panels with the panel edges touching. This connector is for that temporary bench assembly, separate from the spaced diffuser-grid assembly.

Files: `Flockinator-X-joint-fit-test.stl`, `.step`, `.FCStd`, `preview.png`, the two generation scripts, and `validation.json`. All dimensions are millimetres. The FreeCAD file contains a solid and descriptive parameters; modify the script's near/far values and rerun to regenerate geometry. The spreadsheet/properties do not drive the model interactively.

## Candidate geometry and outstanding fit measurement

- Approximately 78 × 78 × 6 mm; 3 mm contact plate plus 3 mm ribs on the outward/rear face.
- Eight 4 mm through holes, two per panel, with nominal corner offsets (10,33) and (33,10) mm in each quadrant. Flat contact face toward the panel mounting bosses; ribs face away from the panels.
- Rounded ends with 4 mm nominal material between each hole edge and outer pad edge. Screw head/washer bearing area is flat and clear of ribs.
- Nine pieces cover every internal junction in a full 4 × 4 panel arrangement. One piece is enough to test a four-panel junction first.

The source STL measures 95 × 45 × 8 mm, with a 3 mm plate and approximately 4.005 mm holes. Its hole centres are (-5,-24), (15,-24), (-28,-47), (38,-47) in source coordinates. Their symmetry establishes 20 mm and 66 mm paired spacing. Mapping those onto symmetric corner offsets of 10 mm and 33 mm is an inference: the actual panel seam location is not encoded in the STL.

The Waveshare P2.5 DWG was converted with LibreDWG and inspected. Its M3 locations appear at approximately 7 mm and 35 mm from the nominal panel edges (14 mm paired spacing across touching panels), which differs from the supplied bracket. The source bracket's confirmed physical fit is relevant, but does not remove the need to check the inferred second axis. The owner has been asked to measure **across-seam hole spacing and distance inward from the perpendicular panel edge**. Do not batch print until these are confirmed and one joint is fitted.

## Print and fit

Suggested starting setup: same material that worked for the existing temporary brackets, 0.4 mm nozzle, 0.2 mm layers, four walls, five top/bottom layers, and 30–40% infill. These are trial slicer settings, not validated printer output. Place the broad flat face on the bed, ribs upward; geometry has no intentional support requirement. Slice at 100% scale in millimetres.

Use M3 screws with suitable washers for the 4 mm clearance holes. Select length from actual boss depth, plate and washer thickness; do not assume the author's screws provide the correct engagement for every panel revision. Check that the plate seats on mounting supports without bearing on electronic components or obstructing ribbon/power connectors. Do not force misaligned holes.

This is a temporary alignment/holding connector, not a tested lifting point or a replacement for the final load-bearing frame. Keep the assembly supported during fitting and handling.

## Validation and provenance

FreeCAD reports one valid solid. The exported STL is watertight, consistently wound and one connected body. Geometric volume is approximately 13.44 cm³; slicer material usage depends on infill and walls. Mechanical strength, screw engagement and actual rear clearance remain untested.

New geometry is supplied under GPL-3.0-or-later, with attribution to John Turner's source bracket, whose supplied Printables guide specifies GPLv3. Full GPLv3 text and source hash are included. The user's original STL, 3MF and PDF are unchanged. The source guide is at `$HOME

Rebuild using FreeCAD's bundled runtime (no GUI or safe-mode launch):

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/python cad/temporary-panel-joints/build_x_bracket.py
uv run --with trimesh --with scipy --with networkx --with matplotlib cad/temporary-panel-joints/render_preview.py
```
