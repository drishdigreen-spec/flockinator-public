# CAD - finished models

Finished, reproducible models only. Iteration drafts and fit studies
live in the project's private archive; their results are the recorded
parameters in [../docs/hardware.md](../docs/hardware.md).

| Model | Description |
|---|---|
| `Flockinator-grid-fit.FCStd` | Full 4x4 layout, 250 mm pitch, purchased track/diffuser meshes, sixteen 160x160 mm panels |
| `Flockinator-compact-fit.FCStd` | Compact 199.8 mm pitch candidate, 875 mm backing envelope |
| `acrylic-node-concept/` | Current acrylic panel-face appearance direction |
| `conductor-7inch/terminal-fresh-v6/` | Finished 7-inch controller terminal |
| `conductor-7inch/sensor-deck-v7/` | Finished shared sensor deck |
| `perimeter-speakers/border-v3/` | Finished perimeter speaker border release |
| `panel-hole-review/` | Measured mounting-hole dimensions |

Regenerate with `build_grid.py` / `build_compact_grid.py` in FreeCAD's
runtime (`show_grid.FCMacro` applies presentation colours). Models are
layout/fabrication sources at the stated maturity: panel-face spacing
and counts are validated; fasteners, connector bend clearance, and
thermal/acoustic details must be confirmed against real hardware
before production printing.
