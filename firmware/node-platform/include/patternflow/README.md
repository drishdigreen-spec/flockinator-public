# Patternflow Origin visual trial

Source: https://github.com/engmung/Patternflow at ae1e3df16179366b93ccd34111688b3f2ae3cc05.
Origin by Seunghun LEE is CC-BY-SA-4.0; its body is retained with hardware includes replaced and Serial logging redirected to a silent adapter. Shared math/color/parameter helpers are MIT, with Arduino includes removed. Licence texts are retained here.

This is an integration of the actual Origin preset into the commissioned ESP-IDF node firmware, not the full upstream firmware, console or module loader. The adapter maps RGB888 pixels to the existing RGB565 panel buffer. A scripted per-node hue/mode/frequency mapping exercises the pattern without encoders. Audio coupling is not implemented in this trial. Build environment: patternflow-trial. Brightness remains the existing 25%.


## Random playlist — 0.11.1

All 34 upstream firmware artwork presets are included in catalogue.h; calibration is excluded because it is a diagnostic overlay. Import reproducibly with `uv run --no-project python tools/patternflow/import_presets.py` against the pinned reference checkout. Bodies retain their per-file author and CC-BY-SA notices; includes are removed and Serial logging redirected to the adapter. Shared helpers retain MIT licensing.

Each node independently shuffles all 34 patterns without repeating within a pass, switches every 25–45 seconds and chooses parameter values from the middle half of each parameter's declared range. Large pattern allocations use PSRAM and are retained once per pattern. Actual elapsed time drives animation, capped at 100 ms per frame. There is no synchronisation or audio coupling.

The upstream catalogue also has 14 explicitly browser-only presets without firmware headers: 0516, 0517, 0519-2, 0524, 0524-2, 0526, 0529, 0530, 0609, 0614, 0614-2, 0619, 0622, 0624. These are not installed: they need separate firmware ports and hardware performance validation. The installed catalogue is recorded in catalogue.json.
