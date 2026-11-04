# Sensor deck v7 — P4 controller sloped-deck sensor carrier

Prototype provision for the terminal-fresh-v6 sloped deck (15°, ~57 mm slope
length, 235 mm wide). **Not a fitted-sensor release.** Vision/sensing is
centralised on this controller per the owner direction recorded in the
[conductor README](../README.md); node cases get no vision sensors by default.

## Parts (stl/)

- `Deck_carrier_PROTOTYPE` — 190 × 44 × 3 plate, three ledged bays, ARGB
  channel on the top edge, rear cable slot. Freestanding study: attachment
  to the v6 housing is not yet designed.
- `Insert_blank_TEMPLATE` — copy this outline for each real module.
- `Insert_env_vented_PROTOTYPE` — segmented vent slots (12 mm max bridge,
  ribs between) for I2C env modules mounted behind (BME680, SCD41, SHT45,
  ENS160+AHT2x, GY-SGP41, ML8511 class). Airflow need per module data sheet.
- `Insert_mmwave_radome_PROTOTYPE` — plain face plate with rear standoff
  posts; module (HLK-LD2410C in hand, or Waveshare HMMD) mounts behind with
  its antenna facing the plate. No range/FOV/through-case claim.
- `Insert_module_rail_PROTOTYPE` — twin slots for Elegoo 37-kit / Freenove
  modules on straps or screws; module sizes vary, hence rails not holes.
- `ARGB_diffuser_PROTOTYPE` — separate translucent bar for the channel.
  Strip width/pitch must be measured; ARGB rings are not fitted here.

Inserts: 55.4 × 33.4 × 2.4, M3 clearance holes into the carrier ledge.
GY-521 (ITG/MPU) and other motion modules belong inside the case on a rigid
mount, not on a vented insert; they are not accommodated on this deck.

## Verify

`freecadcmd build.py` then `freecadcmd verify.py` → `validation.json`:
6/6 single valid solids, vent bridge 12 mm. Geometry only.

## Before a fitted print

1. Measure the chosen modules; cut fitted inserts from the blank template.
2. Choose LD2410C vs HMMD; check antenna keepout/radome guidance.
3. Design carrier-to-housing attachment and confirm deck clearance against
   the v6 housing, screen and speaker envelopes.
