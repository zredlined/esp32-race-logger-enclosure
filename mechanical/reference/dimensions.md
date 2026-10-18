# Board dimensions (extracted from Adafruit Eagle .brd files, mm, board origin bottom-left, top view)

Source files in this folder. STEP models: 5323 (same PCB as 5477), 2922, 4415, 938. LSM6DSOX and HDC3022 have .brd only.

| Board | Outline | Plated holes (2.5 mm unless noted) | Connectors (position, plug exit) |
|---|---|---|---|
| ESP32-S3 Feather 5477 | 50.80 x 22.86 | (2.54,2.54) (2.54,20.32); far end 2.2 mm unplated at (48.26,1.84) (48.26,20.96) | USB-C at x=0 edge (2.67,11.43) exits -X (out the short edge); STEMMA QT top-entry at (22.35,11.43) exits UP; JST-PH battery at (10.92,19.37) exits -Y... (verify with STEP); headers on both long edges |
| Adalogger FeatherWing 2922 | 50.80 x 22.86 | Feather pattern (not flagged as plated in brd; verify in STEP) | microSD socket at (33.78,4.32) rot 90, 14.2 x 20.5 body, card exits -Y through the long edge (verify with STEP); CR1220 holder on top |
| PA1010D GPS 4415 | 25.40 x 25.40 | (2.54,2.54) (22.86,2.54) (2.54,22.86) (22.86,22.86) | JST SH side-entry at (2.54,12.70) exits -X and (22.86,12.70) exits +X; patch antenna on top must face sky |
| LSM6DSOX IMU 4438 | 25.40 x 17.78 | ONLY TWO: (2.54,15.24) (22.86,15.24); other corners are pads, board needs a support ledge | JST SH at (2.54,8.89) exits -X and (22.86,8.89) exits +X |
| HDC3022 5989 (from HDC3021 brd, same board) | 25.40 x 17.78 | (2.54,2.54) (22.86,2.54) (2.54,15.24) (22.86,15.24) | JST SH at (3.18,8.89) exits -X and (22.23,8.89) exits +X; sensor needs airflow |
| OLED FeatherWing 128x64 6313 (= 4650 assembled, SH1107) | 50.80 x 22.86 | Feather pattern | STEMMA QT side-entry on the UNDERSIDE at (3.18,11.43), plug exits -X out the USB end, 3 mm below PCB bottom; glass 37.1 x 17.0 at x 9.97..47.07, y 2.93..19.93, 2.06 tall; buttons A/B/C 3.8 x 2.8 at x 2.4..6.2, y centers 7.0 / 11.4 / 15.9; reset at x 5.5..9.3, y 20.8 |

Note: the eagle_brd.py "plug exits" for the Feather USB-C reported +X in raw output; the connector sits at x=2.67 on the x=0 edge, so the plug physically exits -X. Sign conventions on rotated parts need a STEP check before trusting.

## Stack heights (from sourcing notes; verify in Onshape)
- Feather PCB 1.6 mm; stacking header adds ~11 mm board-to-board; Adalogger on top with SD socket (~2 mm) and coin cell holder (~4 mm).
- JST SH mated plug: reserve 10–12 mm straight from header face, bend radius >= 8 mm.

## Measured from STEP models (mm, relative to each PCB's min corner; z relative to PCB top)
- Feather 5477 (5323 model): PCB 1.57 thick. USB-C body 7.9 x 8.9 x 4.2 at x -1.08..6.82, y 6.96..15.90, top 3.22 above PCB (overhangs the x=0 edge by 1.1). JST-PH battery 7.9 x 7.6 x 4.8 at x 6.97..14.87, y 14.97..22.57 (plug exits +Y over the long edge). STEMMA QT top-entry 2.9 x 6.0 x 4.25 at x 20.9..23.8, y 8.4..14.4. ESP32-S3 module 20.5 x 15.4 at x 30.64..51.14 (antenna overhangs the far end 0.34), 2.55 tall. Tallest part on top: 4.8 (battery JST). Header pins not in model.
- Adalogger 2922: CR1220 holder 15.2 x 15.0 at x 2.5..17.7, y 5.3..20.3, 4.0 tall (USB end). microSD socket 15.2 x 14.1 x 1.9 at x 33.5..48.7, y 4.3..18.4: CARD EXITS +X, out the short end opposite USB-C. Tallest on top: 4.0.
- OLED Wing 4650/6313: see table. Nothing above 2.06 except button caps (1.9). Underside: QT connector to 2.96 below PCB bottom, a few parts to 2.0 below.
- GPS 4415: patch antenna 10 x 10, top 6.4 above PCB, centered x 12.7, y 13.5. Side-entry JST SH 4.95 x 6.0 x 2.96 at both x ends, y 9.7..15.7. Model shows a 15 x 15 x 4.9 solid UNDER the PCB (z -4.04 below PCB bottom) that looks like a copied coin-cell holder from another model; the real board has nothing there. Design 4 mm standoffs regardless and verify against the physical board.

## Stack math (Feather PCB top = 0; MEASURED 2026-09-12 on the user's assembled stack: 12.7 mm PCB-bottom-to-PCB-bottom per stacking level, 27.0 mm Feather PCB bottom to OLED PCB top. The 2830 header body is 6.9 mm with 11.4 mm tails, not the 8.5 mm body assumed earlier.)
| Level | z bottom | z top |
|---|---|---|
| Feather PCB | -1.57 | 0 |
| header tails below Feather | up to -11.4 if untrimmed (trim to <= 3 mm or raise the standoffs) | -1.57 |
| Feather parts (USB-C, battery JST) | 0 | 4.8 |
| Adalogger PCB | 11.13 | 12.7 |
| Adalogger parts (coin cell holder) | 12.7 | 16.7 |
| OLED Wing PCB | 23.83 | 25.4 |
| OLED glass | 25.4 | 27.46 |
| OLED button caps (MEASURED: 4.0 above PCB bottom) | 25.4 | 27.83 |
| OLED Wing QT connector (underside) | 20.87 | 23.83 |
Feather PCB bottom to glass top: 29.0 mm. USB-C opening centered z = 1.1, x = 0 end. microSD slot centered z ~9.5 at the x = 50.8 end. OLED QT cable exits the x = 0 end at z ~17, same face as USB-C.
