# Enclosure Design Brief — Retro Terminal Language

Design brief for AI agents producing 3D-printable enclosures for ESP32 / Raspberry Pi experiments. Read fully before modelling. Where this brief gives a range, pick a value inside it and record it in the parametric spreadsheet. Where it gives a rule, do not break it without stating why in the deliverable notes.

---

## 1. Design intent

Target look: **late-1970s video terminal and instrument design**, re-read through the retro-futurism of Fallout's RobCo terminals and Aperture Science hardware. Monolithic wedge bodies, sloped control decks, deep screen bezels, warm beige plastic, confident single-colour accents.

**Reference lineage (name these, study these):**

- **Lear Siegler ADM-3A** — the primary reference. One continuous shell, screen hooded and raked back, keyboard deck sloped toward the user, large soft radii where planes meet, zero visible fasteners.
- **Osborne 1** — rugged luggable proportions, recessed panels, handles and bumpers integrated into the shell, chunky bezels around small screens.
- **Fallout RobCo terminal / Pip-Boy** — exaggerated bezel depth, rounded-rectangle apertures, riveted or bolted detail used sparingly as ornament, screen glow treated as a design element.
- **Braun (Dieter Rams era)** — restraint. Controls in a strict grid, one accent colour, labels small and precisely aligned, nothing decorative that is not also functional.
- **Soviet-era instruments** — heavy knurled knobs, toggle switches in rows, engraved labels, slightly over-built proportions, honest utilitarian vents.

**Not this:** 1990s beige PC box (flat planes, sharp 90° corners, uniform tiny fillets, snap-on façade panels, Tupperware lid), consumer-electronics "rounded blob", gamer angular chamfers, any faux-wood.

One sentence test for every design decision: *would this part look at home on a 1978 terminal desk, or in a Vault-Tec lab?* If not, remove it.

---

## 2. Form language

**Massing**
- The body reads as **one block that has been sliced**, not a box with things attached. Primary volume is a wedge or a truncated prism.
- Front face is **never vertical**. Control deck slopes **10–20°** from horizontal toward the user. Screen face is raked back **12–30°** from vertical.
- Where two sloped planes meet, blend with a large radius (**R6–R15 mm**) rather than a crease. Vertical outer corners **R4–R10 mm**. Edges around apertures stay crisp (**R0.5–R1 mm** or a 0.8 mm chamfer).
- Footprint-to-height ratio: wide and low. Avoid cubes. Prefer width ≥ 1.4× height.
- Visually "heavy" base: a **2–4 mm plinth step** or a 45° chamfer at the bottom edge, or an undercut that makes the body float on hidden feet.

**Panels and apertures**
- Screens, grilles and control clusters sit in **recessed panels** (1.5–3 mm deep) with their own small radius. The recess is the retro signature; a flush cutout is not.
- Bezels around screens are **generous**: 6–14 mm wide, with corners rounded to **R3–R6 mm** independently of the display's own corner radius. A bezel that is thin and equal all round reads modern; make the bottom lip slightly deeper than the top (chin).
- Group controls on one plane in a strict grid; align to the screen edges or to the panel centre. No scattered controls.
- Any text or symbols are **recessed 0.4–0.6 mm**, never raised. Fonts: tracked uppercase sans, or DIN/Eurostile-like. Minimum stroke 0.5 mm at FDM resolution.

**Details allowed**
- Parting line as a deliberate reveal: a **0.6–1.0 mm groove** between lid and base, or a contrasting colour band.
- Horizontal cooling slots (not round hole arrays) — see §4 vents.
- Up to **four** ornamental bolts / rivets / countersunk screw heads, only where they coincide with real fasteners.
- A single model/serial plate recess (e.g. 24 × 10 mm, 0.5 mm deep) for a label.

**Details forbidden**
- Honeycomb or hex vents. Exposed layer-line-prone cylinders. Gratuitous chamfer facets. Visible snap latches on exterior. Raised logos. Rounded-everything.

---

## 3. Surface and colour

Printer: **Bambu Lab X2D** with **AMS Pro 2** (4 spools) and **AMS HT** (support material). Multi-colour is available and expected on the exterior.

**Primary body colour** — warm beige / putty. Target one of:
- Classic terminal beige: approx. **#D9C9A3** (Pantone 468-ish)
- Warm grey-beige: approx. **#C8BFA9**
- Lighter cream (Portal/Aperture): approx. **#E6DCC3**

**Accent palette** (pick one accent per enclosure, optionally one secondary):
- Dark brown-black for bezels and screen hoods: **#2B2622**
- Instrument orange: **#D9622B**
- Terminal green (indicator rings only): **#39B54A**
- Aperture / lab blue-grey: **#5B6770**
- Soviet instrument grey-green: **#7F8C79**

**Multi-colour usage rules**
- Colour changes happen on a **plane**, not through a surface: bezel inlays, recessed panel floors, parting-line bands, label text. Design bodies so each colour is its own solid in the CAD model and shares a flat interface.
- Recessed text is printed in the accent colour as a **0.4–0.6 mm inlay body** rather than a hollow pocket, so it survives bed adhesion and reads cleanly.
- Keep colour changes to **one or two layers** of the print where possible (floors, lids) to limit purge waste. Any colour used only in a few layers should sit on the same Z-band.
- Transparent/clear PETG from the AMS can be used for LED light pipes and indicator jewels (see §4 LEDs).

**Finish**
- Large visible top/sloped faces go toward the **textured PEI plate** when the orientation allows, giving a uniform matte "moulded" surface. Use the **engineering / smooth plate** only for parts whose visible face must be glossy (bezel inlays).
- Default materials: **PLA matte** for bodies (hides layer lines, most "plastic-moulded" look), **PETG** where heat (Pi 4/5, ESP32 with displays running hot) or flex (snap fits) matters. Support interface via AMS HT: PETG support under PLA, PLA support under PETG, for clean sloped undersides.

---

## 4. Component rules

**Boards (ESP32 dev boards, Pi Zero / 3 / 4 / 5, custom PCBs)**
- Mount on **standoffs integral to the base**, 4.5–6 mm tall, with a **2.6 mm hole** for M2.5 self-tapping or a **3.2 mm boss** for an M2.5 heat-set insert. Pi hole pattern: 58 × 49 mm (Pi 3/4/5), 58 × 23 mm (Zero). Ask for or measure ESP32 board holes; dev boards vary.
- Minimum **1.5 mm clearance** above the tallest component; **3 mm** over USB/antenna cans.
- Position connectors to exit the **rear or side**, through a recessed connector panel with **0.5 mm** clearance per side and a 0.6 mm chamfer on the opening.
- Pi 4/5 and any board over ~3 W needs a convective path: inlet slots low on one side, outlet slots high on the opposite side or rear (see Vents).

**Touchscreens (2.8" – 7")**
- The glass sits **0.5–1.0 mm below** the bezel surface (recessed, not flush, never proud).
- Bezel aperture = active area + **0.4 mm per side** for the viewing window; a stepped recess behind holds the module with **0.3 mm** clearance on the PCB outline.
- Retain modules from behind with a **clamp frame** screwed into the lid or with **four hook tabs + one snap**; never rely on glue.
- Flex cable gets a **slot 2 mm wider than the cable**, routed so the bend radius is ≥ 3 mm.
- Screen tilt angle: match the raked face (12–30°). For 7" screens on a desk, 20° is the comfortable default.

**Tactile buttons**
- Expose through **keycaps modelled as separate parts** (printed in accent colour), 10–14 mm cap, **1.5 mm travel**, with a 0.3 mm radial gap to the panel and a 0.5 mm top chamfer. Sculpted (slightly dished) cap tops read "terminal"; flat domes read "appliance".
- Alternatively use **living-hinge membranes** in PETG: 0.6 mm web, 1.2 mm hinge, button disc 10 mm. Hinge axis along the print's X or Y axis, never across layer lines.
- Button rows: pitch **16–19 mm**, aligned to the panel grid.

**Rotary encoders / dials**
- Knobs are **separate printed parts**: 18–30 mm diameter, 12–18 mm tall, with a skirt 1 mm larger than the shaft bushing, and either **knurl (1.0 mm pitch triangular)** or 10–14 flat facets. Add a **pointer line** recessed 0.4 mm and inlaid in accent colour.
- Encoder shaft: D-shaft **6 mm → 6.1 mm bore with a 4.6 mm flat** for PLA (adjust −0.1 mm for PETG). Panel hole **7.2 mm** for a 7 mm bushing, with a 0.5 mm raised collar on the panel for a seat.
- Give dials a scale: 7–11 tick marks recessed into the panel around the knob.

**Toggle switches**
- Rows of **2–5**, standard 6 mm or 12 mm bushings (holes **6.3 / 12.3 mm**), pitch 16–20 mm, each with a recessed label beneath. Mount on a sub-plate so wall thickness around the hole can be 2 mm regardless of body wall.

**Sensors, ports and vents**
- Sensors needing air (temp/humidity/gas): place behind a **slot grille** of 5–8 horizontal slots, **1.5–2.0 mm wide × 10–30 mm long**, 2.5 mm pitch, with a 0.5 mm chamfer on each slot edge. Grille sits in its own recessed panel.
- Optical sensors / cameras: round aperture **+0.6 mm** over lens diameter, with a 45° countersink outward.
- Vents: same horizontal slot language as grilles. Never round hole arrays, never hex.
- Ports: USB-C **9.2 × 3.6 mm** with R1.2 corners; micro-SD **12 × 2.5 mm**; 3.5 mm jack **6.5 mm** hole. Recess the port panel 1.5 mm so the cable plug shoulder lands below the surface.

**Speakers**
- Grille of slots as above or a **perforated inlay** (separate body, accent colour) with 1.6 mm round holes on a 2.8 mm triangular pitch — the one exception to "no round holes", and only as an inlay panel. Speaker clamps to the lid with a **ring + 3 tabs**; add a sealed back volume if the driver is ≥ 28 mm.

**Battery / USB-C power**
- 18650 or LiPo pouch in a **dedicated bay** with 1 mm foam allowance and a cable pass-through. Charging board port exits through the rear recessed panel. Never place the cell under a heat-producing board. Add a 1.5 × 20 mm slot above the cell bay for vapour release.

**Status LEDs**
- Use **light pipes**: a 3 mm or 5 mm clear PETG cylinder printed as a separate body, 0.2 mm clearance, press-fit into the panel, flush-domed on the outside. Or a **recessed jewel**: 6 mm hole with a 1 mm step holding a printed clear disc.
- Place indicators in a labelled row, not scattered. Retro indicators are **round, not rectangular**.

---

## 5. FDM engineering rules

**Walls and features**
- Nominal wall **2.4 mm** (6 perimeters at 0.4 mm). Range **2.0–3.0 mm**. Never below **1.6 mm** on exterior.
- Lid / panel plates **2.0–2.4 mm**. Internal ribs **1.2–1.6 mm**, height ≤ 10× thickness.
- Minimum feature: **0.8 mm** wall, **1.0 mm** hole, **0.4 mm** recessed text depth.
- Standoffs: boss OD ≥ hole + 3 mm; fillet R1 at the base.
- Draft angle is **not required** for printing, but add **1–2°** draft on visible vertical walls anyway: it removes the box look and catches light the way moulded parts do.

**Overhangs and bridging**
- Design so every visible surface prints without support, or with the support only on the interior. Max unsupported overhang **50°** from vertical (PLA), **45°** (PETG). Max bridge **25 mm**.
- Sloped decks: orient so the slope faces **down onto the plate** or stands at ≤ 50°. If the shell cannot satisfy this, **split the shell** at a parting line that the design already shows as a reveal.
- Use the AMS HT support material for any interior overhang; mark support regions in the deliverable notes.

**Tolerances (X2D, 0.2 mm layers, 0.4 nozzle)**
- Sliding fit: **0.2 mm** per side. Press fit (light pipes, knobs on D-shaft): **0.05–0.1 mm** interference. Clearance around purchased parts: **0.3 mm**. Lid-to-base lip: **0.15 mm** per side.
- Holes shrink: model **+0.2 mm** on all round holes under 10 mm.

**Fastening strategy**
- **Small enclosures (longest side ≤ 80 mm, opened rarely):** snap-fit. Cantilever hooks **1.2 mm thick, 6–8 mm long, 0.8 mm catch**, PETG preferred; minimum 3 hooks; hooks on the lid, catches in the base, hooks oriented so they print upright. Include one **pry slot** 8 × 1 mm at a corner. No screws.
- **Medium (80–160 mm) or opened often:** **M3 heat-set inserts** (M3 × 5.7 × 4.6 mm): hole **4.0 mm**, depth **6.5 mm**, boss OD **7.5 mm**, ≥ 1.6 mm floor under the insert. Screws enter from the **underside** and are hidden by the plinth, or from the back inside the connector recess. Max four visible fastener heads, and only as ornament per §2.
- **Large (> 160 mm) or structural:** inserts as above plus **alignment pins** (3 × 4 mm, 2 per edge), lid lip **4 mm** tall, ribs tying standoffs to walls.
- Lid lip: tongue **1.2 mm × 3 mm** on the lid, groove in the base; the parting line is the design reveal.
- Rubber feet: 4 recesses **Ø8 × 1 mm** for self-adhesive bumpers, or print **TPU feet** as a separate body if a TPU slot is available.

**Print orientation and plates**
- Base: open side up, bottom on the plate. Add a 0.5 mm chamfer on the first-layer perimeter to kill elephant's foot.
- Lid / sloped deck: visible face **down** on the textured plate where the geometry allows; any recessed text and inlays then print face-down and come out crisp.
- Knobs, keycaps, light pipes, inlays: stand upright, one per cluster, same plate.
- Every deliverable states the intended orientation and plate per part.

---

## 6. FreeCAD workflow

**Document structure**
- One FreeCAD file per enclosure. One **Part Design Body per printable part** (Base, Lid, Bezel_Inlay, Knob_01, Keycap_A, LightPipe_3mm…). Multi-colour inlays are separate bodies that share faces with their host.
- One **Spreadsheet** named `Params`. Everything dimensional references it. No magic numbers in sketches.
- A **master sketch** (`SK_Master_Side`) on the XZ plane defines the wedge profile: base length, overall height, deck angle, screen rake. Every body derives from it.

**Spreadsheet conventions**
- Aliases in `snake_case`, units in mm, degrees for angles:
  `wall`, `lid_t`, `deck_angle`, `screen_rake`, `body_w`, `body_d`, `body_h`, `corner_r`, `blend_r`, `recess_depth`, `bezel_w`, `screen_active_w`, `screen_active_h`, `screen_pcb_w`, `screen_pcb_h`, `clearance`, `insert_hole_d`, `insert_boss_d`, `snap_t`, `snap_len`, `snap_catch`, `btn_pitch`, `knob_d`
- Column A alias, B value, C unit, D note (source of the number: datasheet, measured, this brief §).
- Derived values live in the spreadsheet, not the sketch: `=screen_active_w + 2*0.4`.

**Modelling order (strict)**
1. Master side sketch → **Pad** symmetric to body width → the solid wedge.
2. **Pocket** for the interior shell (offset = `wall`), leaving the floor.
3. Apertures and recessed panels as Pockets from datum planes on the sloped faces (create a **Datum Plane** per sloped face; never sketch on a face that a later fillet will destroy).
4. Standoffs, bosses, lip, snap hooks as Pads / additive primitives.
5. **Fillets and chamfers last**, largest first: blend radii, then corners, then aperture edges, then the 0.5 mm plate chamfer. Name each fillet feature by purpose (`Fillet_Blend`, `Fillet_Corners`, `Chamfer_Apertures`).
6. Inlay bodies: `Part → Boolean → Common` of a shallow pad against the host recess, then `Part → Cut` from host.
7. Validate: `Part → Check Geometry` on every body; zero errors before export.

**Hygiene**
- Fully constrain every sketch. Use construction geometry for grids.
- Never fillet before pockets. Never use Part workbench booleans in a Part Design body except for inlays.
- Mirror / Polar Pattern for repeated controls; the pattern count is a spreadsheet value.

---

## 7. Export rules

- Units **mm**, origin at the **centre of the base footprint on the bottom face**, Z up.
- **STEP (AP214)** of the full assembly as the master: `ProjectName_v##.step`.
- **3MF** per plate with bodies pre-assigned to colours/filaments: `ProjectName_v##_PlateA.3mf`. Multi-colour parts export as one 3MF with multiple objects, not merged meshes.
- **STL (binary)** per body for fallback: `ProjectName_v##_Lid.stl`. Mesh tolerance 0.01 mm, angular 5°.
- Export orientation = print orientation (§5). Include `ProjectName_v##.FCStd` and a `README.md` listing: parts, colours, material, plate, support regions, inserts/screws BOM, declared parameter values.

---

## 8. Deliverable checklist

Before handing over, confirm every line:

- [ ] Front face sloped; screen raked; no vertical front plane.
- [ ] Planes blend with R6–R15; corners R4–R10; apertures crisp.
- [ ] Screen, grilles and controls sit in recessed panels, screen glass below bezel.
- [ ] Controls on one grid, aligned to screen or panel centre.
- [ ] Text recessed and inlaid; no raised logos.
- [ ] Beige body + one accent colour; colour changes on planes.
- [ ] Vents are horizontal slots; no hex, no round arrays (except speaker inlay).
- [ ] Walls 2.0–3.0 mm; standoffs and bosses per §5; +0.2 mm on small holes.
- [ ] Fastening matches size class; hidden fasteners; ≤ 4 visible heads.
- [ ] Every visible surface prints support-free in the declared orientation.
- [ ] Params spreadsheet complete, all sketches constrained, Check Geometry clean.
- [ ] STEP + 3MF + STL + FCStd + README exported with declared orientation.

---

## 9. Common failures to avoid

- **Tupperware**: a box with a lid and a cutout. Fix: wedge massing, sloped deck, plinth, blended planes.
- **Uniform fillets**: R2 on every edge. Fix: large blends where planes meet, crisp edges at apertures.
- **Flush screen**: display sitting level with or proud of the surface. Fix: 0.5–1 mm recess in a wide bezel with a chin.
- **Scattered controls**: holes placed wherever the board happened to be. Fix: controls on a grid; move the board, not the controls.
- **Raised text** and **extruded logos**. Fix: recess and inlay.
- **Unprintable sloped shell**: 60° overhang on the visible deck. Fix: split at the reveal, or flip the lid face-down.
- **Visible snaps / screws on the top face**. Fix: fasten from below or rear.
- **Hex vents**. Fix: horizontal slots.
- **Hard-coded dimensions**. Fix: everything in `Params`.

---

## 10. Agent prompt header

Paste above any modelling task:

> Design a 3D-printable enclosure following the "Enclosure Design Brief — Retro Terminal Language". Form: ADM-3A / Osborne 1 / RobCo-terminal wedge with sloped control deck (10–20°) and raked screen (12–30°), blended planes R6–R15, recessed panels, deep bezel, warm beige PLA body with one accent colour inlaid on planes. Fabrication: Bambu Lab X2D, AMS Pro 2 multi-colour, AMS HT support material, textured PEI plate. Walls 2.4 mm, +0.2 mm on small holes, 0.3 mm clearance to purchased parts. Fastening per size class (snap ≤ 80 mm, M3 heat-set inserts above). Model in FreeCAD Part Design with a `Params` spreadsheet, master side sketch, fillets last. Export STEP + per-plate 3MF + STL + FCStd + README. Components for this build: [list boards, screen model and active/PCB dimensions, buttons, encoders, switches, sensors, speaker, battery, LEDs]. Overall footprint target: [W × D × H mm].
