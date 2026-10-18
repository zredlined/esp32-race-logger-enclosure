# Decision (Gate B), 2026-09-09

**Concept B: seamless shell + sled + bolted saddle clamp.** Chosen by the user after the four-lens panel (see PANEL_GATE_B.md) recommended it unanimously.

Confirmed by the user:
- Buy Adafruit 4218 USB-C panel-mount extension (flush port in the left wall) and a second 2830 stacking header set.
- Roll bar tube is 1.75 in (44.45 mm). Clamp cap designed for 44.45 with the diameter as a feature parameter.
- Do NOT drill the Feather. Its two far-end 2.2 mm holes take M2 screws (user has M2) self-tapping into 1.6 mm standoff holes; the USB-end holes take M2.5.
- microSD access is optional (wireless transfer); a slot is kept but does not drive the layout.
- USB-C power is the only external connection.

Why B: the only concept that reads as a product (no visible fasteners, bed-textured roof), and the sled doubles as the bench fixture.
Why not A/C: A adds roof screws and counterbores in a 2 mm lid; C tilts the roof but not the display and faces the slope away from the driver.

## Addendum after CAD (2026-09-09)
- USB: the Adafruit 4218 round jack (22 mm hole, 22 mm body, 30 cm pigtail) and flat-flange extensions do not fit beside the OLED cable and the Feather plug. Decision: printed 26 mm guide chute on the sled with a 2 mm thumb pocket in the wall. Do not buy 4218.
- Shell fastening: 3 screws (P1, P2, P4); the right-wall post is a bearing pad because a screw there sits over the roll bar.
- Clamp: cradle is part of the saddle; a different tube diameter reprints saddle + cap (tubeDia parameter).
- Cables: OLED hop is 200 mm (Adafruit stocks 50/100/200/300/400).
