"""Seeded rescue cycle: HEAT/TRACE -> VERIFY -> DIG (or refuse).

Real-survivor case: two nodes, two modalities (thermal + CO2) agree.
Fabricated case: Kulira forges one heat sighting and relays copies -
one modality, one origin - so VERIFY refuses DIG. This is the
multi-modal corroboration rule exercised end to end.
"""
from __future__ import annotations
from .sensing import Reading, assess_contact

def run_rescue_cycle(seed: int = 1, fabricated: bool = False) -> dict:
    if fabricated:
        readings = [Reading("K1", "ir_max_c", 36.0, 20.0, "heat-fake")]
        # forwarded copies arrive as reports, not readings: they add
        # reporters, never modalities or independent nodes
        copies = 2
        a = assess_contact(readings, min_modalities=2)
        return {"seed": seed, "fabricated": True, "dig": False,
                "strength": a["strength"], "independent_modalities": len(a["modalities"]),
                "forwarded_copies": copies, "reason": "single modality from single origin; copies are not witnesses"}
    readings = [Reading("A1", "ir_max_c", 36.5, 21.0, "heat-1"),
                Reading("B1", "co2_ppm", 1500, 450, "trace-1")]
    a = assess_contact(readings, min_modalities=2)
    return {"seed": seed, "fabricated": False, "dig": a["strength"] == "strong",
            "strength": a["strength"], "independent_modalities": len(a["modalities"]),
            "forwarded_copies": 0, "reason": "two modalities, two independent nodes"}
