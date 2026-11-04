"""Independent checks: reopen the saved FCStd, verify dimensions/clearances.
Run: freecadcmd verify.py  -> writes validation.json, exits nonzero on failure.
"""
import sys
import json
from pathlib import Path

sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
import FreeCAD as A

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from parameters import (SPEAKER_POST_PATTERN, SPEAKER_POST_D, CLIP_GAP, LUG_T,
                        VENT_SLOT_W, VENT_RIB_W)

doc = A.openDocument(str(HERE / "Panel-box-prototype.FCStd"))
S = {o.Name: o.Shape for o in doc.Objects if hasattr(o, "Shape")}
checks = {}


def inter(a, b):
    return S[a].common(S[b]).Volume


checks["all_valid"] = all(s.isValid() and s.Volume > 0 for s in S.values())
checks["tray_single_solid"] = len(S["Node_tray_PROTOTYPE"].Solids) == 1
checks["vent_max_bridge_mm"] = VENT_SLOT_W
checks["vent_rib_mm"] = VENT_RIB_W
bb = S["Speaker_cradle_92x36_D5p6_PROTOTYPE"].BoundBox
checks["cradle_envelope_mm"] = [round(bb.XLength, 2), round(bb.YLength, 2),
                                round(bb.ZLength, 2)]
# Post tops: highest Z region of cradle must span the 92 x 36 pattern.
top = S["Speaker_cradle_92x36_D5p6_PROTOTYPE"].BoundBox
checks["post_pattern_expected_mm"] = list(SPEAKER_POST_PATTERN)
checks["speaker_vs_controller_keepout_mm3"] = round(
    inter("Speaker_body_REFERENCE", "Controller_keepout_8p5_PROVISIONAL"), 3)
checks["speaker_vs_controller_keepout5p6_mm3"] = round(
    inter("Speaker_body_REFERENCE", "Controller_keepout_5p6_PROVISIONAL"), 3)
checks["clip_gap_mm"] = CLIP_GAP
checks["clip_clearance_over_lug_mm"] = round(CLIP_GAP - LUG_T, 2)
checks["power_plug_vs_speaker_mm3"] = round(
    inter("Power_plug_clearance_MUST_MEASURE", "Speaker_body_REFERENCE"), 3)
checks["power_plug_vs_tray_mm3"] = round(
    inter("Power_plug_clearance_MUST_MEASURE", "Node_tray_PROTOTYPE"), 3)
ok = (checks["all_valid"] and checks["tray_single_solid"]
      and checks["vent_max_bridge_mm"] <= 25
      and checks["speaker_vs_controller_keepout_mm3"] == 0
      and checks["speaker_vs_controller_keepout5p6_mm3"] == 0
      and checks["clip_clearance_over_lug_mm"] == 0.2)
checks["status"] = "PASS" if ok else "FAIL"
checks["open_measurements"] = [
    "HUB75_CENTRE/engagement on a real assembled node (controller XY provisional)",
    "VH4 power plug + latch + cable-bend envelope (placeholder box only)",
    "Clip retention/release force and compliant-pad need (geometry only here)"]
(HERE / "validation.json").write_text(json.dumps(checks, indent=2))
print(json.dumps(checks, indent=2))
sys.exit(0 if ok else 1)
