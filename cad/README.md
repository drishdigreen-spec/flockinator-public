# CAD - models and measured parameters

Models and the measured parameters they encode. Build/verify scripts,
draft variants, and validation logs live in the project's private
archive. Maturity is stated per model and is part of the record.

| Model | Maturity | Description |
|---|---|---|
| `Flockinator-grid-fit.FCStd` | Layout study | Full 4x4 layout, 250 mm pitch, sixteen 160x160 mm panels. **Contains purchased track/diffuser meshes; envelope-only redistribution is pending (issue #61) - do not redistribute this file until replaced.** |
| `Flockinator-compact-fit.FCStd` | Layout candidate | Compact 199.8 mm pitch candidate, 875 mm backing envelope. Same mesh note as above. |
| `acrylic-node-concept/` | Appearance direction | Current acrylic panel-face concept |
| `conductor-7inch/terminal-fresh-v6/` | Engineering study | 7-inch controller terminal; not hardware-fit or slicer verified. Text inlay geometry derives from a proprietary font; OFL substitution pending (issue #61) |
| `conductor-7inch/sensor-deck-v7/` | Prototype provision | Shared sensor deck; insert STLs are prototypes, not a fitted-sensor release |
| `perimeter-speakers/border-v3/` | Geometric prototype | Perimeter speaker border; not sliced or physically fitted |
| `panel-hole-review/` | Measured parameters | Mounting-hole coordinates and 1:1 template extracted from manufacturer drawings (source drawings not redistributed) |

Models are layout/fabrication sources at the stated maturity:
panel-face spacing and counts are validated; fasteners, connector
bend clearance, and thermal/acoustic details must be confirmed
against real hardware before production printing.
