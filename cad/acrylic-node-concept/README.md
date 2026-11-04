# Acrylic-mounted node and rear speaker concept

Official controller dimensions and component-location diagrams are now retained
in [controller-reference](../controller-reference/README.md). The concept's generic
controller block and side ports still require replacement using the actual
panel-to-HUB75 registration; they are not ready-to-print interface locations.

27 October 2026. Visual concept created through FreeCAD MCP, not a fabrication release.

Open `Flockinator-raised-5mm.FCStd` for the current complete sixteen-node
assembly with panel faces 5 mm above the channels. `Flockinator-flush-reference.FCStd`
preserves the level-face comparison. `Flockinator-acrylic-node-concept.FCStd`
is the earlier flush assembly. `Exploded-node-concept.FCStd` is the earlier exploded detail. The full
assembly also contains an initially hidden ExplodedNode group. PNG previews show
the front perspective, rear and exploded module.

## Proposed stack

All dimensions are millimetres. XY is the display plane; +Z faces the audience.

| Feature | Trial geometry |
|---|---|
| Acrylic carrier | Four 429.25 × 429.25 × 6 tiles, 860 overall, R30 external corners |
| Tile seams | 1.5 mm along central horizontal/vertical lighting paths |
| Node grid | 4 × 4, 200 centre pitch, 160 × 160 panel faces |
| Carrier-to-tray standoffs | 12 long, Z6–18 |
| Ventilated tray | 160 × 160 × 45, 3 mm nominal walls/base |
| Panel / pixel diffuser | Panel Z68–73; diffuser Z74–77; 5 mm proud of channel face |
| Panel riser | 5 mm perimeter ring above original tray, fixing details provisional |
| Track | 35.8 wide, base Z48–70, cover Z70–72 |
| Outer track corners | Centreline R20; outside R37.9, inside R2.1 |
| Speaker chamber | 116 × 62 × 30, rear-facing slotted grille |
| Speaker proxy | 99.5 × 44.8 × 21.3, retaining existing housing |
| Acrylic speaker opening | 104 × 50 per node |
| Rear support | Perimeter frame, trial 20 × 25 section |
| Cross reinforcement | Hollow 20 × 25 × 2 aluminium trial section, with seam saddle plates |

The rear cross supports all four inner tile edges and joins the perimeter frame.
The horizontal arms stop at the continuous vertical member. Saddle plates span
the seams, with a separate fastening position in each tile. Perimeter pads
support the outer tile edges. All frame, brace and saddle shapes clear the XY
projections of the sixteen speaker openings. Four tile solids are valid and
connected. These are placement checks, not load ratings: joints, fastener access,
compliant interfaces, tube-wall bearing and resistance to frame racking need
engineering. No diagonal bracing or rigid joint performance is established.

The track bases sit on discrete pedestals attached to the acrylic. Nodes and
tracks have independent support. Speaker chambers occupy the lower portion of
each tray; green blocks reserve controller space. Vent slots are shown on two
opposite walls; side openings suggest USB/power and microphone access. Their
locations and sizes are placeholders, not measured port interfaces. Mounting
holes are conceptual and do not yet implement the owner-confirmed panel pattern.

## Limits

- Valid shape checks passed for all generated objects, as recorded in validation.json.
  This is not a collision-free assembly certification or structural calculation.
- The channel and cover each form one connected solid with rounded outer
  corners and merged T/cross junctions. Printable section seams,
  LED strips, retention, cabling and purchased-track fit remain unresolved.
- Pixel texture is illustrative 32 × 32, not actual 64 × 64 optical tooling.
- Panel/electronics thicknesses and spacing, carrier thickness, frame attachment,
  speaker retention and connector clearances need physical measurements.
- No screws, wire harnesses, power enclosure, feet or world controller are modelled.
- Cooling, sound quality, vibration and acrylic load capacity remain untested.
- Speaker openings and ventilation are separated in concept; acoustic sealing
  around the grille/chamber still needs detailing.

`build_concept.py` is the dimensional source, executed inside FreeCAD via MCP.
Objects are generated solids, not a fully constrained sketch-based design.

The 5 mm variant was generated from the saved flush reference using
`make_raised_variant.py` in FreeCAD's bundled runtime after GUI dispatch stalled.
`render_raised_freecad.py` produces its CAD previews. Validation checks all sixteen
diffuser faces at Z77 against the channel face at Z72. Riser fixing details remain
provisional. The current builder also includes the 5 mm change for future regeneration.
