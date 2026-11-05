# CAD - models and measured parameters

Models and the measured parameters they encode. Build/verify scripts,
draft variants, and validation logs live in the project's private
archive. Maturity is stated per model and is part of the record.

| Model | Maturity | Description |
|---|---|---|
| `Flockinator-grid-fit.FCStd` | Layout study | Full 4x4 layout, 250 mm pitch, sixteen 160x160 mm panels. **Panel envelopes only:** purchased track/diffuser meshes were stripped from this file on 2026-11-06 (issue #61; owner-authored panels, adaptations and rear-space solids retained). Preview renders elsewhere may still show the full purchased track assembly. |
| `Flockinator-compact-fit.FCStd` | Layout candidate | Compact 199.8 mm pitch candidate, 875 mm backing envelope. Panel envelopes only; purchased meshes stripped as above (issue #61). |
| `acrylic-node-concept/` | Appearance direction | Current acrylic panel-face concept |
| `conductor-7inch/terminal-fresh-v6/` | Engineering study | 7-inch controller terminal; not hardware-fit or slicer verified. Text inlay regenerated 2026-11-06 from JetBrains Mono (SIL Open Font License 1.1, `FONT-LICENSE-OFL.txt`), replacing the previous proprietary-font geometry (issue #61); wordmark width changed with the font metrics. The pre-substitution render was removed. |
| `speaker-fit-guide/` | Fit tested | Speaker post/lug-gap fit gauges, revision 2 (92x36 mm, D5.6 posts; owner-reported perfect fit 2026-10-28). See `FIRST-PRINT.md` in the directory. |
| `conductor-7inch/sensor-deck-v7/` | Prototype provision | Shared sensor deck; insert STLs are prototypes, not a fitted-sensor release |
| `perimeter-speakers/border-v3/` | Geometric prototype | Perimeter speaker border; not sliced or physically fitted |
| `panel-hole-review/` | Measured parameters | Mounting-hole coordinates and 1:1 template extracted from manufacturer drawings (source drawings not redistributed) |

Models are layout/fabrication sources at the stated maturity:
panel-face spacing and counts are validated; fasteners, connector
bend clearance, and thermal/acoustic details must be confirmed
against real hardware before production printing.
