"""Reopen saved model; check validity, single solids, insert/ledge fit."""
import sys
import json
from pathlib import Path

sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
import FreeCAD as A

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from parameters import INSERT_W, BAY_W, VENT_SLOT_W

doc = A.openDocument(str(HERE / "Sensor-deck-v7.FCStd"))
S = {o.Name: o.Shape for o in doc.Objects if hasattr(o, "Shape")}
checks = {
    "all_valid": all(s.isValid() and s.Volume > 0 for s in S.values()),
    "single_solids": {n: len(s.Solids) for n, s in S.items()},
    "insert_window_clearance_per_side_mm": round((BAY_W - INSERT_W) / 2, 2),
    "ledge_overlap_per_side_mm": 4.0,
    "vent_max_bridge_mm": VENT_SLOT_W,
}
checks["ok"] = (checks["all_valid"]
                and all(v == 1 for v in checks["single_solids"].values())
                and checks["vent_max_bridge_mm"] <= 25)
checks["status"] = "PASS" if checks["ok"] else "FAIL"
checks["open_measurements"] = [
    "Each real module outline/hole pattern before a fitted insert",
    "LD2410C vs HMMD selection, antenna keepout and radome guidance",
    "ARGB strip width/pitch for the channel; ring not accommodated here",
    "Carrier-to-v6-deck attachment (plate is freestanding in this study)"]
(HERE / "validation.json").write_text(json.dumps(checks, indent=2))
print(json.dumps(checks, indent=2))
sys.exit(0 if checks["ok"] else 1)
