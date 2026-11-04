# Seven-inch conductor enclosure: mechanical reference brief

Reviewed 28 October 2026. Reference stage; no print-ready case or verified fit.

## Owner-reported hardware markings

- Main PCB: `ESP32-PR Function_EV_Board v1.6` (verbatim owner transcription; do not silently normalise PR to P4).
- Display adapter PCB: `ESP32-P4 HMI SubBoard V1.2`.
- The retained main-board drawing is v1.5.2, not a verified v1.6 mechanical reference. No matching v1.6 manufacturer drawing was located in this review.
- The official LCD adapter layout explicitly carries `ESP32-P4 HMI SubBoard V1.2`, matching the reported adapter revision:
  https://dl.espressif.com/dl/schematics/esp32-p4-function-ev-board-lcd-subboard-pcb-layout.pdf
- A user report in Espressif's BSP issue tracker also lists a P4 Function EV Board v1.6 with HMI SubBoard V1.2. This corroborates the revision combination but is not mechanical evidence:
  https://github.com/espressif/esp-bsp/issues/747

## Sources retained

Official guide (v1.5.2):
https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32p4/esp32-p4-function-ev-board/user_guide.html

Downloaded unmodified manufacturer references in `references/`:
- `board-dimensions.pdf` and `.dxf`: https://dl.espressif.com/dl/schematics/esp32-p4-function-ev-board-dimensions.pdf (DXF uses the same stem).
- `display-datasheet.pdf`: https://dl.espressif.com/dl/schematics/display_datasheet.pdf
- PNGs are Poppler renders for visual inspection; TXT is extracted reference text.

## Confirmed drawing information

- Main-board drawing calls out 88 mm overall width and 74 mm height; its stepped outline also has 82.5 mm and 53.5 mm callouts. These are outline dimensions, not mounting-hole centre distances. Use the DXF to resolve geometry, then compare to the physical board.
- Bare LCD module AML070JGI50-07403L: 165 x 100 x 3.5 mm in the datasheet specification. Active area: 154.2144 x 85.92 mm. Outline drawing is page 4. Neither size establishes the complete capacitive-touch/glass/adapter assembly envelope.
- Guide assembly: main board mounts to four central adapter-board posts using 8 mm standoffs; four peripheral posts take 20 mm standoffs as the supplied stand.
- LCD uses the reverse-direction ribbon. Allow protected cable routing and connector access, not a sharp fold against a case wall.

## Proposed case direction (not yet confirmed by owner)

Landscape desktop console with a removable front bezel, rear electronics tray and a detachable angled stand. Retain the supplied board/adapter mounting arrangement initially. Support the display frame without loading the active glass or flex tails. Keep the rear removable for development.

Provide access to USB programming/power, Ethernet, microSD, power switch and BOOT/RESET; retain header and ribbon service clearance. Preserve microphone air access and antenna clearance. Speaker and camera provisions depend on the selected configuration; do not invent their mounting dimensions.

## Measurements before fitted CAD

1. Compare owner-reported v1.6 main board with the retained v1.5.2 drawing: outline, mounting-hole centres and diameters, connector locations and heights. Do not assume revision equivalence. Obtain matching manufacturer CAD or measure the physical board before locating fitted ports and mounts.
2. Full touch-glass envelope, active-area offset, adapter-board outline, peripheral mount centres/hole diameters and glass-to-mount stack.
3. Installed rear depth including headers, USB/Ethernet plugs, wiring and ribbon bend space.
4. Desired desktop/handheld/wall format, stand angle, camera/speaker inclusion and printer/build-volume constraints.

Next deliverable: parametric assembly envelope and a small bezel/mount fit coupon before a full enclosure print. All provisional dimensions must remain labelled as such.

## Desktop console concept - 28 October 2026

Owner selected **angled desktop console**. The smaller Korvo case is owner-reported printed and working. Eight unmodified upstream STEP/STL references were retained at `references/korvo-case/`, pinned to commit `bd4d4ac18657e73583af3d7c0b0a23c3cddf3735`; downloads were checked against Git blob hashes. Its four STEP parts imported as valid single solids. Those parts are design references, not scaled into the P4 case.

Initial review geometry:
- Proposed 25-degree screen inclination above desk.
- Shell footprint 185 x 113.29 mm; height 30 mm front / 82.83 mm rear, excluding the 3 mm inclined bezel.
- Separate screen bezel and detached rear service cover; generic front ventilation.
- Transparent bare-LCD reference; no claim that this includes the touch glass or adapter.
- Four valid single solids; three shell/bezel/LCD intersection checks have zero volume. `concept-checks.json` contains measurements and checks.

Files: `Conductor-7inch-concept.FCStd` (editable document), `Conductor-7inch-concept.STEP` (interchange), `concept-preview.png`, `design-parameters.json` and `build-concept.py` (regenerator for FreeCAD's bundled runtime). Edit JSON then regenerate; the spreadsheet in the document is a parameter record, not a live expression-driven model.

**Not print-ready:** no fitted board mounts, display retention, enclosure fasteners, closure lips or registered port cutouts. Full touch glass dimensions/offset, adapter mounts and assembled depth remain unverified. The rear cover is shown detached to the right. Do not print this concept as a fitted enclosure. Next step is measured assembly geometry and a mount/bezel fit coupon.

## Internal speaker requirement - owner confirmed 28 October 2026

Include a speaker inside the console. Owner has the Waveshare speakers used elsewhere in the project, or can use a smaller speaker if required. Select the actual driver before locating mounts or committing the enclosure depth.

The official P4 Function EV Board guide specifies a speaker output capable of driving a 4-ohm, 3 W speaker (mono amplifier). Confirm the selected speaker's impedance and continuous power rating against that output. Do not assume the Waveshare driver's electrical rating from its dimensions.

Design provisions: speaker mounted to a rigid case surface with a grille, clearance for cone excursion, removable mechanical retention and protected wiring to the board connector. Keep the speaker's rear acoustic path separate from the onboard microphone where practical; preserve service access and check the assembled speaker against the screen/board/ribbon envelopes. A sealed speaker chamber is not yet specified. Speaker geometry is not yet included in the concept model.

Candidate reference: the existing speaker-fit study uses a 90 x 36 mm mounting pattern and an approximately 9 mm rear projection; these are candidate study values, not confirmation that every available Waveshare speaker matches. Driver body, front projection, impedance, rating and connector must be verified for the selected unit. Enlarge the console or choose the smaller driver after checking actual fit.

Candidate correction after reading the perimeter-speaker inventory: latest owner-measured Waveshare body is **98 x 44 x 20 mm**, superseding the older mesh-derived body dimensions. Use this envelope for the candidate layout, with separate installation/wiring clearance. Existing kit documentation identifies its driver as **8 ohms, 5 W**; confirm the marking of the actual selected speaker. This differs from the P4 guide's 4-ohm/3-W load specification, so do not promise 3 W output into the Waveshare speaker. The 90 x 36 mounting pattern and 9 mm projection above remain older reference values, not validated mount coordinates for the latest measured unit.

## Selected smaller speaker - supersedes Waveshare candidate

Owner provided **3 W, 4 ohms, 44 x 31 x 15 mm, 100 mm lead**. This matches the board guide's stated nominal speaker load and power. The concept now includes an orange speaker body envelope behind a provisional front grille. Width is horizontal; the 31 mm dimension is vertical and 15 mm depth goes into the enclosure, assuming a front-facing cone. Confirm the actual cone orientation and mounting features before creating a cradle.

The original 30 mm front shell interfered with the speaker envelope. The updated concept raises the front to **42 mm** and rear to **94.83 mm**, excluding the inclined bezel; footprint and 25-degree angle are unchanged. Five valid solids and six zero-overlap checks pass. These checks exclude the still-unmodelled board/adapter, plug and cable envelopes. No speaker screws or cradle were invented. A 100 mm lead must be checked against the eventual board connector position; connector compatibility is unverified. Earlier dimensions above describe the initial concept.

### Speaker image clarification

Owner supplied `references/selected-speaker-dimensions.png`. The drawing establishes **31 x 31 mm square body**, **44 mm total width including the two opposing mounting ears**, and a **100 mm lead**. The earlier written specification supplies the **15 mm depth**. Thus the conservative modelled 44 x 31 x 15 mm overall clearance envelope remains appropriate, but does not represent a rectangular 44 mm-wide speaker body. The cone faces out of the square body. Neither the hole-centre distance nor hole diameter is dimensioned; do not use 44 mm as screw spacing or derive fitted mounts by scaling the illustration. The visible two-pin connector does not establish pitch or polarity compatibility with the P4 board.

## External port access - owner requirement, 28 October 2026

Keep **Ethernet and all main-board USB ports accessible from outside the assembled case**, with the rear service cover installed. Do not rely on removing the cover for routine plugging, programming or networking.

Design the board orientation and case wall openings around the actual v1.6 board. Include clearance for USB plug housings, Ethernet plug boot and latch release, insertion/removal travel, cable bend space, and simultaneous cable use where the board permits it. The board guide notes that the high-speed USB Type-A and Type-C share an interface and cannot operate simultaneously; physical access should still be retained for both. Retain access to the LCD adapter's power connector if the final power wiring uses it.

Preferred layout: group the board's USB connector edge toward an external service face and expose the Ethernet edge on an adjacent face as required by the physical PCB. Confirm this against the assembled adapter and ribbon arrangement before choosing a registered orientation. No exact port centres or heights are assumed from the older v1.5.2 drawing.

Current CAD limitation: it still has only a generic rear service opening and does **not** yet satisfy external access with the cover fitted. Next fitted revision needs measured connector locations/heights and cable envelopes, then cutouts and latch-access checks. Speaker and wire placement must not obstruct those paths.

## Power path unresolved on physical v1.6 assembly

Owner reports a USB-C power input on the display; whether that powers the main board is not established. Do not infer electrical power transfer through mounting standoffs, or treat the display cable as a documented power feed.

The linked v1.5.2 guide explicitly describes separate power options: power the LCD adapter through its own USB input, OR feed its 5V/GND from corresponding main-board header pins if the main-board supply is sufficient. When powering the LCD adapter through its USB input, the guide says the inter-board 5V/GND wires are not needed. This does not establish that the adapter USB powers the main board through the ribbon or standoffs, nor approve paralleling independent supplies.

Retain physical access to the display USB-C power input as well as main-board USB ports. Final single-input wiring, supply budget, common ground and any protection/backfeed implications require checking the actual v1.6 board and HMI V1.2 schematics/wiring. No power wiring change has been made. Case closure must not commit to one external power cable yet.

### Included six-pin harness - owner report

Owner reports a six-pin female inter-board cable supplied with the brass standoffs. Treat this as the likely electrical interconnect between the main PCB and display, separate from the MIPI ribbon. The guide documents inter-board 5V/GND plus display reset and PWM signals; do not infer the complete cable pin order, orientation or power-feed direction from its six-pin count alone.

Design intent is now **one external USB-C supply using the included harness**, subject to confirming the supplied cable's connections and the actual kit's supported power-input port. Preserve access to both USB-C locations and allocate an internal harness route with connector engagement and service slack. No need to add a second permanent power cable to the concept at this stage. Single-input operation remains unverified on the physical v1.6 assembly.

## Supplied standoffs - owner measurement, 28 October 2026

Owner reports **four 19.5 mm brass standoffs and four 7.5 mm brass standoffs**. These physical kit measurements supersede the guide's nominal 20 mm / 8 mm values for this enclosure's hardware record.

Provisional roles follow the guide's assembly: four short (7.5 mm) spacers between the LCD adapter and main board; four long (19.5 mm) standoffs at the adapter periphery for support. The installed roles are not independently confirmed. The length datum (spacer body versus including male threaded projection), thread size and engagement remain unverified; do not use total fastener length as a PCB face-to-face clearance. Case mounting geometry must reference the installed bearing faces and actual mounting-hole pattern. No power conduction through these mounts is assumed.

## Owner-observed direct mounting arrangement - supersedes provisional spacer roles

Owner identifies the supplied sets as likely nominal **20 mm / 8 mm** standoffs (earlier measured approximately 19.5 / 7.5 mm). Preserve both descriptions; these are not two different hardware sets.

Owner reports the EV board can mount directly to the display assembly's existing mounting posts **without adding the short 8 mm standoffs**, and that the installed 20 mm perimeter standoffs extend comfortably beyond the EV board. Use this direct-mounted arrangement as the intended enclosure layout. Do not add an assumed 8 mm to the board stack.

This is a physical observation of available clearance, not a measured complete stack. The existing post height, board bearing plane, highest component and plugged cable envelopes still need registration. The long standoffs are candidates for case retention only after checking thread, bearing faces and mount coordinates; no fitted fastener geometry has been created. Check underside clearance/support before final assembly; do not interpret direct mounting as placing bare PCB against the display/adapter circuitry. Electrical power remains through the harness, not assumed through mounting hardware.

## Speaker and complete camera assembly layout

Owner requires placement of the **speaker, camera board and camera sensor** inside the enclosure. Include the full camera assembly, not just a decorative lens opening.

Proposed placement for review:
- Speaker: front lower face below the screen, retaining the selected 31 x 31 x 15 mm body / 44 mm ear envelope and grille. Final cradle and hole pattern remain unmeasured.
- Camera sensor/lens module: upper screen edge, outward-facing, provisionally centred. Its optical direction should face the operator when the console sits on the desk; do not assume the lens must be normal to the 25-degree screen. An adjustable or separately angled camera mount may be needed.
- Camera adapter PCB: inside the upper/rear region, on its own supported mount, with access to connectors. This is a proposed zone, not a proven fit against the EV board.
- Camera ribbon: protected route to the EV board's CSI connector, retaining the supplied cable's correct orientation and allowing assembly slack and a gentle bend without pinching at the cover seam. The guide distinguishes the camera's forward-direction ribbon from the LCD's reverse-direction ribbon.

Before fitted CAD: identify the actual sensor and adapter pieces and establish board outlines, mount-hole patterns, installed lens projection, camera optical axis, ribbon length and connector locations. Register these with the direct-mounted EV board and external Ethernet/USB plug envelopes. The existing 185 x 125 mm screen-plane concept has only limited upper bezel space; permit a wider top bezel or camera pod if physical geometry requires it. Do not conceal the lens behind an undimensioned bezel or claim an unmeasured field of view.

Current model includes only the speaker clearance envelope; camera sensor, adapter, optical aperture, supports and ribbon are **not yet modelled**. Existing zero-overlap checks therefore do not establish complete kit fit.

## Current layout: separated flat board, v2

Owner clarified that the main PCB may mount independently via the ribbon and harness, flat on the desk-side base with ports towards the rear. This supersedes the prior direct-display mounting layout for the desktop case.

The visual model is now in **`flat-board-v2/`**. It includes assembled, interior and rear-port images, FreeCAD and STEP files, generation source and geometry checks. Speaker faces right; camera is above the display. Old concept files remain historical. See `flat-board-v2/README.md` for assumptions and limitations before using this geometry. This is a visual review model, not a print-ready enclosure.

## Touch-first sensor conductor - owner direction, 28 October 2026

Touchscreen provides the main operator input. Do not add the previously suggested bank of rotary encoders or performance buttons by default. Incorporate **camera, lidar and mmWave sensing** in the controller to experiment with sharing sensed signals with the swarm.

Preserve the camera provision above the screen. Reserve separate replaceable sensor mounting areas, internal wiring space and service access for lidar and mmWave hardware. Exact sensor models, power/interface requirements, dimensions and mounting orientation must be established before fitted CAD or GPIO assignment. Project notes mention an available TFmini Plus, but owner has not confirmed it as this unit's selected lidar. No mmWave model has been identified in the searched project inventory.

Placement intent: camera and lidar need unobstructed outward views and serviceable mounts; mmWave needs placement and cover design suited to its actual module and antenna guidance. Do not invent field-of-view, detection-range or cover-thickness claims. Avoid committing all three sensors to a common axis before their intended use and physical modules are known.

Future software intent: conductor acquires sensor observations and shares timestamped, identified readings/events with swarm nodes, allowing visual and sound responses. This is a proposed capability, not implemented sensing, networking or fusion. Keep sensor acquisition separate from operator touch input and performance timing.

The current v2 CAD contains camera planning volumes only; lidar and mmWave are requirements, not yet modelled. Next geometry revision should add measured sensor modules and suitable apertures/mounts after identification, rather than a bank of controls.

## Selected mmWave module - planned order

Owner plans to order Waveshare **HMMD-mmWave-Sensor**, 24 GHz FMCW, advertised SXKMXXX0 family. Status: planned order, not received or tested. Owner image retained as `references/hmmd-mmwave-dimensions.png`.

The image dimensions the PCB at **20 x 20 mm**, with **2.54 mm adjacent header pitch**. Image labels show 3V3, GND, TX, RX and OT2. Overall installed thickness, connector mating height, wire exit and mounting-hole geometry are not dimensioned. Do not interpret visible header solder pads as enclosure screw holes.

Proposed integration: separate removable front-facing sensor carrier in the upper bezel, clear of the display's conductive layers and major metalwork. Reserve extra connector space behind the 20 x 20 footprint. Exact antenna spacing, cover material/thickness and sensing-axis guidance must be checked against manufacturer installation guidance before fitted CAD; direct product/wiki access returned HTTP 403 during this check. No claim of validated transmission through the case.

Use UART as the candidate detailed-data interface and retain optional OT2 access, subject to verifying module documentation, output meaning, electrical levels and available v1.6 pins. Do not assign ESP32 GPIOs yet. Presence/motion observations are intended for swarm experiments; do not promise angular tracking, gestures, people counting or raw radar access from the product title.

## Current print prototype v3 - dark beige, sensors deferred

Owner requested proceeding with the model for printing on a Bambu Labs printer in dark beige. **`print-prototype-v3/`** contains the latest CAD, shell/base STEP, individual STL files and an aperture fit gauge. This supersedes v2 for enclosure geometry; v2 remains the internal layout study. See `print-prototype-v3/PRINT-FIRST.md` before printing. Solid geometry is checked, but a complete fitted enclosure cannot be established without hardware measurements and retention design.

## Current styling revision: retro v4

Owner requested rounded edges, extended grilles and FLOCKINATOR lettering. Latest files are in **`retro-v4/`**, superseding v3 for styling. Includes rounded housing and screen aperture, longer rounded grille slots, raised text, separate aligned colour part and a fused single-colour embossed option. Dark beige with dark brown lettering is the suggested appearance. Hardware-fit limitations remain. Read `retro-v4/PRINT-FIRST.md`; the two-colour parts must retain their shared alignment in Bambu Studio.

## Current: MonoLisa Code and O camera aperture, v5

Owner requested MonoLisa Code with the first O enlarged for a camera lens. Latest files in **`monolisa-camera-v5/`** use installed MonoLisaCode-Regular.ttf outlines, an enlarged first O and a 10.6 mm camera opening (assumed 10 mm barrel + 0.3 mm radial clearance). Both embossed and separate-colour exports are included. Actual camera mounting and lens dimensions remain unverified; see the version's printing notes and camera-aperture.json. The font itself is not redistributed.

## Centralised sensing direction — owner clarification, 29 October 2026

Vision and most sensing live on this P4 controller (the flock's shared
world/sensor unit), **not** in the individual nodes. Do not add vision sensors
to node cases unless a specific experiment gives a reason. This corrects an
earlier discussion that placed node-case sensors on the flock nodes; the
sloped-front sensor revisions belong to this controller case.

Owner sensor inventory available for controller experiments: Elegoo 37 Sensor
Kit v2.0, HLK-LD2410C mmWave (in hand; the Waveshare HMMD above remains a
planned alternative), Freenove sensor modules, ARGB LED rings/strips, and
environmental modules including BME680, GY-ML8511, CJMCU-390, GY-SGP41,
HW-611, SHT3x, SHT45, SCD41, ENS160+AHT2x and GY-521 (ITG/MPU). Most env
modules are I2C; exact module outlines/hole patterns must be measured per
unit before fitted inserts. First CAD provision: `sensor-deck-v7/` — a
replaceable carrier for the sloped deck with blank, vented-env and mmWave
radome inserts plus a diffused ARGB strip channel. No module fit, field of
view, range or through-case radar claim is established by that provision.

## Fresh design from supplied brief: terminal v06

Owner requested a fresh model following `enclosure-design-brief.md`. The current style study is **`terminal-fresh-v6/`**, a new native Part Design model with upright screen, lower sloped deck, recessed bezel, flush MonoLisa text inlay, first-O camera hole and horizontal grille. Earlier v1-v5 are historical, not the base of this new feature tree. See the version's README for exports, chosen dimensions, brief-compliance gaps and unverified hardware fit.
