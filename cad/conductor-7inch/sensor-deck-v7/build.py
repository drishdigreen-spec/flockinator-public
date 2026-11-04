"""Sensor deck v7: replaceable carrier for the v6 sloped deck (15 deg).
Plate lies in XY here; tilt by DECK_ANGLE_DEG when fitting to the housing.
Run: freecadcmd build.py. Prototype provision, not a fitted-sensor release.
"""
import sys
from pathlib import Path

sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
import FreeCAD as A
import Part
import MeshPart

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from parameters import *  # noqa: E402,F403

(HERE / "stl").mkdir(exist_ok=True)
doc = A.newDocument("SensorDeckV7")
MADE = []
HOLES = [(x, y) for x in (-25.8, 25.8) for y in (-14.8, 14.8)]
WIN_W, WIN_D = BAY_W - 8, BAY_D - 8


def box(x, y, z, w, h, d):
    return Part.makeBox(w, h, d, A.Vector(x, y, z))


def cyl(x, y, z, r, h):
    return Part.makeCylinder(r, h, A.Vector(x, y, z))


def add(name, shape, printable=False):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    MADE.append((name, shape, printable))
    return o


def export(name, shape):
    MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.08,
                           AngularDeflection=0.15, Relative=False).write(
        str(HERE / "stl" / (name + ".stl")))


def with_holes(s):
    for hx, hy in HOLES:
        s = s.cut(cyl(hx, hy, -1, INSERT_SCREW_D / 2, INSERT_T + 2))
    return s.removeSplitter()


def insert_base():
    return box(-INSERT_W / 2, -INSERT_D / 2, 0, INSERT_W, INSERT_D, INSERT_T)


# Carrier plate: ledged bays (window < insert), ARGB channel, cable slot.
plate = box(-PLATE_W / 2, -PLATE_D / 2, 0, PLATE_W, PLATE_D, PLATE_T)
for bx in BAY_XS:
    plate = plate.cut(box(bx - WIN_W / 2, -WIN_D / 2, -1, WIN_W, WIN_D, PLATE_T + 2))
    for hx, hy in HOLES:
        plate = plate.cut(cyl(bx + hx, hy, -1, INSERT_SCREW_D / 2, PLATE_T + 2))
plate = plate.cut(box(-PLATE_W / 2 + 8, PLATE_D / 2 - ARGB_CHANNEL_D - 2, 1.2,
                      PLATE_W - 16, ARGB_CHANNEL_W, PLATE_T))
plate = plate.cut(box(-CABLE_SLOT_W / 2, -PLATE_D / 2 - 1, -1,
                      CABLE_SLOT_W, CABLE_SLOT_D, PLATE_T + 2))
add("Deck_carrier_PROTOTYPE", plate.removeSplitter(), printable=True)

add("Insert_blank_TEMPLATE", with_holes(insert_base()), printable=True)

vented = insert_base()
for r in range(VENT_ROWS):
    vz = -INSERT_D / 2 + 6 + r * 7
    for sx in (-24, -8, 8):
        vented = vented.cut(box(sx, vz, -1, VENT_SLOT_W, VENT_SLOT_H, INSERT_T + 2))
add("Insert_env_vented_PROTOTYPE", with_holes(vented), printable=True)

radome = insert_base()
for px in (-20, 20):
    radome = radome.fuse(cyl(px, 0, -6, 3, 6).cut(cyl(px, 0, -7, 1.4, 8)))
add("Insert_mmwave_radome_PROTOTYPE", with_holes(radome), printable=True)

rail = insert_base()
for ry in (-9, 9):
    rail = rail.cut(box(-22, ry - 2, -1, 44, 4, INSERT_T + 2))
add("Insert_module_rail_PROTOTYPE", with_holes(rail), printable=True)

diffuser = box(-PLATE_W / 2 + 8, PLATE_D / 2 - ARGB_CHANNEL_D - 2, 1.2,
               PLATE_W - 16, ARGB_CHANNEL_W, ARGB_DIFFUSER_T)
add("ARGB_diffuser_PROTOTYPE", diffuser, printable=True)

doc.recompute()
for name, shape, printable in MADE:
    assert shape.isValid() and shape.Volume > 0, name
    if printable:
        export(name, shape)
doc.saveAs(str(HERE / "Sensor-deck-v7.FCStd"))
Part.export(list(doc.Objects), str(HERE / "Sensor-deck-v7.step"))
print(f"OK: {len(MADE)} solids valid; STLs in {HERE / 'stl'}")
