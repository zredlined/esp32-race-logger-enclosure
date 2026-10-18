# Concepts for Gate B

All three share one internal layout (layout_top.png), because the wiring topology allows only one compact arrangement:
every sensor board has two side-entry STEMMA QT connectors on opposite ends, and two plugs facing each other need
24 mm between boards. The S-shaped daisy chain (OLED Wing -> GPS -> IMU -> SHT41) with two 14 mm cable lanes keeps
the footprint at 80 x 82 mm and uses three 100 mm cables, which the user owns. Height 33 mm is set by the three-board
Feather stack (pins to OLED glass 26.8 mm) plus floor, standoffs and roof.

Shared facts:
- Feather stack along the back wall, USB-C end to the left (-X), microSD card ejects through the right (+X) wall.
- OLED window and three buttons on the roof over the stack, reset pin-hole beside them.
- GPS front-left, patch antenna under a 1.6 mm roof region marked by a shallow 22 x 22 recess (no metal above).
- IMU front-middle on two M2.5 screws plus a support ledge under its pad-only edge; axis arrow engraved on the roof.
- SHT41 front-right next to five louvers in the front wall.
- Saddle for a 38.1 mm (1.5 in) roll bar tube, strap or zip-tie slots, tube axis along the case X axis. Diameter is one parameter.
- Screws: M2.5 heat-set inserts (owned). Feather far-end holes are 2.2 mm, so those two corners use printed pegs.

## A. Slab (tray + lid)
Form: box with 4 mm vertical fillets, 1.2 mm roof edge. Lid is a flat plate with the window, buttons, GPS mark and
four countersunk M2.5 screws on the roof corners. Boards mount on the tray floor.
Parts: tray, lid, saddle (3 prints) + window sheet + 3 button caps (print-in-place or loose).
UX: install by strapping the saddle to the bar, then screwing the tray to the saddle from inside before the lid goes on.
Plug USB-C into the recessed port on the left end (port sits 12 mm inside the wall; a slim-overmold cable is needed).
Eject the SD by pushing the card end that protrudes 1 mm from the right wall. Servicing: four screws off, lid off, everything visible.
Failure at the track: a cable unplugs; lid off in 30 s with one driver, everything reachable.
Best reason: simplest CAD, lid prints flat with the window edge on the bed. Visible fasteners read as intentional if aligned.

## B. Shell + sled (recommended)
Form: one seamless wrap-around shell (roof + four walls, 5 mm fillets, 2.5 mm roof edge) printed upside down so the roof
gets the textured-plate finish and the window, button holes and GPS recess have bed-perfect edges. All boards mount on a
flat sled plate that slides up into the shell and is held by four M2.5 screws from below into inserts in the shell's corner posts.
Zero fasteners on any visible face. The saddle screws to the sled bottom with the same four screws (longer), so the shell
lifts off with the box still strapped to the bar.
Parts: shell, sled, saddle (3 prints) + window sheet + button caps.
UX: same ports as A. Servicing: four screws underneath, shell lifts straight up; the sled with all boards and cables stays on the bar
and can be run on the bench as a bare fixture. Bench mode = sled alone, no shell.
Best reason: the cleanest object (TE-like), and the sled doubles as the bench platform the user asked for.
Risk: inserts pressed into posts that hang from the roof; posts must be 8 mm with root fillets. Shell interior prints as overhang-free only if walls are vertical.

## C. Wedge (shell + sled, roof sloped 10 degrees toward the front)
Same as B with the roof rising toward the back wall (stack side), so the display tilts toward a viewer in front of and below the box.
Height 33 at the front, ~47 at the back. The GPS recess follows the slope.
UX: better legibility when the box is mounted on a bar above eye level in front of the seat (dash bar). No benefit on a harness bar behind the seats.
Best reason: ergonomics if the mounting bar is in the driver's forward field of view.
Cost: more volume and print time, angled cuts in CAD, window sheet on a slope, taller back wall catches more sun.

## Tradeoffs
| | A Slab | B Shell+sled | C Wedge |
|---|---|---|---|
| Form | box, lid seam near the top | seamless shell, seam at the very bottom | sloped shell |
| Visible fasteners | 4 on the roof | none | none |
| Parts to print | 3 | 3 | 3 |
| Bench use | tray with boards, lid off | sled alone | sled alone |
| CAD effort | low | medium | medium-high |
| Print | lid flat, tray flat | shell upside down, sled flat | shell upside down, needs the slope handled |
| Best when | fastest path to a working box | it should look like a product | bar is in front of and above the driver |
