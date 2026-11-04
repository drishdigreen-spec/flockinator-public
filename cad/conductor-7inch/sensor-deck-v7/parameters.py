"""Sensor deck v7 parameters (mm). Deck face from terminal-fresh-v6 Params:
slope 15 deg, slope run front_x -90..screen_base_x -35 (55 mm), width 235.
Module outlines are NOT dimensioned here: inserts are generic carriers.
Measure each real module (LD2410C, BME680, SCD41, Elegoo/Freenove boards)
before cutting a fitted insert; blanks are the template.
"""

DECK_ANGLE_DEG = 15.0        # v6 Params deck_angle
PLATE_W = 190.0              # across deck, centred on 235 body
PLATE_D = 44.0               # along slope; deck slope length ~56.9
PLATE_T = 3.0                # wall max in v6 brief range
BAY_W, BAY_D = 56.0, 34.0    # insert window
INSERT_W, INSERT_D, INSERT_T = 55.4, 33.4, 2.4  # 0.3 clearance per side
INSERT_SCREW_D = 3.4         # M3 clearance (+0.2 hole rule applied)
BAY_XS = (-62.0, 0.0, 62.0)  # three bay centres

# Vented env insert: segmented slots, ribs carry every bridge (rev-2 lesson
# from the node tray: fine unsupported spans droop).
VENT_SLOT_W, VENT_SLOT_H, VENT_RIB_W = 12.0, 3.0, 4.0
VENT_ROWS = 4

# ARGB: channel + separate diffuser bar along plate top edge.
ARGB_CHANNEL_W, ARGB_CHANNEL_D = 10.0, 4.0
ARGB_DIFFUSER_T = 2.0        # print translucent; strip width MUST MEASURE
CABLE_SLOT_W, CABLE_SLOT_D = 30.0, 6.0
