# Seven-inch conductor: flat-board desktop concept v2

Created 28 October 2026 following the owner's requested separated layout.

Open `Conductor-7inch-flat-board-v2.FCStd` in FreeCAD. The saved view shows the internal arrangement with the screen and bezel hidden and base transparent. Toggle ScreenAndCameraBezel, BareLCDReference and ScreenSurface visible, and set WedgeBase transparency to 0 for the assembled view. STEP is also provided. Run `build.py` inside FreeCAD's bundled runtime to regenerate. No STL is provided because this is not fitted fabrication geometry.

## Proposed layout

- Envelope: 195 mm wide x 132.32 mm deep; shell front height 22 mm, rear 83.70 mm, excluding bezel and lens. Screen angle 25 degrees above desk.
- Angled display independent of main PCB.
- Flat PCB towards rear with permanent rear port bay, visible with enclosure assembled.
- Right-facing speaker behind side grille: owner-specified 31 x 31 x 15 mm body, conservative 44 mm ear envelope.
- Camera sensor above screen with separate internal camera adapter zone.
- Orange lines are schematic display, camera and power interconnect routes, not validated cable models.

## Colour key

Green flat board: EV board bounding reference. Grey blocks: component allowance and illustrative USB/Ethernet connectors. Orange speaker: measured body / translucent overall ear clearance. Purple: assumed camera adapter volume. Small green board at top: assumed camera sensor volume. Blue: screen reference.

## Limits

The main PCB uses the older drawing's 88 x 74 mm rectangular bound, not a traced or measured v1.6 board. Ports are illustrative and not actual registered connector coordinates. Camera sensor (24 x 24 x 6 mm) and adapter (30 x 30 x 3 mm) are expressly assumed planning volumes. Full touch glass, HMI adapter and connector stack are not modelled. Cable reach, bend radii, plug bodies, Ethernet latch access, antenna clearance and complete assembly fit remain unchecked. The camera currently follows the screen plane; operator-facing aim requires optical review. Speaker lead is not routed yet. No fitted mounts, enclosure fastening or closure features exist.

`checks.json` records valid single-solid checks for all model parts and nine major overlap checks. Valid geometry does not establish hardware fit. This model is for visual review only.

## Views

- `assembled.png`: exterior, screen, camera and side speaker grille.
- `internal-layout.png`: transparent shell, flat board, camera, speaker, schematic cable routes.
- `rear-ports.png`: assembled case rear access bay.
