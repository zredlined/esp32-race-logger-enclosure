# Race logger enclosure, concept B (shell + sled + saddle clamp)

Onshape: https://cad.onshape.com/documents/1b4839c0672e56d3fe2d75a5 (Part Studio 1, custom feature "Race logger enclosure"; the tube diameter and part toggles are feature parameters).
Source of truth: `generate_onshape.py` (constants, clearance validation, FeatureScript generation, Onshape push, STL export; `--local` builds the tray parts with CadQuery for renders without API calls, `--only` limits the export). `render_stl.py` renders `output/*.stl` to `output/renders/`.

## Parts (all ASA on a Bambu P1S, 0.4 nozzle, 4 walls, 0.2 mm layers, brim optional)
| Part | Orientation on the bed | Supports | Notes |
|---|---|---|---|
| Shell | roof DOWN (upside down) on the textured plate | none | the roof gets the plate texture; window, key flaps, GPS groove and chevron have bed-perfect edges. Enable elephant-foot compensation. |
| Sled | plate down | none | 0.3 mm clearance per side inside the shell |
| Saddle | plate down, cradle up | none | the trough prints open-up |
| Clamp cap | standing on one end (60 mm tall, tube axis vertical) | none | holes print horizontal |
| Universal base (GoPro) | plate down, fingers up | none | v1 mount: same plate, inserts and access holes as the saddle; three GoPro fingers (3.0 mm, 3.4 mm gaps, M5 thumbscrew) so any GoPro adhesive, suction or bar clamp carries the box; four 20 x 4 mm strap slots for 25 mm Velcro or zip ties. Print this instead of the saddle + cap for bench and shakedown. |
| Analog tray (v2) | floor down, open up | none | 23.5 mm tray between sled and base with a 10.4 mm connector step; holds a half-size perma-proto and two stacked ADS1115s. Shell screws become M2.5 x 25 (heads inside the columns), sled screws M2.5 x 8 into two inserts in the column tops, base screws M2.5 x 10 from below. |
| Connector card (v2) | face down | none | front face of the step plus its roof; 2 x M12 holes by default, blank variant too. Reprint only this to change connectors. |
| ADS riser frame (v2) | bars down | none | 6 mm sleeves between the two ADS1115s |
| Test coupon | roof-down | none | PRINT FIRST (15 min): three flexure keys with nubs, insert bores 3.4 / 3.6 / 3.8, pilot holes 1.6 / 1.75 / 2.0 / 2.2 / 2.4. Pick the bore the insert does not slide into cold and the pilot that M2.5 / M2 bite without splitting; set INSERT_D / HOLE_M25 / HOLE_M2 and regenerate. |

Exterior 81.6 x 105.8 mm, 43.8 mm from base plate bottom to roof (37.1 above the sled plateau), 71 mm from tube centre to roof. Heights follow the measured 12.7 mm stacking pitch (27.0 mm Feather PCB bottom to OLED PCB top). Shell needs a 5 mm brim (large ASA slab with a chamfered bed edge). Saddle block at 15 % infill. Expected print time: shell ~3 h, sled ~2 h, saddle ~3.5 h, cap ~1.5 h. Print the cap before the saddle to prove the tube fit.

## Hardware
| Where | Fastener | Qty |
|---|---|---|
| Shell posts P1, P2, P4 (3): heat-set M2.5 x 4 inserts (3.5 mm OD), 3.4 mm bore with a 3.6 x 0.5 lead-in, 7.5 deep | M2.5 x 8 from below through the sled counterbores | 3 |
| Post P3 (right wall, middle) | none: bearing pad only, a screw here would sit over the roll bar | 0 |
| Saddle bosses S1 (27,13), S2 (72.8,52.5): heat-set M2.5 inserts pressed from the saddle plate TOP | M2.5 x 12 from the sled top (install before boards) | 2 |
| Cradle ears (4): heat-set M2.5 inserts, bores 9 deep | M2.5 x 12 up through the clamp cap flanges (flanges sit 1 mm open until the liner is compressed) | 4 |
| Feather USB-end holes | M2.5 x 6 self-tap into 2.4 mm standoff holes (coupon-verified) | 2 |
| Feather far-end 2.2 mm holes | NYLON M2 x 6 self-tap into 1.9 mm standoff holes (untested pilot; steel here sits 2 mm from the ESP32-S3 antenna). Until they arrive the stack runs on the two USB-end screws for bench use. | 2 |
| GPS (4, on 26 mm pillars), IMU (2), SHT41 (2 diagonal) | M2.5 x 6 self-tap into 2.4 mm pilots | 8 |
Totals: 9 inserts, 21 screws. The coupon part in the same Part Studio calibrates the bores and pilots.
Tube liner: 1 mm rubber strip (bicycle inner tube) inside the cradle and cap. The bore is 0.3 mm under the liner radius (`CLAMP_PRELOAD`) so tightening compresses the liner; a different bar diameter means reprinting the saddle AND the cap with `tubeDia` changed in the Onshape feature dialog.

Mount choice: v1 = Universal base (2 x M2.5 x 12 into its inserts, exactly like the saddle). Race car = saddle + clamp cap once the bar location is known. IMU orientation: calibrate in firmware (gravity vector at rest for pitch/roll, straight-line acceleration or GPS course for yaw); the chevron is a convenience.

## Assembly order (short form; the full illustrated guide is docs/ASSEMBLY.md)
1. Press 9 inserts: 3 in the shell posts P1/P2/P4 (from the open bottom), 2 in the saddle plate at S1/S2 (from the TOP face), 4 in the cradle ears (from below).
2. Screw the saddle to the sled: 2 x M2.5 x 12 from the sled top at S1 (27,13) and S2 (72.8,52.5).
3. Trim the Feather's stacking-header tails to 3 mm or less below the PCB (they are 11.4 mm long as supplied and the standoffs are 4 mm). Boards onto the sled: Feather stack (Feather with stacking headers, Adalogger with stacking headers, OLED Wing on top; CR1220 in the Adalogger) on 4 standoffs; GPS front-left on the four tall pillars (patch up, connectors front/back, plugs at roof height); IMU front-middle, slide its pad edge under the two hooks, 2 screws on the left edge; SHT41 front-right, 2 diagonal screws.
4. Cables (JST SH, no latches): C1 200 mm from the OLED Wing's underside QT: 10 mm straight out, turn toward the front, dive to the floor and run in the channel between the left wall and the 8 mm rib, rise and U-turn into the GPS front connector; stow the ~50 mm of slack as one flat loop in the front-left corner. C2 100 mm GPS rear -> IMU rear: U through the middle lane, straight run in the channel between the rib and the Feather's header sockets. C3 100 mm IMU front -> SHT41 front: U in the front lane against the wall. Tie each slack loop with a small zip tie or a dab of hot glue on the plug housings before car use.
5. Shell over the sled, 3 x M2.5 x 8 from below at P1, P2, P4 (heads reachable through the saddle access holes while the box is on the bar).
6. Clamp to the 1.75 in bar: cap + 4 x M2.5 x 12. Chevron on the roof and sled points to the front of the car; IMU axes: board +X = case -Y (car forward), board +Y = case -X (map in firmware).

## Ports
USB-C: left wall, guided 26 mm chute to the Feather (13.5 x 8.4 mm opening with a 2 mm thumb pocket, fits overmolds up to ~13 x 8 mm; most of the plug body sits inside the wall, pull by the strain relief). A flush panel-mount jack was considered and rejected: no room beside the OLED cable and the plug. microSD: right wall slot, card end ~4 mm inside (optional access). Buttons A/B/C: three 0.6 mm flexure keys left of the window, dots mark A, B, C. Reset: the round key above them (reboots the ESP32). A thin groove frames the whole control field (dots, keys, window); a 12 mm square marks the GPS patch; the 4OGS wordmark is engraved on the back wall facing the driver. Slicer: filament change at layer 3 (0.4 mm) from graphite to purple fills every roof engraving purple (frame, dots, GPS square, chevron); optionally paint the key tops purple. Recommended: a 1 mm smoked polycarbonate or acrylic lens in the 1 mm pocket on the roof's inner face (window + 1.5 mm per side), held with thin double-sided tape on the long sides; it hides the roof-to-glass gap and seals the window.

## v2: analog tray (2 x ADS1115 + proto board)
The tray sits between the sled and the base and reuses the shell, sled and base as printed (the base's two blind insert bores get drilled through with a 2.7 mm bit). Fasteners, all from the kit: 3 x M2.5 x 25 from below clamp shell + sled + tray (heads seat 7 mm up inside the P columns, reached through the base's access holes); 2 x M2.5 x 8 from the sled top into inserts in the S column tops; 2 x M2.5 x 10 from below through the base inserts into pilots in the S column bottoms; 4 x M2.5 x 16 through the ADS stack. Inside, tray coordinates equal case coordinates: a half-size perma-proto (DIKAVS 51 x 81.5 or Adafruit 571) at x 7.3-58.3, y 17.3-98.8 on 4 mm standoffs with 15 mm of headroom, held by two centreline screws, three snap hooks and a lip on the back wall; the two ADS1115 STEMMA QT boards stacked at x 58.8-76.6, y 17-42.4 (right wall relieved 0.5 mm beside them) (lower 0x48 on 6.5 mm standoffs, upper 0x49 on a printed 6 mm riser frame, four M2.5 x 16 through both). STEMMA chain: SHT41 rear -> 100 mm down the sled's drop slot -> upper ADS rear; 50 mm hairpin lower front -> upper front; lower rear spare. A 10.4 mm step at the front carries a removable connector card (2 x M12 by default, bodies up to 18 mm deep), screwed from the front into the corner blocks; the card's roof closes the step. Full guide: docs/ASSEMBLY.md section 8. Onshape assembly "Enclosure v2 (analog tray)".
