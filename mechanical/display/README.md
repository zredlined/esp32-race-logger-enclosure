# Race display mount (Waveshare ESP32-S3-Touch-LCD-7B)

Bench and shakedown-car mount for the 7-inch touch display that shows race-logger data over ESP-NOW. Same design
language as the logger enclosure: charcoal ASA, one orange line, aligned exposed screws, louvers, a four-dot mark.

Onshape document "race-display": https://cad.onshape.com/documents/f0ee92e6ca4b95fa969eb547
Part Studio 1 holds the custom feature "Race display mount"; "Display mount assembly" places the real Waveshare STEP on the mount.

## Parts (all print flat, no supports)

| Part | Filament | Orientation | Notes |
|---|---|---|---|
| Backpack | charcoal ASA + orange ASA (AMS) | rear face on the bed | 199.0 x 116.8 x 23.0 mm. 4 bosses land on the display's M3 frame lugs. In the slicer add a filament change to orange at Z = 21.0 mm: the top 2 mm of the wall is the orange band. One change, one flush. |
| Crown ring (optional) | orange ASA | flat | Only with the feature option "Separate crown ring" on (no AMS): the wall stops 2 mm lower with 8 pegs and the ring is glued on. |
| GoPro puck | charcoal ASA | base down, fingers up | 3-finger GoPro tab. Nests in a 0.6 mm recess in the backpack's rear face; 4 x M2.5 x 8 self-tap into 2.4 mm pilots. No inserts. |
| Bench stand | charcoal ASA | base down | 130 x 90 base, centred fin, 2-finger tab, pivot 68 mm up. Two parallelogram fields of five angled through-slots either side of the fin. No branding. |
| Depth coupon | any | counterbore side down | 70 x 14 x 15 bar, five M3 columns at the real boss height with counterbores 7.5 / 8.5 / 9.5 / 10.5 / 11.5 mm (1 to 5 dots). Result: 9.5 mm (3 dots) seats firmly; 8.5 gives ~1.6 mm of thread. Coupon kept in the feature for future screw changes. |

## Hardware
- 4 x M3 x 10 button head, through the bosses into the display's frame lugs. Measured: an M3 goes about 3 mm into a lug.
  The feature parameter "M3 screw length" sets the rear counterbore depth. Depth coupon result (2026-09-15): the lug thread starts about 2 mm below the frame surface, so the
  counterbore is 9.5 mm deep for M3 x 10 (ENGAGE 4.5 nominal = ~2.5 mm of real thread). Bosses are 9 mm diameter.
- 4 x M2.5 x 8 for the puck, self-tapping into 2.4 mm pilots (coupon-proven) with a 3.2 mm lead-in. Drive gently; ASA threads form on the first pass.
- 1 x M5 GoPro thumbscrew (long). Optional: GoPro roll-bar mount, suction mount.
- GoPro interface (v3): fingers 2.9 mm, gaps 3.6 mm, bolt hole 5.6 mm, puck fingers 18 mm so the knob clears the backpack by ~5 mm.
- USB-C cable: right-angle plug for the car (from the top-edge port, down the right-hand band inside the cavity between plate and LCD
  frame, out through the plate slot below the puck). Straight plugs work on the bench through the notch in the top wall.

## Assembly
1. Drop the puck into the recess on the backpack's rear face and drive the four M2.5 x 8.
2. Drop the display into the cavity, connector edge at the top (the notch side). Fit 4 x M3 from the rear.
3. The connector edge is the TOP edge (v3, 2026-09-15): the panel's native image orientation is upright that way, no firmware rotation needed.

## Design notes
- The cover glass overhangs the LCD frame by 12 to 15 mm per side; the wall follows the glass outline at 0.6 mm clearance and
  stops 0.5 mm below the glass face, so the glass is slightly proud (never sunk, never flush).
- Glass ledge (v2): a 3 mm stair-stepped ledge inside the wall sits 0.1 mm under the 1.0 mm cover glass; the factory adhesive tape and liner on the glass underside (kept on for serviceability) may lightly touch it. The four bosses remain the
  hard stop so the screws never preload the glass; the ledge closes the gap visually and supports the overhang. No foam. The glass overhang carries Waveshare's own peel-off tape; if it is ever bonded to the ledge, set LEDGE_GAP to ~0 and shorten the bosses 0.2 mm so the tape, not the screws, sets the glass height.
- Frame back sits 12 mm above the plate; the terminal blocks (8.3 mm tall) clear the plate by 2.1 mm.
- Ribbed grip zones on both short end walls: 26 vertical grooves, 0.6 deep on a 1.2 mm pitch over a 30 mm run, between the rear chamfer and the orange band. Constants RIB_* in the generator; tune after the first print.
- Louvers over the ESP32-S3 module (viewer's right) and mirrored over the terminal row.
- TF card, boot and reset buttons are inside the cavity: remove the four M3 screws to reach them (30 s job).
- Colour: single Z-height filament change on the AMS; the orange band is the only accent. Without an AMS, enable the separate crown ring option instead.

## Pipeline
```
source ~/.zshrc
~/.cache/electronics-prototype/cqenv/bin/python mechanical/display/generate_display.py   # constants -> checks -> FeatureScript -> Onshape -> STL
~/.cache/electronics-prototype/cqenv/bin/python mechanical/display/render_display.py     # pyvista renders into output/renders
~/.cache/electronics-prototype/cqenv/bin/python mechanical/display/assemble_display.py   # rebuild the assembly (only needed if part IDs change)
```
Print-ready files: output/print_*.stl (bed face at Z = 0, puck already flipped fingers-up). Reference data: mechanical/reference/waveshare-7b/ (STEP, drawing, schematic, dimensions.md).
