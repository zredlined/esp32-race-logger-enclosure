# Requirements: ESP32 race logger enclosure

## Purpose
- Logs GPS position (10 Hz), 6-axis motion (100 Hz), cabin temp/humidity (1 Hz) to microSD with an RTC timestamp, and shows live status on an OLED.
- Looked at by the driver/co-driver; installed and serviced by the owner with hand tools. Bench testing first, then car testing.

## Boards and parts already owned
| Part | Adafruit PID | Notes |
|---|---|---|
| ESP32-S3 Feather 4MB/2MB PSRAM | 5477 | controller, USB-C, on-board STEMMA QT, LiPo charger |
| Adalogger FeatherWing (microSD + PCF8523 RTC) | 2922 | stacks on Feather; needs CR1220 coin cell; low stock (2) |
| Feather stacking headers | 2830 | between Feather and Adalogger |
| Mini GPS PA1010D STEMMA QT | 4415 | patch antenna must face sky |
| LSM6DSOX 6-DoF IMU | 4438 | axes must align with car; board must be rigid |
| SHT41 temp/humidity (per recent order; firmware mentions HDC3022 5989) | 5776 | same 25.4 x 17.78 footprint and holes either way |
| Assembled OLED FeatherWing 128x64 (SH1107) with 3 buttons | 6313 | top of the Feather stack; STEMMA QT on its underside at the USB end |
| M2.5 heat-set inserts, M2.5 screws 4–25 mm | owned | |
| STEMMA QT cables 100 mm (and 150 mm JST-to-header pigtails) | owned | 50 mm on hand per user |

## Environment
- Car cabin, roll bar mounted; also desk/bench. assumed: no sealing (splash only from spilled drinks), interior only.
- Temperature: parked car can exceed 60 C. assumed: PETG minimum; ASA preferred if the user can print it. PLA only for bench fit checks.
- Vibration: racing. Boards on screws, not friction; cables strain-relieved by routing, no free loops.
- Sunlight: OLED window should be recessed/shaded slightly; dark body OK, light body cooler.

## Mounting
- Roll bar tube. assumed: 1.5 in (38.1 mm) or 1.75 in (44.5 mm) OD; design mount as a separate printed saddle so the diameter is a single parameter.
- Removable: yes, by unscrewing the saddle or a quick-release; assumed: two M2.5 screws or a Velcro/hook strap through slots in the saddle for v1.
- Orientation: GPS antenna up (sky), OLED up (readable from seat), IMU axes parallel to case edges, case edges parallel to car axes. Case has a clear "forward" mark.

## Access while installed
- OLED visible through top window.
- Buttons: the OLED Wing has A/B/C tactile buttons and a reset button on its top face at the USB end; they must be pressable through the top window opening or via printed plungers. Feather reset reachable through a small side hole.
- microSD: OPTIONAL access (user will transfer logs wirelessly). A right-wall slot is kept because it is free, but it does not drive the layout; fiddly card removal is acceptable.
- USB-C: the one external connection, power (and flashing). Must be easy to plug one-handed in the car.
- Status LEDs: Feather NeoPixel/charge LEDs, assumed: not light-piped; small view hole optional.

## Interfaces leaving the box
- Power: USB-C 5 V from car USB adapter or bench. assumed: no LiPo in v1 (keep a bay option for a 400–500 mAh cell later).
- Data: Wi-Fi/BLE from the Feather; no wired links. Keep GPS antenna and Feather antenna away from metal saddle.
- No external sensors in v1.

## Manufacturing limits
- Bambu Lab P1S (enclosed, 256 mm bed, 0.4 mm nozzle). Material: ASA for car parts, PETG acceptable; PLA only for bench fit checks.
- Fasteners on hand: M2.5 heat-set inserts, M2.5 screws 4, 6, 8, 10, 12, 16, 20, 25 mm.
- New purchases allowed but minimal and fast to get.

## Look and feel
- Industrial, minimal, beautiful. Teenage Engineering meets motorsport: flat faces, crisp radii, one accent color, exposed and aligned fasteners, engraved labels, a purposeful window.
- Few printed parts (target 3: base/sled, shell, saddle). Visible screws acceptable if aligned and intentional.

## Budget and timeline
- Parts mostly owned. Additional purchases under ~$30. Bench platform first.

## Explicit non-goals
- No sealing, no swap doors, no battery in v1, no engine bay, no wired vehicle bus.
