# Dark-beige desktop enclosure v3 - print prototype

This is a printable enclosure prototype, **not a verified complete hardware enclosure**. The v1.6 board, full touch assembly, display retention, actual port alignment and cable reach have not been measured. Do not install powered electronics unsecured in this prototype.

## Included

- `Conductor-7inch-dark-beige-v3.FCStd`: CAD assembly in dark beige. Colour is visual only; select your own dark-beige filament in Bambu Studio.
- `Conductor-7inch-dark-beige-v3.STEP`: housing and base only.
- `stl/ScreenApertureFitGauge.stl`: print first. 165 x 98 x 1.2 mm gauge with provisional 156 x 88 mm opening. It tests the opening and edge relationships only, not the complete display outer envelope, retention or PCB alignment. Do not force it against the glass.
- `stl/BeigeUpperHousing.stl`: 195 x 154.03 x 76.14 mm in the exported printing orientation, front/bezel face towards bed. Requires support review in slicer. Open-bottom shell, integrated upper bezel, rear port bay, side speaker grille, corner screw towers.
- `stl/RemovableSlottedBase.stl`: 195 x 132.32 x 3 mm, flat on bed. Generic slotted field for future measured mounting, not an established PCB-hole pattern.

## Prototype printing sequence

1. Print and inspect the aperture gauge before the housing. Verify the opening does not obscure the active image or conflict with touch glass/frame. Record actual outer glass dimensions and offsets.
2. Confirm your printer's usable bed can accommodate each part; 195 mm width will not fit a 180 mm bed as oriented. No printer model was specified.
3. For a 0.4 mm nozzle, 0.20 mm layers and four walls are reasonable starting settings; use the filament manufacturer's material profile. Review supports under the housing's internal towers/ledges and all bridges in Bambu Studio. Colour alone does not identify PLA/PETG or determine temperatures.
4. Base screw holes are 3.4 mm clearance; towers have 2.6 mm x approximately 12 mm pilot bores for trial M3 plastic-tapping fasteners. These are not threaded or heat-insert holes. Choose screw length from actual engagement and test first; do not force machine screws or run a screw into the screen area. Fasteners are provisional.
5. Finalise display retention, insulated PCB standoffs, speaker mount, port alignment and cable routes before treating this as an operational case. Speaker is an allocated space, not a completed cradle. Keep electronics insulated from loose fasteners.

## Changes from v2

Sensors, camera hole and camera volumes removed for now. Dark-beige appearance. Flat-board arrangement retained. Bottom plate removes for service. Screen remains 25 degrees above desk. Upper shell and base have zero volume overlap; bare LCD reference clears the shell. Exported meshes passed FreeCAD mesh solid checks. Hardware fit, print slicing, first-layer stability, supports, thermal behaviour and physical strength are not validated.

See `checks.json` for exported bounds and checks. `build.py` regenerates in FreeCAD's bundled runtime. The saved model contains a bare LCD reference for visual context; the STEP/STLs exclude electronics.
