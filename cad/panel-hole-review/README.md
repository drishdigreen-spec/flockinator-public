# Corrected temporary panel supports — revision 2, 10 October 2026

The owner reported that the previous T and X supports do not align with their panels. The prior X design inferred mounting offsets from a third-party bracket despite a conflicting Waveshare drawing. That was the wrong reference. Its files are preserved under `../temporary-panel-joints/rejected-v1/` and must not be printed.

The owner has now confirmed that both the corner mounting positions and the separate edge M3 positions are wanted. This revision includes both sets: **six holes for the T, twelve for the X**. It is for the temporary touching-panel assembly, not the final spaced lighting grid.

## Physical fit confirmed — 11 October 2026

The owner confirms that the revised T and X pieces fit the actual panels. The inner holes are unused for joining because the corresponding mounts are inlaid; retain these holes for possible panel-to-back-plate attachment. Back-plate fastening depth, spacers and hardware are still to be designed. Revision 2 geometry is the physically fitting baseline and has not been changed. The original report is recorded in `physical-fit-observation.json`.

## Drawing-derived dimensions

Source: `references/repos/RGB-Matrix-Px-xx/hardware/dimensions/RGB-Matrix-Pxx-64x64/RGB-Matrix-P2_5-64x64-2D.dwg`. Its SHA-256 and original entity handles are recorded in `panel-hole-coordinates.json`. LibreDWG conversion and entity extraction were cross-checked against the drawing's text and dimension endpoints.

| Feature | Drawing dimensions | At nominal 160 mm panel pitch |
|---|---|---|
| Eight explicitly labelled M3 edge holes | Centres at (±73, ±45) and (±45, ±73) relative to panel centre | 7 mm and 35 mm offsets from adjacent panel edges |
| Opposing M3 rows | 146 mm | 14 mm across a touching-panel seam |
| Two M3 holes along an edge | 90 mm apart | 35 mm and 125 mm from the nominal edge datum |
| Corner mounting features | 145 mm square, centres at (±72.5, ±72.5) | 7.5 mm offsets; 15 mm square around a four-panel junction |
| Plastic shell | 159.8 ± 0.1 mm | 0.2 mm nominal shell gap at 160 mm panel pitch |

The nominal 160 mm panel edge and 159.8 mm plastic-shell edge are distinct datums. Offsets measured from the drawing's shell edge are 6.9/34.9 mm for the edge M3 set and 7.4 mm for the corner set. The bracket centre pattern uses 160 mm panel-to-panel pitch, consistent with the user's 160 mm panels. It does not use 159.8 mm pitch or force the plastic shells into contact.

The 145 mm corner pattern must not be confused with the 146 mm edge-hole pattern. The drawing depicts additional holes and positioning features that are not included. In particular, drawn hole diameters are not all thread specifications: the edge set is explicitly marked M3; the owner subsequently clarified that the inner holes correspond to inlaid mounts and are unused for joining. They remain available for a future back plate.

The rejected X used 10/33 mm offsets, making each edge-hole centre √13 ≈ 3.606 mm from its correct location. It also omitted the four corner mounting holes. The supplied third-party T's 20/66 mm paired spans and 23 mm row spacing likewise do not match the drawing's edge-hole pattern (14/70 mm and 28 mm). It is not the dimensional reference for this revision.

## Files

- `Flockinator-T-joint-v2.stl`, `.step`, `.FCStd`: approximately 82 × 40 × 6 mm, six holes, joins two panels at a perimeter seam.
- `Flockinator-X-joint-v2.stl`, `.step`, `.FCStd`: approximately 82 × 82 × 6 mm, twelve holes, joins four panels at an internal junction.
- `panel-hole-map.png`: all relevant hole positions on one panel, separated by type.
- `corrected-joints-overlay.png`: actual exported STL outlines/holes overlaid with expected drawing coordinates.
- `panel-hole-template-1to1.svg`: 190 × 210 mm paper template containing a nominal 160 mm panel outline and a 100 mm scale line. Print at 100%, without fit-to-page, and measure the scale line before using it.
- `corrected-validation.json`: solid/mesh and exported-hole validation results.

Both parts have a 3 mm contact plate, 3 mm outward-facing reinforcement ribs and 4 mm screw clearance holes. Ribs run along the seams rather than diagonally through the corner mounting positions. A 7 mm washer envelope clears the ribs geometrically at every hole. These are clearance holes, not printed threads. Print flat face down, ribs up; use the slicer profile appropriate to the chosen material and verify its preview. The owner has confirmed the printed parts fit; the actual slicer settings were not recorded.

A complete 4 × 4 array has nine internal X junctions and twelve perimeter T junctions. Revision 2 fit is now owner-confirmed. Use the joining holes that seat correctly; leave the inlaid inner mounting positions unused until the back-plate attachment is designed. Screw/standoff length and thread engagement depend on the actual hardware and washer stack. The fit report does not establish support strength or lifting capacity.

## Validation

The source drawing was independently re-extracted and matched all twelve audited locations. FreeCAD reports one valid solid per part. Re-imported STEP cylinder centres match the drawing-derived positions. STL cross-sections independently recover six/twelve through-holes with less than 0.01 mm centre error (actual numerical error below 0.000001 mm). Both STLs are watertight, consistently wound, and one connected body. These checks establish CAD alignment to the drawing. The separate 11 October owner report confirms physical fit; it does not establish a manufacturing tolerance or structural load rating. Generated CAD/preview metadata predates that report; the dated observation is the current physical-validation record.

The FreeCAD objects include a hole-coordinate spreadsheet and descriptive properties. Change source parameters and regenerate to edit; the properties are not live parametric constraints.

```sh
uv run --with ezdxf cad/panel-hole-review/extract_drawing.py
/Applications/FreeCAD.app/Contents/Resources/bin/python cad/panel-hole-review/build_corrected_joints.py
uv run --with trimesh --with scipy --with networkx --with matplotlib cad/panel-hole-review/verify_and_render.py
```

FreeCAD's bundled Python runs without launching a GUI or safe mode. The corrected connector geometry and scripts continue under GPL-3.0-or-later; attribution to the earlier John Turner bracket is retained for provenance, but its hole pattern is rejected. The original vendor drawing and downloaded user files are unchanged and retain their own provenance/licensing.
