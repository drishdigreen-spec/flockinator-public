"""Single-node panel-box prototype parameters (mm).

Sources:
- Panel holes/shell: cad/panel-hole-review/panel-hole-coordinates.json (audited DWG).
- Controller PCB: cad/controller-reference (official 50.01 x 42, M2.5 at 42.54).
- Speaker: owner-measured 99.6 x 44.5 x 21, lugs 1.9; proven guide 92 x 36 / D5.6.
HUB75 datum and power-plug envelope are NOT dimensioned in any retained source:
they stay parameters to fill from a physical measurement before any print release.
"""

# --- Panel (audited) ---
PANEL_SHELL = 159.8          # +/-0.1, bottom-shell drawing
PANEL_SHELL_DEPTH = 12.0     # shell only, not assembled stack
PANEL_NOMINAL = 160.0
M3_EDGE = [(45, 73), (-45, 73), (73, 45), (-73, 45),
           (73, -45), (-73, -45), (45, -73), (-45, -73)]  # relative to centre
CORNER_FEATURES = [(72.5, 72.5), (-72.5, 72.5), (72.5, -72.5), (-72.5, -72.5)]

# --- Controller (official outline; placement provisional) ---
CTRL_PCB = (50.01, 42.0)
CTRL_PCB_T = 1.6
CTRL_CORNER_R = 2.0
CTRL_MOUNT_SPACING = 42.54   # two M2.5 positions
CTRL_COMP_A = 8.5            # side-view projection, one face
CTRL_COMP_B = 5.6            # side-view projection, opposite face
# MUST MEASURE on a real assembled node before release:
HUB75_CENTRE = (0.0, 0.0)    # panel-relative XY of controller HUB75 socket centre
HUB75_ENGAGE = 8.0           # plug engagement depth behind panel rear face
CTRL_ROT_DEG = 0.0           # controller rotation in panel plane

# --- Power plug (unmeasured; clearance placeholder only) ---
POWER_PLUG_BOX = (30.0, 20.0, 25.0)  # MUST MEASURE: VH4 plug + latch + bend

# --- Speaker (owner-measured / physically fitted) ---
SPEAKER_BODY = (99.6, 44.5, 21.0)
SPEAKER_POST_PATTERN = (92.0, 36.0)  # proven perfect fit, 28 Oct 2026
SPEAKER_POST_D = 5.6
SPEAKER_SHOULDER_D = 9.0
SPEAKER_SHOULDER_H = 15.0
LUG_T = 1.9
CLIP_GAP = 2.1               # proposed capture gap (middle tested gauge)

# --- Prototype box (trial, inherits concept stack) ---
BOX_OUTER = 160.0
BOX_WALL = 3.0
BOX_BASE_T = 3.0
BOX_DEPTH = 45.0             # outer, front face to rear face
RISER_H = 5.0                # raised panel face above channel face
SPEAKER_OPENING = (104.0, 50.0)
TRACK_W = 35.8

# --- Forward ToF pod (owner direction 29 Oct 2026) ---
# $7 VL53-class laser ToF per node, looking +Z. 50/200/400 cm listings are
# different chips, not settings. Board outline varies by module: carrier is
# generic; measure one purchased unit before a fitted insert.
TOF_POD_W, TOF_POD_H, TOF_POD_D = 36.0, 16.0, 12.0
TOF_WINDOW_W, TOF_WINDOW_H = 14.0, 8.0   # open aperture, no cover glass
TOF_CARRIER_W, TOF_CARRIER_D, TOF_CARRIER_T = 30.0, 14.0, 2.0
TOF_BOARD_MAX = (28.0, 12.0, 6.0)        # placeholder envelope, MUST MEASURE

# --- Vents (rev 2, after owner print tip 29 Oct 2026) ---
# Fine horizontal slots drooped over long unsupported spans. Rev 2 segments
# every slot with vertical ribs and backs them with an internal rib grid.
# Longest unsupported bridge is VENT_SLOT_W (keep <= 25 mm).
VENT_SLOT_W = 12.0
VENT_SLOT_H = 3.5
VENT_RIB_W = 4.0      # vertical rib between slots (>= 1.6 mm min feature)
VENT_ROW_PITCH = 7.0
VENT_ROWS_Z = (14.0, 21.0, 28.0)
VENT_X0 = -60.0       # first slot left edge; slots step SLOT_W + RIB_W
VENT_COLS = 8
INNER_RIB_T = 1.6     # internal reinforcement ribs behind the vent band
INNER_RIB_PROTRUDE = 4.0
