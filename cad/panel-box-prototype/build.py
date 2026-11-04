"""One-node panel box prototype: registered panel, real controller envelope,
proven speaker cradle + removable clips, short track section with screw tabs.

Run: freecadcmd build.py   (FreeCAD 1.1.4 verified)
Status: prototype for one-node owner fit test. NOT a production release.
Controller XY follows HUB75_CENTRE in parameters.py (provisional until measured).
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
doc = A.newDocument("PanelBoxPrototype")
MADE = []  # (name, shape, printable)


def box(x, y, z, w, h, d):
    return Part.makeBox(w, h, d, A.Vector(x, y, z))


def cyl(x, y, z, r, h, axis=(0, 0, 1)):
    return Part.makeCylinder(r, h, A.Vector(x, y, z), A.Vector(*axis))


def add(name, shape, printable=False):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    MADE.append((name, shape, printable))
    return o


def export_stl(name, shape):
    MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.08,
                           AngularDeflection=0.15, Relative=False).write(
        str(HERE / "stl" / (name + ".stl")))


# Z datum: tray rear outer face Z=0, audience toward +Z. Panel front at BOX_DEPTH.
inner_z0 = BOX_BASE_T
panel_rear_z = BOX_DEPTH - PANEL_SHELL_DEPTH  # panel shell occupies top 12 mm

# --- Tray: 160 square shell, 3 mm walls/base, rear speaker opening 104x50 ---
tray = box(-80, -80, 0, BOX_OUTER, BOX_OUTER, BOX_DEPTH).cut(
    box(-77, -77, BOX_BASE_T, 154, 154, BOX_DEPTH))
tray = tray.cut(box(-SPEAKER_OPENING[0] / 2, -50 - SPEAKER_OPENING[1] / 2, -1,
                    SPEAKER_OPENING[0], SPEAKER_OPENING[1], BOX_BASE_T + 2))
# Eight M3 standoff bosses fused to tray base, at audited panel coordinates:
for hx, hy in M3_EDGE:
    tray = tray.fuse(cyl(hx, hy, inner_z0, 4.0, panel_rear_z - inner_z0).cut(
        cyl(hx, hy, inner_z0 - 1, 1.4, panel_rear_z - inner_z0 + 2)))
# Service cutouts on +X wall (positions follow controller datum; provisional):
tray = tray.cut(box(76, 18, 10, 8, 26, 14))   # programming USB-C sweep
tray = tray.cut(box(76, -30, 10, 8, 34, 12))  # SD removal sweep
# Rev 2 vents: segmented horizontal slots on both Y walls. Vertical ribs
# (VENT_RIB_W) cap every bridge at VENT_SLOT_W; internal 1.6 mm ribs behind
# the band tie the ribs to the wall so the grille cannot droop as one span.
for sgn in (1, -1):
    y_in = 77 if sgn > 0 else -77  # inner wall face
    for c in range(VENT_COLS - 1):
        rx = VENT_X0 + VENT_SLOT_W + VENT_RIB_W / 2 + c * (VENT_SLOT_W + VENT_RIB_W)
        tray = tray.fuse(box(rx - INNER_RIB_T / 2,
                             min(y_in, y_in - sgn * INNER_RIB_PROTRUDE), 10,
                             INNER_RIB_T, INNER_RIB_PROTRUDE, 25))
    for c in range(VENT_COLS):
        sx = VENT_X0 + c * (VENT_SLOT_W + VENT_RIB_W)
        for vz in VENT_ROWS_Z:
            tray = tray.cut(box(sx, 76 if sgn > 0 else -81, vz,
                                VENT_SLOT_W, 5, VENT_SLOT_H))
tray = tray.removeSplitter()
add("Node_tray_PROTOTYPE", tray, printable=True)

# --- Panel shell reference + audited holes (shown as tray standoff bosses) ---
panel = box(-PANEL_SHELL / 2, -PANEL_SHELL / 2, panel_rear_z,
            PANEL_SHELL, PANEL_SHELL, PANEL_SHELL_DEPTH)
for hx, hy in M3_EDGE + CORNER_FEATURES:
    panel = panel.cut(cyl(hx, hy, panel_rear_z - 1, 1.6, PANEL_SHELL_DEPTH + 2))
add("Panel_shell_REFERENCE", panel.removeSplitter())

# --- Riser: 5 mm raised face ring ---
riser = box(-80, -80, BOX_DEPTH, 160, 160, RISER_H).cut(
    box(-77, -77, BOX_DEPTH - 1, 154, 154, RISER_H + 2))
add("Panel_riser_5mm_PROTOTYPE", riser.removeSplitter(), printable=True)

# --- Controller: real PCB outline at HUB75 datum (PROVISIONAL placement) ---
cx, cy = HUB75_CENTRE
pcb_z = panel_rear_z - HUB75_ENGAGE - CTRL_PCB_T
pcb = box(cx - CTRL_PCB[0] / 2, cy - CTRL_PCB[1] / 2, pcb_z,
          CTRL_PCB[0], CTRL_PCB[1], CTRL_PCB_T)
for mx in (-CTRL_MOUNT_SPACING / 2, CTRL_MOUNT_SPACING / 2):
    pcb = pcb.cut(cyl(cx + mx, cy, pcb_z - 1, 1.4, CTRL_PCB_T + 2))
add("Controller_PCB_50x42_PROVISIONAL", pcb.removeSplitter())
keep_a = box(cx - CTRL_PCB[0] / 2, cy - CTRL_PCB[1] / 2, pcb_z - CTRL_COMP_A,
             CTRL_PCB[0], CTRL_PCB[1], CTRL_COMP_A)
add("Controller_keepout_8p5_PROVISIONAL", keep_a)
keep_b = box(cx - CTRL_PCB[0] / 2, cy - CTRL_PCB[1] / 2, pcb_z + CTRL_PCB_T,
             CTRL_PCB[0], CTRL_PCB[1], CTRL_COMP_B)
add("Controller_keepout_5p6_PROVISIONAL", keep_b)
plug = box(cx - POWER_PLUG_BOX[0] / 2, cy - 40 - POWER_PLUG_BOX[1] / 2,
           pcb_z - POWER_PLUG_BOX[2], *POWER_PLUG_BOX)
add("Power_plug_clearance_MUST_MEASURE", plug)

# --- Forward ToF pod: top-centre of riser, sensor looking +Z ---
pod_y, pod_z = 80 - TOF_POD_H / 2, BOX_DEPTH + RISER_H
pod = box(-TOF_POD_W / 2, pod_y - TOF_POD_H / 2, pod_z, TOF_POD_W, TOF_POD_H, TOF_POD_D)
pod = pod.cut(box(-TOF_POD_W / 2 + 2, pod_y - TOF_POD_H / 2 + 2, pod_z + 2,
                  TOF_POD_W - 4, TOF_POD_H - 4, TOF_POD_D))
pod = pod.cut(box(-TOF_WINDOW_W / 2, pod_y - TOF_WINDOW_H / 2, pod_z + TOF_POD_D - 3,
                  TOF_WINDOW_W, TOF_WINDOW_H, 5))
pod = pod.cut(box(-6, pod_y - TOF_POD_H / 2 - 1, pod_z - 4, 12, 6, 5))  # cable entry
add("ToF_pod_PROTOTYPE", pod.removeSplitter(), printable=True)
carrier = box(-TOF_CARRIER_W / 2, pod_y - TOF_CARRIER_D / 2, pod_z + 3,
              TOF_CARRIER_W, TOF_CARRIER_D, TOF_CARRIER_T)
for ry in (-4, 4):
    carrier = carrier.cut(box(-11, pod_y + ry - 1.5, pod_z + 2, 22, 3, TOF_CARRIER_T + 2))
add("ToF_carrier_GENERIC", carrier.removeSplitter(), printable=True)
board = box(-TOF_BOARD_MAX[0] / 2, pod_y - TOF_BOARD_MAX[1] / 2, pod_z + 5, *TOF_BOARD_MAX)
add("ToF_board_MUST_MEASURE", board)

# --- Speaker cradle: proven posts (guide geometry) on two rails ---
spk_cy = -50.0  # speaker centre Y; clear of controller keep-out (cy +/- 21)
cradle = box(-51, spk_cy - 22, inner_z0, 102, 8, 3).fuse(
    box(-51, spk_cy + 14, inner_z0, 102, 8, 3)).fuse(
    box(-4, spk_cy - 22, inner_z0, 8, 44, 3))
for px in (-SPEAKER_POST_PATTERN[0] / 2, SPEAKER_POST_PATTERN[0] / 2):
    for py in (-SPEAKER_POST_PATTERN[1] / 2, SPEAKER_POST_PATTERN[1] / 2):
        cradle = cradle.fuse(cyl(px, spk_cy + py, inner_z0 + 2,
                                 SPEAKER_SHOULDER_D / 2, SPEAKER_SHOULDER_H - 2))
        cradle = cradle.fuse(cyl(px, spk_cy + py, inner_z0 + SPEAKER_SHOULDER_H,
                                 SPEAKER_POST_D / 2, 4))
        cradle = cradle.fuse(Part.makeCone(
            SPEAKER_POST_D / 2, 2.4, 1,
            A.Vector(px, spk_cy + py, inner_z0 + SPEAKER_SHOULDER_H + 4)))
cradle = cradle.removeSplitter()
add("Speaker_cradle_92x36_D5p6_PROTOTYPE", cradle, printable=True)
speaker = box(-SPEAKER_BODY[0] / 2, spk_cy - SPEAKER_BODY[1] / 2,
              inner_z0 + 3, *SPEAKER_BODY)
add("Speaker_body_REFERENCE", speaker)

# --- Removable clip: separate part, 2.1 capture gap over 1.9 lug ---
clip = box(0, 0, 0, 18, 12, 3).fuse(box(0, 0, 3, 3, 12, CLIP_GAP)).fuse(
    box(0, 0, 3 + CLIP_GAP, 18, 12, 3)).fuse(box(15, 0, 3, 3, 12, CLIP_GAP))
clip = clip.removeSplitter()
add("Speaker_clip_gap2p1_PROTOTYPE_x1of4", clip, printable=True)
for px in (-SPEAKER_POST_PATTERN[0] / 2, SPEAKER_POST_PATTERN[0] / 2):
    placed = clip.copy()
    placed.translate(A.Vector(px - 9, spk_cy - 24, inner_z0 + SPEAKER_SHOULDER_H))
    add("Speaker_clip_PLACED", placed)

# --- Short track section + screw tabs to tray bosses ---
track = box(-100, 88, 0, 200, TRACK_W, 22).cut(box(-100, 91, 3, 200, 29.8, 22))
tabs = []
for tx in (-60, 0, 60):
    tab = box(tx - 9, 76, 0, 18, 14, 3).cut(cyl(tx, 82, -1, 1.7, 5))
    tabs.append(tab)
    track = track.fuse(tab)
add("Track_section_screwtabs_PROTOTYPE", track.removeSplitter(), printable=True)
cover = box(-100, 88, 22, 200, TRACK_W, 2)
add("Track_cover_REFERENCE", cover)

doc.recompute()
for name, shape, printable in MADE:
    assert shape.isValid() and shape.Volume > 0, name
    if printable:
        export_stl(name, shape)
doc.saveAs(str(HERE / "Panel-box-prototype.FCStd"))
Part.export(list(doc.Objects), str(HERE / "Panel-box-prototype.step"))
print(f"OK: {len(MADE)} solids valid; STLs in {HERE / 'stl'}")
