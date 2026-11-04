# Official P2.5 resource review — 28 October 2026

Reviewed the current Waveshare documentation and its linked official repository.
Re-ran `extract_drawing.py`: all eight edge M3 locations and four corner feature
centres match the existing audited register. The panel repository HEAD remains
413a8e04db2e46365b9b1922fa6db79c75afd01f, matching the retained drawing source.

The actual DWG was rendered to `official-drawing-review.png` and visually inspected.
Its title identifies a **160 × 160 P2.5 indoor bottom shell**. It shows front/rear
shell views, side/section views, nominal 159.8 ± 0.1 mm shell width/height, a 12 mm
shell depth dimension, 146 mm edge mounting span and 145 mm corner-feature span.
The edge fastener annotation is M3×6. These refer to the bare shell and its
interfaces, not a complete powered node or safe screw length through an added case.

Crucially, this drawing does **not** show the assembled power connectors, plugged-in
cable/latch envelope or controller board. Do not use 12 mm as the full panel plus
electronics depth. Existing proof of bracket fit is retained; the new node-case
concept still contains placeholder holes and must adopt the audited coordinates.

Waveshare's current P2.5 specification confirms nominal 160 × 160 mm, 64 × 64,
2.5 mm pitch, 5 V / 4 A via VH4 input. It separately identifies two HUB75 data
headers. The owner's report of two physical power sockets is retained, but neither
parallel wiring nor pass-through current capacity is established by this shell drawing.

The current panel resource page links a 2D DWG directory containing P2, P2.5 and
P3 drawings. The controller resource page links its schematic and 2D project
drawing. No official panel 3D assembly link was located in those pages during this
review. This does not establish that no 3D model exists; a located model must be
checked for exact P2.5 version and inclusion of connectors before adoption.

Sources:
- https://docs.waveshare.com/RGB-Matrix-Px-64x64
- https://docs.waveshare.com/RGB-Matrix-Px-64x64/Resources-And-Documents
- https://github.com/waveshareteam/RGB-Matrix-Px-xx/tree/main/hardware/dimensions/RGB-Matrix-Pxx-64x64
- https://docs.waveshare.com/ESP32-S3-RGB-Matrix/Resources-And-Documents

No manufacturing files were released or assembly dimensions silently changed.
