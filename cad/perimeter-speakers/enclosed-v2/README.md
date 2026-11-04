# Flockinator fully enclosed speaker prototype v2

11 October 2026. This version provides a surrounding shell, honeycomb front guard and closed removable rear cover integrated with the proven T panel connector. Each speaker remains a removable, independent assembly. **First-fit prototype: CAD/export checks are complete only when recorded in validation.json; physical fit, printing and acoustic performance remain untested.**

## Parts to print

| Part | First single test | Complete 16-speaker array |
| --- | ---: | ---: |
| Speaker shell | 1 | 16 |
| Honeycomb grille | 1 | 16 |
| Internal retaining frame | 1 | 16 |
| T rear cover, single-left | 1 | 4 |
| T rear cover, single-right | 0 | 4 |
| T rear cover, twin | 0 | 4 |

After the single test, print one twin cover and two complete shell/grille/retainer sets to test the two-speaker arrangement before batching. Three printable components are shared across every speaker; the integrated rear cover supplies the single/twin arrangement. The twin has two independent enclosed cavities.

The `parts` folder contains STL, STEP and FreeCAD files for each component. **Use the STL orientation provided, millimetres, 100% scale.** STEP and FreeCAD files use assembly coordinates. The assembly FreeCAD files include speaker/fibre envelope objects marked REFERENCE; those objects are not printable parts. Edit dimensions in `build_enclosed.py` and regenerate; FreeCAD solid properties are descriptive rather than live constraints.

## Requested slicer settings

- **Infill: gyroid, 50%.**
- **Wall loops: 5.**
- Suggested initial layer height: 0.20 mm with a 0.4 mm nozzle; verify on the actual printer/profile.
- Shell, grille and retaining frame: supplied front-side-down orientation, no designed unsupported ledges. Inspect the sliced result before printing.
- Integrated T/rear covers: rear-side-down orientation, **supports required** beneath raised cover and panel-plate areas. Keep nut seats and bores accessible after support removal.
- Five loops are a slicer setting, not a guarantee of five extrusion paths in every feature: narrow grille webs become solid with as many paths as fit. The 50% infill applies only where there is room between walls/skins; it is not the grille opening percentage.
- Suggested appearance using available filament: PLA Basic Jade White shell/cover and PLA Basic Black grille. Retainer colour is not visible. Material shrinkage, actual line widths, plate and support choices require the user's printer profile.

`print-settings.json` records the requested settings in a printer-independent form. **It is not a Bambu-importable process preset.** No printer-specific G-code or sliced Bambu project has been generated, and no print job has been sent. Slice geometry in your selected Bambu profile and apply the settings above. The 3MF/Prusa G-code from the earlier lual reference is not used to print this design.

## Dimensions and clearance

- Each enclosure: **116 × 62 × 40 mm**. Shell cavity: 104 × 50 mm before its front lip and corner transitions.
- Accommodated envelope: 99.5 × 44.8 × 21.3 mm, covering both the reference and owner-reported 98 × 44 × 20 mm body. This verifies bounding geometry only; actual rim, wire exit and protrusions must be checked.
- Grille inner face: Z = −32 mm; speaker's assumed foremost envelope: −29 mm, giving **3 mm nominal clearance**. Do not allow pads or retainers to push a diaphragm into the guard.
- Rear cover: Z = +5 mm. A whiteboard at Z = +12 mm gives **7 mm nominal rear clearance**, before any protruding fastener or cable. The 12 mm board datum remains an installation assumption to verify.
- The enclosure projects 35 mm toward the audience from the panel mounting plane. The panel's actual front surface has not been measured against that plane; this is not a panel-front protrusion dimension.
- Twin centres: **118 mm**, leaving **2 mm** between shells. Across each side, centres at 140, 261, 379 and 500 mm give 5 mm single-to-twin gaps. Nominal complete outline is **776 × 776 mm** before wiring/fasteners.

## Hardware and assembly

Starting hardware per speaker: **four M3 × 40 machine screws, four M3 nuts and suitable small flat washers**. Case holes are 3.4 mm clearance. Rear nut pockets are 5.8 mm across flats and 2.6 mm deep; test the actual nuts and print before assembly. Verify screw engagement with the chosen washer stack; the end must not project into the whiteboard clearance. If your hardware differs, change the stack or screw length. Retain the original appropriate panel screws/standoffs; do not substitute the case screws into the panel.

1. Deburr and remove supports. Dry-fit the four corner screws through grille, shell and rear cover, and seat the nuts. Confirm all original panel holes still align without force.
2. Apply thin compliant foam pads to the shell's front seating lip at rigid housing contact areas. Keep all material out of the two moving surfaces and acoustic openings. Start around 1 mm thick, then adjust to the actual housing shape.
3. Place the speaker behind that lip facing the grille. The central front aperture is 94 × 40 mm. Check the lip contacts the rigid casing rather than either surround or diaphragm.
4. Add thin rear pads between the **rigid rear rim** and the removable retaining frame. The designed retainer face is approximately 1.7 mm behind the reference envelope, or 3 mm behind the owner's 20 mm body when placed at the front datum. Select the pad stack to retain gently without bending the housing. These are fit allowances, not measured foam compression requirements.
5. Place the retaining frame behind the speaker. Four pillars on the rear cover retain the frame when the case is fastened. The original speaker mounting holes are unused; this avoids relying on their approximate spacing and flange depth.
6. Add a loose acoustic-fibre pad behind the speaker in the reserved space, then fit the rear cover. Tighten evenly, retaining the speaker without crushing pads flat or forcing the shell. Check no internal part rattles.
7. Check grille clearance, cable routing and speaker-to-board clearance on the actual panel assembly before listening tests.

The rim-clamping concept needs a physical check: if the housing lacks suitable rigid seating areas, stop and adjust the cradle before tightening. Avoid glue on the speaker or any permanent change until the fit is proven.

## Acoustic fibre and cabling

Reserved pad envelope: **80 × 26 × 5 mm**, centred behind the speaker. It fits through the retainer's central opening with clearance from the modeled speaker rear and cover pillars. Secure it loosely so fibres cannot migrate into ports or moving parts. Use the actual speaker's vents to determine final placement; avoid tightly packing the space. If loose fibre sheds, retain it in acoustically permeable scrim. The existing speaker housing is retained; this added rear space does not automatically become the driver's acoustic rear chamber. Sound improvement requires comparison testing.

A **6 × 3 mm cable opening** exits at the top rear seam. Route the original connector outside before closing the cover, then fit soft packing/grommet material around the wire as needed. Do not force a connector through the small passage or clamp insulation between mating faces. The wire diameter has not been measured, so check the opening first. Use the paired 3 mm lacing holes on the carrier rail for external strain relief; keep ties clear of the panel and speaker.

The stock lead is 150 mm. Check real routed reach for each node; use soldered, individually insulated and strain-relieved extensions for the central four and any other short routes. The enclosure is mechanically closed at its sides/rear, with intentional acoustic and cable openings; it is not an airtightness-certified box.

## Verification and next test

`validation.json` records CAD solid checks, original T preservation, panel-front clearance, speaker and fibre envelope clearance, corner screw passages, twin spacing and independent STL bore-centre checks. These do not establish a structural load rating or physical speaker fit. `enclosed-speaker-preview.png` renders exported geometry; the speaker and fibre are dimension proxies.

Test one single at the requested print settings. Compare the same speaker/node with and without the outer enclosure and with/without fibre, using the same volume, position and speech/tones. Listen for rattling and muffling; check node microphone pickup. Then test a twin before printing the full array. Keep successful settings consistent across nodes.

## Reproduction and provenance

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/python /Volumes/devops/flockinator/cad/perimeter-speakers/enclosed-v2/build_enclosed.py
uv run --with trimesh --with scipy --with networkx --with matplotlib /Volumes/devops/flockinator/cad/perimeter-speakers/enclosed-v2/verify_and_render.py
/Applications/FreeCAD.app/Contents/Resources/bin/python /Volumes/devops/flockinator/cad/perimeter-speakers/enclosed-v2/check_assembly.py
```

New enclosure geometry is constructed from primitives using the user's requirements and recorded speaker dimensions. The proven T solid is imported from `../../panel-hole-review/Flockinator-T-joint-v2.step`; its provenance and physical fit report remain there. These generated parts/scripts are GPL-3.0-or-later, continuing the T interface license. The downloaded lual model under CC BY-NC-SA remains a separately attributed reference in `../box-reference-lual`; none of its mesh is incorporated in these CAD parts. The speaker reference envelope dimensions trace to the owner measurements and Francois Stander model recorded in `../speaker-reference`.
