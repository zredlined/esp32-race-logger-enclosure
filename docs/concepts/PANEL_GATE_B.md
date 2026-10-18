# Review panel, Gate B (concepts) — consolidated findings and lead decisions

Four reviewers (industrial design, FDM manufacturing, wiring/RF/thermal, red-team user) reviewed the three concepts.
All four recommend **Concept B (shell + sled)**. Concept C was found to defeat its own purpose (roof tilts but the OLED stays flat, and the slope faces away from a driver behind the bar). Concept A's roof screws and counterbores in a 2 mm lid add problems without benefits.

## BLOCKS (found by 3 of 4 reviewers)
1. **Corner posts collide with the Feather stack.** The stack sits 0.9 mm from the back wall and 3 mm from the right wall; 8 mm posts land inside the PCBs and beside the ESP32-S3 antenna.
   Decision: two posts stay in the front corners (clear of GPS/SHT41); the two rear fasteners move to the walls where the lanes are empty: back wall in the USB lane (x ~10) and right wall in the middle lane (y ~mid-lane). All metal stays >= 10 mm from the Wi-Fi module.
2. **Cable lanes too narrow for a straight approach plus an 8 mm bend.** 14 mm lanes force a kink at every plug housing; the OLED-to-GPS hop cannot make its 3D drop.
   Decision: front lane 20 mm, middle lane 24 mm. Interior depth grows from 77 to ~93 (exterior ~98). Width and height unchanged.
3. **Saddle geometry.** A 56 x 44 block cannot reach the sled screws and a 5 mm deep cradle with strap slots lets the box rock, which shows up directly as fake g in the IMU.
   Decision: two-piece bolted clamp. Upper cradle is part of a full-footprint saddle plate (dark, same fillets as the shell, cutouts so the four shell screws stay reachable); lower cap bolted with two M2.5 x 25 (owned) through ears; cradle wraps >= 120 deg; rubber or TPU liner strip; caps printed for both 38.1 and 44.5 mm tubes. Saddle attaches to the sled with its own two screws into inserts in the saddle, so the shell comes off without disturbing the mount.

## FIX BEFORE PRINT
4. **USB-C port 22 mm deep, blind, and yank loads land on the Feather receptacle.** Three reviewers independently proposed the same fix.
   Decision: Adafruit 4218 USB-C round panel-mount extension ($9.95, in stock) mounted flush in the left wall; its internal plug lives in the USB lane. One purchase, and the user's only external connection becomes a designed, robust port.
5. **Window.** Sheet floats in a through-cut; roof underside only 0.5 mm above the OLED glass.
   Decision: open window sized glass + 0.3 mm per side with 1.5 mm corner radii; roof underside raised to glass + 1.5 mm. A 1 mm pocket on the INNER face accepts an optional 1 mm polycarbonate sheet later (prints without overhang on the upside-down shell). v1 ships open.
6. **Buttons.** 5.2 mm holes at 4.4 mm pitch merge; loose caps fall out and rattle.
   Decision: three print-in-place flexure flaps in the roof (3.8 x 7 mm, 0.6 mm slots, hinged at the -X end, 2 mm nub underneath), flush in a shallow recessed key bar, A/B/C engraved beside them; reset gets a 1.5 mm pin hole on the same centreline.
7. **microSD.** Card end is ~4 mm inside the wall behind a 3 mm slot.
   Decision (user says SD access is optional): stack moved to 1.5 mm from the right wall, slot 16 x 6 with an external thumb scallop. Not a layout driver.
8. **SHT41 in a dead-end pocket in front of the ESP32-S3 module (the heater).**
   Decision: 12 x 3 mm floor slot under the sensor, three louvers in the right wall opposite the front louvers (cross flow), and a 1.2 mm baffle rib on the sled between the middle lane and the sensor. Louvers become constant-width 1.2 mm slots spanning exactly the SHT41 width, aligned to the SD slot and base line.
9. **Cable slack and plug walk-out.** Each 100 mm hop carries 35 to 58 mm of excess; JST SH has no latch.
   Decision: tie-down slot pairs (2 x 4.5 x 1.8 mm, 4.4 mm apart) moulded in the sled at mid-lane for each hop; excess routed as one flat S under a zip tie.
10. **IMU free edge rests on a ledge without preload.**
    Decision: ledge 0.2 mm high for light preload plus a printed snap hook at each pad-edge corner; axis arrow engraved on both the roof and the sled.
11. **Fastener count.** Inserts in every standoff would need 7.6 mm bosses everywhere.
    Decision: heat-set inserts only in the 4 shell posts and 2 saddle bosses (6 total). Boards self-tap M2.5 into 2.1 mm holes in 6 mm dia x 4 mm standoffs (GPS and SHT41 on two diagonal screws each). Feather far-end holes are 2.2 mm unplated: user drills them to 2.6 mm so all four Feather corners take M2.5 (recommended over printed pegs, which shear).
12. **GPS mark** was a 22 mm bridge on the bed face.
    Decision: engraved outline groove 0.8 x 0.4 mm with a small satellite glyph; roof stays a flat 2 mm over the patch, no metal above.

## NICE TO HAVE (adopted)
- Radius family 5 / 2.5 / 1.5 mm; bed-side roof edge gets a 1.5 mm 45 deg chamfer instead of a fillet (prints clean upside down); sled 0.3 mm clearance per side with a 0.5 mm bottom chamfer.
- Delete the base groove; the sled's exposed 2.5 mm edge becomes the single accent band. Orange only on the sled edge, the button flaps and the strap/clamp liner.
- Engraved FWD chevron on the roof's front edge and on the sled; keyed notch between sled and saddle so it cannot be mounted rotated.
- Four rubber-foot recesses under the sled so it stands flat on the bench without the saddle.

## Lens conflicts resolved
- Manufacturing wanted an integral USB chute instead of buying a panel-mount part; overruled by three lenses and the user's statement that USB is the one connection they touch every session.
- Industrial design wanted a recessed outer-face window frame; manufacturing showed it becomes an overhang on the upside-down shell. Inner-face pocket adopted.
- Manufacturing's "sheet-free open window" vs red team's "2 mm air above the glass": both satisfied by raising the roof 1 mm and leaving the sheet optional.

## Resulting envelope (interior / exterior, mm)
Width 75.2 / 80, depth ~93 / ~98, height ~30 / ~35. Three printed parts (shell, sled, saddle-cradle) plus the clamp cap.
