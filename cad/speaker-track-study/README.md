# Speaker and lighting track envelope study

27 October 2026. Created in FreeCAD through MCP. Open
`Speaker-track-fit-study.FCStd`; `fit-study.png` is an isometric preview.

Three arrangements run from bottom-left to top-right in the preview:

1. Existing 200 mm pitch: 160 mm panel faces, 35.8 mm optical-track envelope,
   and the existing 116 × 62 × 40 mm speaker-case envelope rotated in plane.
   The case is 26.2 mm wider than the optical track. It overlaps the panel-face
   XY projection by 11 mm on each side. The speaker is placed ahead of the
   panel slab to reveal the projection conflict, not as a proposed installation.
2. Trial 230 mm pitch: optical width 65.8 mm. Only 3.8 mm total width remains
   around the case before any separate light lanes or dividers. This is not a
   resolved combined speaker/light track. Four-node centre span grows by 90 mm;
   the complete backing and outer border would need resizing.
3. Speaker behind a single panel: a depth-placement alternative only. Electronics,
   fixing points, grille/duct opening and acoustic path are unresolved.

Orange is the existing enclosure bounding box, charcoal is the full panel face,
and translucent cyan is the optical track envelope. All ten reference solids
passed FreeCAD shape validity and positive-volume checks. They are simple
envelopes, not imported detailed speaker parts or printable geometry. Panel
slab thickness and Z positions are illustrative and unmeasured.

The existing perimeter-border v3 remains another candidate and is preserved in
`../perimeter-speakers/border-v3/`. No pitch or speaker placement is selected by
this study. Next compare detailed speaker geometry with an actual panel/PCB
stack, and design independent optical and acoustic openings before releasing parts.
