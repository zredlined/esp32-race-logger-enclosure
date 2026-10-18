#!/usr/bin/env python
"""ESP32 race logger enclosure (concept B): layout constants -> clearance validation -> FeatureScript -> Onshape.

Frame: interior coordinates, origin at the inner front-left corner on the sled plateau top. X right (along the roll bar),
Y toward the back wall (car forward is -Y), Z up. All mm. The FeatureScript is generated from these constants so the
numbers below are the single source of truth; the Onshape feature exposes tube diameter and part toggles.

Usage:  generate_onshape.py [--dry] [--no-render]
"""
import sys, os, json, math, argparse, subprocess, time
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # cq_toolkit.py is vendored next to this file (from the electronics-prototype skill)
from cq_toolkit import Env, clearance_report, side_connector_envs, polyline_length  # noqa

HERE = Path(__file__).parent
OUT = HERE / "output"; OUT.mkdir(exist_ok=True)

# ------------------------------------------------------------------ constants
WALL, PLATE_T, PLATEAU_T, ROOF = 2.4, 2.5, 1.2, 2.0
LANE_F, ROW, LANE_M, STACK_D, BACK = 24.0, 25.4, 23.5, 22.86, 5.24
STACK_L, RIGHT = 50.8, 1.5
Y_ROW0 = LANE_F; Y_ROW1 = Y_ROW0 + ROW; Y_STK0 = Y_ROW1 + LANE_M; Y_STK1 = Y_STK0 + STACK_D
D = round(Y_STK1 + BACK, 1)                       # 101.0
X_STK0 = 24.5; X_STK1 = X_STK0 + STACK_L
W = round(X_STK1 + RIGHT, 1)                      # 76.8
STANDOFF, PCB = 4.0, 1.57
Z_GPS_DECK = 26.0                                 # GPS PCB bottom on 4 pillars: patch top 1 mm under the roof, above the stack's shadow (2026-09-13)
ZF = STANDOFF + PCB                               # Feather PCB top 5.57
STACK_PITCH = 12.7                                # measured 2026-09-12 on the real 2830 headers: PCB bottom to next PCB bottom (27.0 mm Feather bottom to OLED top)
Z_ADA = STANDOFF + STACK_PITCH; Z_OLED = STANDOFF + 2 * STACK_PITCH    # PCB bottoms of Adalogger / OLED wing
Z_GLASS_TOP = Z_OLED + 1.57 + 2.06                # 27.77
STACK_TO_CAP = 29.7                               # Feather PCB bottom to OLED button cap top: sum of measured parts 29.4, eyeballed "just under 30" on the assembled stack; design mid-point
Z_BTN_TOP = STANDOFF + STACK_TO_CAP                # 34.0
NUB_GAP = 0.3                                     # nub clearance above the caps; tolerates ~0.6 mm of stack height variation either way
H_INT = round(Z_GLASS_TOP + 2.1, 1)               # roof underside: glass + 2.1 so a 0.6 mm taller stack still clears
Z_ROOF_TOP = H_INT + ROOF                         # 31.3
Z_PLATE_TOP, Z_PLATE_BOT = -PLATEAU_T, -PLATEAU_T - PLATE_T   # -1.2, -3.7
SADDLE_T = 3.0; Z_SAD_TOP, Z_SAD_BOT = Z_PLATE_BOT, Z_PLATE_BOT - SADDLE_T  # -3.7, -6.7
TUBE_D_DEFAULT = 44.45; LINER = 1.0
R_VERT, R_WIN, CHAMF_ROOF = 5.0, 1.5, 1.5
INSERT_D, INSERT_DEPTH = 3.4, 5.0                 # M2.5 x 4 mm inserts, 3.5 mm OD (user 2026-09-13): bore = OD - 0.1; the body does not enter cold, the iron seats it. Coupon-verified.
INSERT_SEAT_D, INSERT_SEAT_H = 3.6, 0.5            # small lead-in at the mouth so the insert starts straight
BORE_POST, BORE_EAR = 7.5, 9.0                    # bore depth = insert + screw protrusion + 1 (M2.5 x 8 / x 12)
FLAP_T, FLAP_L, FLAP_W, SLOT_W = 0.6, 10.0, 3.65, 0.8   # flexure keys: 3 layers thick, 10 mm long, 0.8 mm slots
CLAMP_PRELOAD = 0.3                               # bore radius under liner radius; cap flanges sit 1 mm open until tightened
HOLE_M25, HOLE_M2 = 2.4, 1.9                      # self-tap pilots: coupon 2026-09-12, M2.5 best in 2.4 (2.2 too tight); M2 scaled +0.2, untested
CLR_M25, CBORE_D, CBORE_H = 2.7, 5.0, 1.5

# boards (case coords of their min corner). Sensors rotated 90 deg: board-local X runs along case Y.
GPS = dict(x=8.0, y=Y_ROW0, w=25.4, d=25.4)
IMU = dict(x=36.4, y=Y_ROW0, w=17.78, d=25.4)
SHT = dict(x=57.2, y=Y_ROW0, w=17.78, d=25.4)
GPS_CONN_X = GPS["x"] + 12.7; IMU_CONN_X = IMU["x"] + 8.89; SHT_CONN_X = SHT["x"] + 8.89
USB_Y = Y_STK0 + 11.43; USB_Z = ZF + 1.1
QT = dict(cx=X_STK0 + 3.175, cy=USB_Y, z0=Z_OLED - 2.96, z1=Z_OLED)   # OLED wing QT, underside, exits -X
GLASS_TRIM_R = 2.5   # measured on hardware 2026-09-13: glass ends 2-3 mm before the STEP edge on the +X side
GLASS = dict(x0=X_STK0 + 9.97, x1=X_STK0 + 47.07 - GLASS_TRIM_R, y0=Y_STK0 + 2.93, y1=Y_STK0 + 19.93)
BTN_X = X_STK0 + 4.3; BTN_Y = [Y_STK0 + v for v in (7.0, 11.4, 15.9)]
GPS_PATCH = (GPS["x"] + 13.46, GPS["y"] + 12.7)
# fasteners
POSTS = {"P1": (33.0, 4.0, "front"), "P2": (W - 4.0, 4.0, "corner"), "P4": (4.0, D - 4.0, "corner")}   # screwed posts (all outside the tube shadow)
PAD_P3 = (W - 4.0, 61.0)   # bearing pad only: a screw here would sit 5 mm above the roll bar
SADDLE_SCREWS = {"S1": (27.0, 13.0), "S2": (W - 4.0, 52.5)}   # outside the cradle block footprint so the inserts are reachable
# chute (USB-C guide) on the sled
CH_IN_W, CH_IN_Z0, CH_IN_Z1, CH_WALL = 13.5, 2.5, 10.9, 1.2
CH_X0, CH_X1 = 0.3, X_STK0 - 2.0   # 0.3 clearance to the shell wall like the plateau
CH_Y0, CH_Y1 = USB_Y - CH_IN_W / 2 - CH_WALL, USB_Y + CH_IN_W / 2 + CH_WALL
# louvers
LOUV_F_X = [58.0, 61.2, 64.4, 67.6]; LOUV_R_Y = [27.6, 30.8, 34.0, 37.2, 40.4]; LOUV_B_X = [58.0, 61.2, 64.4]
LOUV_W = 1.2   # louver heights are set below from the SD slot datum
SD = dict(y=Y_STK0 + 11.4, z0=Z_ADA + 1.57 - 2.0, z1=Z_ADA + 1.57 + 4.0, half=8.0)
LOUV_Z = (5.0, round(SD["z1"], 2)); LOUV_Z_BACK = (round(SD["z1"], 2), round(H_INT - 2.5, 2))   # tops share the SD slot datum; back-wall chimney over the ESP32
VENT = dict(x=71.6, y=36.75, w=6.0, d=13.5)
DROP = dict(x=SHT_CONN_X, y=SHT["y"] + 22.225 + 12.7 + 4.0, w=10.0, d=5.0)   # future: cable drop slot beyond the SHT41's spare rear plug, for an analog bay under the sled (blanked by the saddle plate in v1)   # beside the cradle block (x > 68.4), between SHT41 standoff and pad
FEET = [(12, 6), (W - 12, 6), (12, D - 6), (W - 12, D - 6)]
# cradle
CR_X0, CR_X1, CR_Y0, CR_Y1 = 8.4, W - 8.4, 15.15, D - 15.15
GPS_MARK_CX = X_STK0 + 9.97 - 0.3 - 11.0   # square's right edge on the window's left edge
RESET = (X_STK0 + 7.4, Y_STK0 + 20.8)   # reset switch cap centre (3.8 x 2.8)
RESET_KEY = dict(cx=X_STK0 + 6.2, cy=Y_STK0 + 21.1, r=1.9, stem_w=1.6, hinge_x=BTN_X - 6.5, nub_d=1.8)   # round key + stem toward -X: all four keys hinge on one line; ring slot meets key C's slot
import os as _os
FRAME_ON = _os.environ.get("FRAME_ON", "1") == "1"; LOGO_ON = _os.environ.get("LOGO_ON", "1") == "1"
# 4OGS wordmark: the seven "4OGS" polygons from reference/4ogs_logo.svg (RACING text and outline dropped: too thin for FDM)
LOGO_POLYS = [[(61.72, 41.62), (50.04, 78.15), (78.52, 78.15), (87.22, 71.87), (102.35, 24.54), (72.24, 24.54), (65.66, 29.29), (63.16, 37.11), (84.31, 37.11), (75.21, 65.58), (68.08, 65.58), (75.74, 41.62), (61.72, 41.62)], [(44.33, 7.58), (27.97, 7.58), (18.53, 37.11), (34.89, 37.11), (44.33, 7.58)], [(136.73, 41.62), (142.19, 24.54), (112.07, 24.54), (105.49, 29.29), (102.99, 37.11), (124.15, 37.11), (122.7, 41.62), (136.73, 41.62)], [(202.0, 7.58), (51.57, 7.58), (38.66, 47.93), (31.42, 47.93), (33.44, 41.62), (17.08, 41.62), (10.38, 62.59), (33.98, 62.59), (29.0, 78.15), (45.37, 78.15), (63.84, 20.36), (188.06, 20.36), (182.7, 37.11), (202.0, 7.58)], [(145.35, 29.29), (142.85, 37.11), (178.03, 37.11), (182.04, 24.54), (151.93, 24.54), (145.35, 29.29)], [(155.43, 41.62), (141.41, 41.62), (136.29, 57.61), (157.45, 57.61), (154.9, 65.58), (133.75, 65.58), (129.73, 78.15), (164.9, 78.15), (175.48, 45.08), (154.32, 45.08), (155.43, 41.62)], [(91.92, 71.73), (97.86, 78.15), (125.05, 78.15), (133.51, 51.67), (117.04, 51.67), (114.42, 59.86), (116.87, 59.86), (115.04, 65.58), (107.91, 65.58), (115.58, 41.62), (101.55, 41.62), (91.92, 71.73)]]
LOGO_W = float(_os.environ.get("LOGO_W", "32.0"))   # engraved width; slit in the O is ~0.85 mm at 36
LOGO_POS = _os.environ.get("LOGO_POS", "back")      # "right": beside the GPS mark, right edge on the frame; "corner": small, front-right, on the chevron's baseline
GPS_MARK = float(_os.environ.get("GPS_MARK", "12.0"))   # engraved square over the patch (patch itself is 10 x 10)
FRAME = dict(x0=13.6, y0=Y_STK0 + 2.93 - 0.3 - 1.8, x1=X_STK0 + 47.07 - 2.5 + 0.3 + 1.8, y1=Y_STK0 + 21.1 + 2.7 + 1.8, w=0.8, r=2.5)   # bezel groove around dots + keys + window
EAR_PTS = [(16.4, 21.0), (W - 16.4, 21.0), (16.4, D - 21.0), (W - 16.4, D - 21.0)]
TUBE_CY = D / 2

# ------------------------------------------------------------------ v2 ANALOG TRAY: between the sled and the base; shell, sled and base stay as printed
# Tray-local frame: same x/y as the case; z from the tray's bottom face. Emitted in the Part Studio beside the enclosure (x + TRAY_DX),
# at case z = Z_TRAY_BOT + z. The base drops by TRAY_H in the v2 assembly. Five M2.5 x SCREW_LONG replace the five v1 screws.
# Fasteners (all from the user's kit, 2026-10-02): shell screws P1/P2/P4 = M2.5 x 25 from below, heads seated inside the tray columns (driver channel from the
# tray bottom); sled -> tray at S1/S2 = M2.5 x 8 into inserts pressed into the column tops; tray -> base = M2.5 x 10 from below through the base's (drilled-through)
# inserts into pilots in the column bottoms; ADS stack = M2.5 x 16 on 6 mm lower standoffs. The tray height is set by the ADS stack, not by a screw.
P_SCREW, S_SCREW, BASE_SCREW = 25.0, 8.0, 10.0
ADS_SO_H = 6.5                                                     # lower ADS standoff height: 6.5 + 2 floor gives an 8 mm pilot for the M2.5 x 16 stack screws
TRAY_H = 23.5                                                      # upper ADS plug housings end 0.9 mm under the lid
P_SEAT = TRAY_H + PLATE_T + PLATEAU_T + 4.8 - P_SCREW              # 6.5: head seat height inside the P columns (4.8 mm of thread in the shell inserts)
P_CHAN_D = 5.0                                                     # driver / head channel from the tray bottom to the seat (same 5.0 the v1 counterbores use)
TRAY_FLOOR, TRAY_WALL, COL_D = 2.0, WALL, 7.5                     # floor, walls (= shell wall), screw columns
CHIN_D, CARD_T, FLANGE_T = 10.4, 2.4, 2.0                         # forward step for connector bodies; card = its front face + a roof over the step
CARD_Y0 = -WALL - CHIN_D                                           # -12.8: card outer face
CARD_Y1 = CARD_Y0 + CARD_T                                         # -10.4: card inner face = front of the cavity
Z_TRAY_BOT = Z_SAD_TOP - TRAY_H                                    # -25.2 case z
TRAY_DX = W + 2 * WALL + 30.0                                      # Part Studio offset for the tray parts
CARD2_DX = W + 2 * WALL + 20.0                                     # blank card and riser frame sit one more footprint to the right
TRAY_CLEAR_H = TRAY_H - TRAY_FLOOR                                 # 21 inside; the sled plate is the lid
# boards (tray xy). Proto: DIKAVS / Adafruit half perma-proto, long axis along Y, two 3.2 mm holes on the centreline 73.7 apart.
PROTO = dict(x=7.3, y=17.3, w=51.0, d=81.5, t=1.6, hole_dy=36.85)
PROTO_CX, PROTO_CY = PROTO["x"] + PROTO["w"] / 2, PROTO["y"] + PROTO["d"] / 2
PROTO_SCREWS = [(PROTO_CX, PROTO_CY - PROTO["hole_dy"]), (PROTO_CX, PROTO_CY + PROTO["hole_dy"])]
_pi = 3.6   # pad inset from the board edges (clears the P4 block)
PROTO_PADS = [(PROTO["x"] + _pi, PROTO["y"] + _pi), (PROTO["x"] + PROTO["w"] - _pi, PROTO["y"] + _pi), (PROTO["x"] + _pi, PROTO["y"] + PROTO["d"] - _pi),
              (PROTO["x"] + PROTO["w"] - _pi, PROTO["y"] + PROTO["d"] - _pi), (PROTO["x"] + _pi, PROTO_CY), (PROTO["x"] + PROTO["w"] - _pi, PROTO_CY)]
Z_BRD = TRAY_FLOOR + STANDOFF                                      # 6.0: PCB bottoms of the proto and ADS level 1
Z_PROTO_TOP = Z_BRD + PROTO["t"]                                   # 7.6
PROTO_HOOKS = [("left", PROTO["x"], 35.0), ("left", PROTO["x"], 80.0), ("front", PROTO["y"], 45.0)]   # (edge, edge coord, along coord); the back edge gets a fixed lip from the wall
PROTO_BACK_LIP_X = (43.75, 46.25)
# ADS1115 STEMMA QT x2, stacked two high in the strip right of the proto; long axis along Y, ports face +-Y. Level 2 sits on a printed riser frame.
ADS = dict(x=58.8, y=17.0, w=17.78, d=25.4)                       # rear plug housings end 1.9 mm before the S2 column
WALL_RELIEF = (W - 0.5, 14.0, 47.0)                                # right wall thinned to 1.9 mm beside the ADS stack (x0, y0, y1): 0.7 mm board-to-wall clearance
ADS_HOLES = [(ADS["x"] + dx, ADS["y"] + dy) for dx in (2.54, 15.24) for dy in (2.54, 22.86)]
ADS_CONN_X = ADS["x"] + 8.89
ADS_SO_D = 6.0                                                     # standoff dia; the two proto-side standoffs are D-shaped (flat at ADS_SO_FLAT_X), the two wall-side ones fuse to the wall
ADS_SO_FLAT_X = PROTO["x"] + PROTO["w"] + 0.3                      # 58.6: leaves 1.5 mm of wall around the 2.4 pilot on the proto side (sled standoffs have 1.8)
RISER_H = 6.0                                                      # level-2 PCB bottom = level-1 PCB top + 6
Z_ADS1 = TRAY_FLOOR + ADS_SO_H; Z_ADS2 = Z_ADS1 + PCB + RISER_H     # PCB bottoms 8.5 / 16.07; level-2 plug tops 22.6 under the 23.5 lid
RISER_BAR = 1.3                                                    # frame bars along the long edges, inside the header-pad rows
RISER_SCREW = 16                                                   # M2.5 x 16 through level 2 (1.57), riser (6), level 1 (1.57) = 9.1, then 6.9 mm into the 7.5 mm pilots
# connector card: (x, hole dia, label); z centre = CONN_Z. Default two M12 panel receptacles (12.6 holes). Set CONNECTORS=blank for a blank card only.
CONN_Z = TRAY_FLOOR + (TRAY_CLEAR_H - FLANGE_T) / 2                # 11.5: centred in the 19 mm clear height under the card roof
CONNECTORS = [(W / 2 - 18.0, 12.6, "M12 A"), (W / 2 + 18.0, 12.6, "M12 B")]
CONN_DEPTH, CONN_BODY_D = 18.0, 15.0                               # behind-card body used for the clearance check (M12 solder-cup receptacle)
CARD_SCREWS = [(0.6, CONN_Z), (W - 0.6, CONN_Z)]                   # horizontal M2.5 x 8 self-tap into the front corner blocks, 3 mm from the card's ends
BLOCK_L = (0.0, CARD_Y1, 3.6, 6.0)                                 # x0, y0, x1, y1 front-left corner block
BLOCK_R = (69.0, CARD_Y1, W, 7.75)                                 # contains the P2 column
TRAY_COLS = {"P1": POSTS["P1"][:2], "P2": POSTS["P2"][:2], "S1": SADDLE_SCREWS["S1"], "S2": SADDLE_SCREWS["S2"]}   # P4 is a stepped corner block
P4 = POSTS["P4"][:2]
P4_LOW = (0.0, 93.25, 7.5, D, 3.5)                                 # x0 y0 x1 y1 z1: head pocket zone, the proto overhangs it from z 4
P4_UP = (0.0, 94.4, 7.0, D)                                        # 0.5 mm wall outside the 5.0 driver channel (a face exactly tangent to the channel made Onshape's regen fail); 0.3 from the proto edge
S2_BRIDGE = (SADDLE_SCREWS["S2"][0], SADDLE_SCREWS["S2"][1] - COL_D / 2, W, SADDLE_SCREWS["S2"][1] + COL_D / 2)

def tray_cables():
    """Tray-side cables (tray xy, tray z). T1 = box SHT41 rear -> drop slot -> ADS level-2 rear (100 mm; the box part is C4 in cables()).
    T2 = ADS level-1 front -> level-2 front hairpin (50 mm): a vertical loop in front of the stack."""
    z1 = Z_ADS1 + PCB + 2.0; z2 = Z_ADS2 + PCB + 2.0
    tip_rear = ADS["y"] + ADS["d"] + 12.7 - 2.54
    t1 = [(DROP["x"] - 3.0, DROP["y"], TRAY_H + 0.5), (DROP["x"] - 3.0, DROP["y"], z2), (ADS_CONN_X, DROP["y"] - 2.0, z2), (ADS_CONN_X, tip_rear, z2)]
    tip_front = ADS["y"] + 2.667 - 12.7
    loop = (50 - 2 * 8.2) / math.pi   # a 50 mm cable: 8.2 mm of wire sits inside each 12.7 reach; the rest forms a ~10.7 mm loop in front of the stack
    t2 = [(ADS_CONN_X, tip_front, z1), (ADS_CONN_X, tip_front - loop, (z1 + z2) / 2), (ADS_CONN_X, tip_front, z2)]
    return [("T1 drop slot -> ADS2 rear", t1), ("T2 ADS1 front -> ADS2 front (hairpin)", t2)]

def tray_envelopes():
    E = []
    E.append(Env("pcb proto", (PROTO["x"], PROTO["y"], Z_BRD), (PROTO["x"] + PROTO["w"], PROTO["y"] + PROTO["d"], Z_PROTO_TOP), "pcb"))
    E.append(Env("proto parts volume", (PROTO["x"] + 1, PROTO["y"] + 1, Z_PROTO_TOP), (PROTO["x"] + PROTO["w"] - 1, PROTO["y"] + PROTO["d"] - 1, TRAY_H - 0.5), "part"))
    for lvl, z0 in (("1", Z_ADS1), ("2", Z_ADS2)):
        E.append(Env(f"pcb ads{lvl}", (ADS["x"], ADS["y"], z0), (ADS["x"] + ADS["w"], ADS["y"] + ADS["d"], z0 + PCB), "pcb"))
        E += side_connector_envs(f"ads{lvl} front", (ADS_CONN_X, ADS["y"] + 2.667), (0, -1), True, f"pcb ads{lvl}", z0 + PCB)
        E += side_connector_envs(f"ads{lvl} rear", (ADS_CONN_X, ADS["y"] + ADS["d"] - 2.667), (0, 1), lvl == "2", f"pcb ads{lvl}", z0 + PCB)
    for x, y in ADS_HOLES:
        E.append(Env("standoff ads", (max(x - ADS_SO_D / 2, ADS_SO_FLAT_X), y - ADS_SO_D / 2, 0), (min(x + ADS_SO_D / 2, W), y + ADS_SO_D / 2, Z_ADS1), "boss"))
        E.append(Env("riser sleeve", (x - 2.5, y - 2.5, Z_ADS1 + PCB), (x + 2.5, y + 2.5, Z_ADS2), "boss"))
    E.append(Env("riser cross bar", (ADS["x"] + 0.2, ADS["y"] + ADS["d"] / 2 - 1.0, Z_ADS2 - 2.0), (ADS["x"] + ADS["w"] - 0.2, ADS["y"] + ADS["d"] / 2 + 1.0, Z_ADS2), "boss"))
    for x, y in PROTO_SCREWS: E.append(Env("standoff proto", (x - 3, y - 3, 0), (x + 3, y + 3, Z_BRD), "boss"))
    for x, y in PROTO_PADS: E.append(Env("pad proto", (x - 2.5, y - 2.5, 0), (x + 2.5, y + 2.5, Z_BRD), "boss"))
    for k, (cx, cy) in TRAY_COLS.items(): E.append(Env(f"column {k}", (cx - COL_D / 2, cy - COL_D / 2, 0), (cx + COL_D / 2, cy + COL_D / 2, TRAY_H), "tower"))
    E.append(Env("block P4 low", (P4_LOW[0], P4_LOW[1], 0), (P4_LOW[2], P4_LOW[3], P4_LOW[4]), "tower")); E.append(Env("block P4", (P4_UP[0], P4_UP[1], 0), (P4_UP[2], P4_UP[3], TRAY_H), "tower"))
    E.append(Env("block front-left", (BLOCK_L[0], BLOCK_L[1], 0), (BLOCK_L[2], BLOCK_L[3], TRAY_H), "tower")); E.append(Env("block front-right", (BLOCK_R[0], BLOCK_R[1], 0), (BLOCK_R[2], BLOCK_R[3], TRAY_H), "tower"))
    E.append(Env("bridge S2", (S2_BRIDGE[0], S2_BRIDGE[1], 0), (S2_BRIDGE[2], S2_BRIDGE[3], TRAY_H), "tower"))
    for edge, c, a in PROTO_HOOKS:
        if edge == "left": E.append(Env("proto hook", (c - 1.8, a - 1.25, 0), (c - 0.2, a + 1.25, Z_PROTO_TOP + 1.5), "part"))
        else: E.append(Env("proto hook", (a - 1.25, c - 1.8, 0), (a + 1.25, c - 0.2, Z_PROTO_TOP + 1.5), "part"))
    for x, d, lab in CONNECTORS:
        E.append(Env(f"connector body {lab}", (x - CONN_BODY_D / 2, CARD_Y1, CONN_Z - CONN_BODY_D / 2), (x + CONN_BODY_D / 2, CARD_Y1 + CONN_DEPTH, CONN_Z + CONN_BODY_D / 2), "part"))
    E.append(Env("card", (-WALL, CARD_Y0, 0), (W + WALL, CARD_Y1, TRAY_H), "wall")); E.append(Env("card roof", (-WALL, CARD_Y0, TRAY_H - FLANGE_T), (W + WALL, -WALL, TRAY_H), "wall"))
    E.append(Env("wall left", (-WALL, CARD_Y0, 0), (0, D + WALL, TRAY_H), "wall"))
    E.append(Env("wall right front", (W, CARD_Y0, 0), (W + WALL, WALL_RELIEF[1], TRAY_H), "wall")); E.append(Env("wall right back", (W, WALL_RELIEF[2], 0), (W + WALL, D + WALL, TRAY_H), "wall"))
    E.append(Env("wall right relief", (W + 0.5, WALL_RELIEF[1], 0), (W + WALL, WALL_RELIEF[2], TRAY_H), "wall"))
    E.append(Env("wall back", (-WALL, D, 0), (W + WALL, D + WALL, TRAY_H), "wall")); E.append(Env("lid (sled plate)", (-WALL, -WALL, TRAY_H), (W + WALL, D + WALL, TRAY_H + PLATE_T), "wall"))
    E.append(Env("floor", (-WALL, CARD_Y0, 0), (W + WALL, D + WALL, TRAY_FLOOR), "wall"))
    E.append(Env("drop slot (sled)", (DROP["x"] - DROP["w"] / 2, DROP["y"] - DROP["d"] / 2, TRAY_H), (DROP["x"] + DROP["w"] / 2, DROP["y"] + DROP["d"] / 2, TRAY_H + PLATE_T), "slot"))
    for name, pts in tray_cables():
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            pad = 1.0
            E.append(Env(f"{name} seg{i+1}", (min(a[0], b[0]) - pad, min(a[1], b[1]) - pad, min(a[2], b[2]) - pad), (max(a[0], b[0]) + pad, max(a[1], b[1]) + pad, max(a[2], b[2]) + pad), "cable",
                         "pcb ads2" if (i == len(pts) - 2 and "T1" in name) else None))
    return E

def tray_validate():
    E = tray_envelopes()
    # the ADS plug envelopes (6.6 wide over the full 12.7 reach) overlap the S2 / P2 columns in plan; the real housings end well short of them and the
    # 1.5 mm cable runs 0.9 mm inside the column faces, so those pairs are replaced by the explicit margin checks below
    problems, notes = clearance_report(E, skip_pairs=(("cable", "lid"), ("cable", "drop slot"), ("cable", "conn ads"), ("cable", "plug ads"),
                                                      ("plug", "column S2"), ("plug", "column P2"), ("plug", "block front-right")))
    rear_housing_end, front_housing_end = ADS["y"] + ADS["d"] + 4.5, ADS["y"] - 4.5
    m_rear = S2_BRIDGE[1] - rear_housing_end; m_front = front_housing_end - BLOCK_R[3]; m_x = BLOCK_R[0] - (ADS_CONN_X + 0.75)
    notes.append(f"ADS plugs: rear housing {m_rear:.1f} mm before the S2 column, front housing {m_front:.1f} mm behind the P2 block, cable {m_x:.1f} mm from the column faces")
    if m_rear < 1.0 or m_front < 1.0 or m_x < 0.5: problems.append("ADS plug housings or cables too close to the S2 / P2 columns")
    eps = 1e-6
    if PROTO["x"] - P4_UP[2] < 0.3 - eps: problems.append("proto board touches the P4 block")
    if ADS["x"] - (PROTO["x"] + PROTO["w"]) < 0.3 - eps: problems.append("ADS stack touches the proto board")
    if W + 0.5 - (ADS["x"] + ADS["w"]) < 0.5 - eps: problems.append("ADS stack touches the right wall")
    if P4[0] + P_CHAN_D / 2 > P4_UP[2] - 0.4 + eps: problems.append("P4 driver channel too close to the block face (tangent faces fail in Onshape)")
    notes.append(f"gaps: P4 block to proto {PROTO['x'] - P4_UP[2]:.2f}, proto to ADS {ADS['x'] - PROTO['x'] - PROTO['w']:.2f}, ADS to wall {W + 0.5 - ADS['x'] - ADS['w']:.2f}, P4 channel wall {P4_UP[2] - P4[0] - P_CHAN_D / 2:.2f}")
    statics = [e for e in E if e.kind in ("pcb", "part", "boss", "tower", "wall")]
    printed = [e for e in E if e.kind in ("boss", "tower") or e.name.startswith("proto hook") or e.name.startswith("connector body")]
    for a in printed:
        for b in statics:
            if a is b or b.kind == "wall": continue                       # everything printed grows out of the floor / walls
            if a.name.startswith(("standoff", "pad", "riser")) and b.kind == "pcb": continue
            if a.name.startswith("proto hook") and b.name == "pcb proto": continue
            if a.kind == "tower" and b.kind == "tower": continue
            if a.name.startswith("connector body") and b.kind == "wall": continue
            if a.overlaps(b): problems.append(f"TRAY STATIC {a.name}  intersects  {b.name}")
    # plug envelopes vs walls and the card are covered by clearance_report (kind wall)
    if Z_ADS1 + PCB + 5.0 > Z_ADS2 - 0.5: problems.append("ADS level-2 PCB sits on the level-1 plug housings")
    if Z_ADS2 + PCB + 5.0 > TRAY_H - 0.5: problems.append("ADS level-2 plug housings hit the lid")
    if CONN_BODY_D > TRAY_CLEAR_H - FLANGE_T - 0.6: problems.append("connector body taller than the clear height under the card roof")
    pilot = ADS_SO_H + TRAY_FLOOR - 0.5 - 0.5   # pilot from the standoff top to 0.5 mm above the tray bottom, keep 0.5 mm of thread room
    stack = 2 * PCB + RISER_H
    if RISER_SCREW > stack + pilot: problems.append(f"ADS stack screw M2.5 x {RISER_SCREW} bottoms out ({RISER_SCREW - stack:.1f} mm into a {pilot:.1f} mm pilot)")
    if RISER_SCREW - stack < 4.0: problems.append(f"ADS stack screw M2.5 x {RISER_SCREW} engages only {RISER_SCREW - stack:.1f} mm")
    notes.append(f"ADS stack: M2.5 x {RISER_SCREW} engages {RISER_SCREW - stack:.1f} mm of a {pilot:.1f} mm pilot; proto M2.5 x 6 engages {6 - PROTO['t']:.1f}; card M2.5 x 8 engages {8 - CARD_T:.1f} of 6.0")
    p_thread = P_SCREW - (TRAY_H - P_SEAT) - PLATE_T - PLATEAU_T
    notes.append(f"shell screws M2.5 x {P_SCREW:.0f}: head seat {P_SEAT:.1f} mm up the column, {p_thread:.1f} mm into the shell inserts (bore {BORE_POST}); sled screws M2.5 x {S_SCREW:.0f}: {S_SCREW - PLATE_T - PLATEAU_T:.1f} mm into the column-top inserts; base screws M2.5 x {BASE_SCREW:.0f} from below: {BASE_SCREW - SADDLE_T - 3.0:.1f} mm into the column-bottom pilots (5.5 deep)")
    if not 4.0 <= p_thread <= BORE_POST - 0.5: problems.append("shell screw length wrong for the tray height")
    if not 4.0 <= S_SCREW - PLATE_T - PLATEAU_T <= INSERT_DEPTH: problems.append("sled screw length wrong for the column-top inserts")
    if not 3.5 <= BASE_SCREW - SADDLE_T - 3.0 <= 5.0: problems.append("base screw length wrong for the column-bottom pilots")
    if P_SEAT < 3.0: problems.append("shell screw head seat too close to the tray bottom")
    wall_d = (ADS_HOLES[0][0] - HOLE_M25 / 2) - ADS_SO_FLAT_X
    notes.append(f"ADS standoff wall at the D flat: {wall_d:.2f} mm (sled standoffs 1.80)")
    if wall_d < 1.4: problems.append("ADS D-standoff wall under 1.4 mm: self-tapping would split it")
    for x, z in CARD_SCREWS:
        if x - HOLE_M25 / 2 < -WALL or x + HOLE_M25 / 2 > W + WALL: problems.append("card screw pilot breaks out of the tray")
    t2 = tray_cables()[1][1]; wire = polyline_length(t2) * 1.1 + 2 * 8.2   # loop (10 % for the curve) + the wire inside both reaches
    notes.append(f"T2 hairpin: {wire:.0f} mm of wire for a 50 mm cable; loop reaches y {t2[1][1]:.1f}, card inner face at {CARD_Y1}")
    if wire > 50: problems.append("T2 hairpin needs more than a 50 mm cable")
    if t2[1][1] - 1.0 < CARD_Y1: problems.append("T2 hairpin loop touches the connector card")
    return E, problems, notes

# ------------------------------------------------------------------ derived: standoffs
def standoffs():
    S = []  # (x, y, hole_d, label)
    S += [(X_STK0 + 2.54, Y_STK0 + 2.54, HOLE_M25, "feather A"), (X_STK0 + 2.54, Y_STK0 + 20.32, HOLE_M25, "feather B"),
          (X_STK0 + 48.26, Y_STK0 + 1.84, HOLE_M2, "feather C (M2)"), (X_STK0 + 48.26, Y_STK0 + 20.96, HOLE_M2, "feather D (M2)")]
    for dx in (2.54, 22.86):
        for dy in (2.54, 22.86):
            S.append((GPS["x"] + dx, GPS["y"] + dy, HOLE_M25, "gps pillar", Z_GPS_DECK, 7.0))   # tall pillars, 7 mm dia
    S += [(IMU["x"] + 2.54, IMU["y"] + 2.54, HOLE_M25, "imu"), (IMU["x"] + 2.54, IMU["y"] + 22.86, HOLE_M25, "imu")]
    S += [(SHT["x"] + 2.54, SHT["y"] + 2.54, HOLE_M25, "sht"), (SHT["x"] + 15.24, SHT["y"] + 22.86, HOLE_M25, "sht")]
    pads = [(SHT["x"] + 15.24, SHT["y"] + 2.54), (SHT["x"] + 2.54, SHT["y"] + 22.86)]  # plain support pads
    return S, pads
STANDOFFS, PADS = standoffs()
def so_geom(t): return (t[4] if len(t) > 4 else STANDOFF, t[5] if len(t) > 5 else 6.0)
IMU_LEDGE = dict(x0=IMU["x"] + 14.2, x1=IMU["x"] + 15.8, y0=IMU["y"] + 3.0, y1=IMU["y"] + 22.4)  # under the pad-only edge
HOOKS = [(IMU["x"] + IMU["w"] + 0.2, IMU["y"] + 2.0), (IMU["x"] + IMU["w"] + 0.2, IMU["y"] + 23.4)]  # snap hooks beside the pad edge
RIBS = [(30.6, 66.6, 35.4, 67.8), (5.8, 20.0, 7.0, 62.0)]   # front-lane run is only 4.8 mm long; the wall alone guides it   # (x0,y0,x1,y1) 8 mm tall channel walls: middle-lane run, left-wall run, front-lane run
RIB_H = 8.0

# ------------------------------------------------------------------ cables (3D polylines between plug tips)
Z_SENSOR_PLUG = ZF + 1.5
def cables():
    zq = (QT["z0"] + QT["z1"]) / 2
    zg = Z_GPS_DECK + PCB + 1.5   # GPS plug height on the deck
    c1 = [(QT["cx"] - 12.7, QT["cy"], zq), (7.0, QT["cy"] - 8.0, zq), (3.8, 65.0, zq), (3.8, Y_ROW0 - 12.5, zg), (GPS_CONN_X, Y_ROW0 - 12.5, zg)]
    c2 = [(GPS_CONN_X, Y_ROW1 + 12.7 - 2.54, zg), (GPS_CONN_X, Y_ROW1 + 12.5, zg), (GPS_CONN_X + 8, Y_ROW1 + 20.5, zg - 6.0),
          (IMU_CONN_X - 8, Y_ROW1 + 20.5, Z_SENSOR_PLUG + 7.0), (IMU_CONN_X, Y_ROW1 + 12.5, Z_SENSOR_PLUG), (IMU_CONN_X, Y_ROW1 + 12.7 - 2.54, Z_SENSOR_PLUG)]
    c3 = [(IMU_CONN_X, Y_ROW0 - 12.7 + 2.54, Z_SENSOR_PLUG), (IMU_CONN_X, Y_ROW0 - 12.5, Z_SENSOR_PLUG), (IMU_CONN_X + 8, Y_ROW0 - 20.5, Z_SENSOR_PLUG),
          (SHT_CONN_X - 8, Y_ROW0 - 20.5, Z_SENSOR_PLUG), (SHT_CONN_X, Y_ROW0 - 12.5, Z_SENSOR_PLUG), (SHT_CONN_X, Y_ROW0 - 12.7 + 3.175, Z_SENSOR_PLUG)]
    # (name, polyline, source-connector name, target-connector name, stock length)
    # C4 (v2 analog tray): SHT41 spare rear port -> 4 mm straight -> down the drop slot -> ADS level-2 rear port in the tray (tray_cables() T1 is the tray half)
    zt = Z_TRAY_BOT + Z_ADS2 + PCB + 2.0
    c4 = [(SHT_CONN_X, Y_ROW1 - 3.175 + 12.7, Z_SENSOR_PLUG), (SHT_CONN_X, DROP["y"], Z_SENSOR_PLUG), (DROP["x"] - 3.0, DROP["y"], Z_PLATE_BOT - 1.0), (DROP["x"] - 3.0, DROP["y"], zt),
          (ADS_CONN_X, DROP["y"] - 2.0, zt), (ADS_CONN_X, ADS["y"] + ADS["d"] + 12.7 - 2.54, zt)]
    return [("C1 OLED QT -> GPS front", c1, "conn oled qt", "conn gps front", 200),
            ("C2 GPS rear -> IMU rear", c2, "conn gps rear", "conn imu rear", 100),
            ("C3 IMU front -> SHT41 front", c3, "conn imu front", "conn sht front", 100),
            ("C4 SHT41 rear -> tray ADS2 rear (v2)", c4, "conn sht rear", "conn ads2 rear", 100)]

def route_length(pts, arc_allow=3.0):
    """Polyline length plus a per-corner allowance (arcs are approximated by corners) plus the two plug reaches."""
    L = 0.0
    for a, b in zip(pts, pts[1:]):
        L += math.dist(a, b)
    return L + arc_allow * (len(pts) - 2) + 2 * 5.5   # wire starts ~7.2 mm from the connector centre; polylines start at 12.7

# ------------------------------------------------------------------ envelopes + validation
def envelopes():
    E = []
    def pcb(name, x, y, w, d, z0=STANDOFF): E.append(Env(name, (x, y, z0), (x + w, y + d, z0 + PCB), "pcb"))
    pcb("pcb feather", X_STK0, Y_STK0, STACK_L, STACK_D); pcb("pcb adalogger", X_STK0, Y_STK0, STACK_L, STACK_D, Z_ADA)
    pcb("pcb oled wing", X_STK0, Y_STK0, STACK_L, STACK_D, Z_OLED)
    pcb("pcb gps", GPS["x"], GPS["y"], GPS["w"], GPS["d"], Z_GPS_DECK); pcb("pcb imu", IMU["x"], IMU["y"], IMU["w"], IMU["d"]); pcb("pcb sht41", SHT["x"], SHT["y"], SHT["w"], SHT["d"])
    E.append(Env("oled glass", (GLASS["x0"], GLASS["y0"], Z_OLED + 1.57), (GLASS["x1"], GLASS["y1"], Z_GLASS_TOP), "part"))
    E.append(Env("usb receptacle", (X_STK0 - 1.1, USB_Y - 4.45, ZF - 0.98), (X_STK0 + 6.8, USB_Y + 4.45, ZF + 3.22), "part"))
    E.append(Env("usb plug body (in chute)", (CH_WALL + 0.5, USB_Y - 6.0, CH_IN_Z0), (X_STK0 - 1.1, USB_Y + 6.0, CH_IN_Z1), "part"))
    E.append(Env("esp32 module", (X_STK0 + 30.64, Y_STK0 + 3.73, ZF), (X_STK0 + 51.14, Y_STK0 + 19.13, ZF + 2.55), "part"))
    E.append(Env("stack sockets front", (X_STK0 + 1.5, Y_STK0, ZF), (X_STK0 + 49.3, Y_STK0 + 2.6, Z_OLED), "part"))
    E.append(Env("stack sockets back", (X_STK0 + 1.5, Y_STK1 - 2.6, ZF), (X_STK0 + 49.3, Y_STK1, Z_OLED), "part"))
    E.append(Env("coin cell holder", (X_STK0 + 2.5, Y_STK0 + 5.3, Z_ADA + 1.57), (X_STK0 + 17.7, Y_STK0 + 20.3, Z_ADA + 1.57 + 4.0), "part"))
    E.append(Env("gps patch", (GPS_PATCH[0] - 5, GPS_PATCH[1] - 5, Z_GPS_DECK + PCB), (GPS_PATCH[0] + 5, GPS_PATCH[1] + 5, Z_GPS_DECK + PCB + 6.4), "part"))
    # sensor connectors (side entry, rotated so they face +-Y). centre = connector centre on the board.
    pt = ZF
    E += side_connector_envs("gps front", (GPS_CONN_X, GPS["y"] + 2.54), (0, -1), True, "pcb gps", Z_GPS_DECK + PCB)
    E += side_connector_envs("gps rear", (GPS_CONN_X, GPS["y"] + 22.86), (0, 1), True, "pcb gps", Z_GPS_DECK + PCB)
    E += side_connector_envs("imu front", (IMU_CONN_X, IMU["y"] + 2.54), (0, -1), True, "pcb imu", pt)
    E += side_connector_envs("imu rear", (IMU_CONN_X, IMU["y"] + 22.86), (0, 1), True, "pcb imu", pt)
    E += side_connector_envs("sht front", (SHT_CONN_X, SHT["y"] + 3.175), (0, -1), True, "pcb sht41", pt)
    E += side_connector_envs("sht rear", (SHT_CONN_X, SHT["y"] + 22.225), (0, 1), True, "pcb sht41", pt)   # v2: C4 to the analog tray
    # OLED QT: hangs under the wing, exits -X
    E.append(Env("conn oled qt", (QT["cx"] - 2.5, QT["cy"] - 3.05, QT["z0"]), (QT["cx"] + 2.5, QT["cy"] + 3.05, QT["z1"]), "conn", "pcb oled wing"))
    E.append(Env("plug oled qt", (QT["cx"] - 12.7, QT["cy"] - 3.3, QT["z0"] - 1.0), (QT["cx"] - 2.7, QT["cy"] + 3.3, QT["z1"] + 1.0), "plug", "pcb oled wing"))
    # printed geometry
    for t in STANDOFFS:
        x, y, hd, lab = t[:4]; h, d = so_geom(t); E.append(Env(f"standoff {lab}", (x - d/2, y - d/2, 0), (x + d/2, y + d/2, h), "boss"))
    for x, y in PADS: E.append(Env("pad sht", (x - 2.5, y - 2.5, 0), (x + 2.5, y + 2.5, STANDOFF), "boss"))
    E.append(Env("imu ledge", (IMU_LEDGE["x0"], IMU_LEDGE["y0"], 0), (IMU_LEDGE["x1"], IMU_LEDGE["y1"], STANDOFF), "boss"))
    for i, (hx, hy) in enumerate(HOOKS): E.append(Env(f"imu hook {i}", (hx, hy - 1.25, 0), (hx + 1.6, hy + 1.25, ZF + 0.8), "part"))
    for k, (px, py, kind) in POSTS.items():
        E.append(Env(f"post {k}", (px - 4, py - 4, 0), (px + 4, py + 4, H_INT), "tower"))
    E.append(Env("pad P3", (PAD_P3[0] - 4, PAD_P3[1] - 4, 0), (PAD_P3[0] + 4, PAD_P3[1] + 4, H_INT), "tower"))
    for k, (sx, sy) in SADDLE_SCREWS.items(): E.append(Env(f"saddle screw head {k}", (sx - 2.5, sy - 2.5, 0), (sx + 2.5, sy + 2.5, 2.0), "part"))
    E.append(Env("usb chute", (CH_X0, CH_Y0, 0), (CH_X1, CH_Y1, CH_IN_Z1 + 0.6), "part"))
    E.append(Env("future drop slot", (DROP["x"] - 5, DROP["y"] - 2.5, -4), (DROP["x"] + 5, DROP["y"] + 2.5, 0.5), "slot"))
    for i, (x0, y0, x1, y1) in enumerate(RIBS): E.append(Env(f"rib {i}", (x0, y0, 0), (x1, y1, RIB_H), "part"))
    E.append(Env("wall left", (-WALL, -WALL, -PLATEAU_T), (0, D + WALL, Z_ROOF_TOP), "wall")); E.append(Env("wall right", (W, -WALL, -PLATEAU_T), (W + WALL, D + WALL, Z_ROOF_TOP), "wall"))
    E.append(Env("wall front", (-WALL, -WALL, -PLATEAU_T), (W + WALL, 0, Z_ROOF_TOP), "wall")); E.append(Env("wall back", (-WALL, D, -PLATEAU_T), (W + WALL, D + WALL, Z_ROOF_TOP), "wall"))
    E.append(Env("roof", (-WALL, -WALL, H_INT), (W + WALL, D + WALL, Z_ROOF_TOP), "wall"))
    # cables as segment boxes
    for name, pts, src, dst, stock in cables():
        n = len(pts) - 1
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            if min(a[2], b[2]) < Z_PLATE_BOT: continue   # below the sled plate: tray side, checked by tray_validate()
            pad = 1.75
            owner = src if i == 0 else (dst if i == n - 1 else None)
            E.append(Env(f"{name} seg{i+1}", (min(a[0], b[0]) - pad, min(a[1], b[1]) - pad, min(a[2], b[2]) - pad),
                         (max(a[0], b[0]) + pad, max(a[1], b[1]) + pad, max(a[2], b[2]) + pad), "cable", owner))
    return E

def validate():
    E = envelopes()
    # the SHT41 rear plug envelope (6.6 wide for the full 12.7 reach) clips the P3 bearing pad by 0.6 mm; the real housing ends 3 mm before the pad and C4 turns toward the drop slot
    problems, notes = clearance_report(E, skip_pairs=(("plug", "pad P3"),))
    # static-vs-static: printed geometry must not intersect boards or each other
    statics = [e for e in E if e.kind in ("pcb", "part", "boss", "tower", "conn")]
    printed = [e for e in E if e.kind in ("boss", "tower") or e.name.startswith(("usb chute", "rib", "imu hook"))]
    seen = set()
    for a in printed:
        for b in statics:
            if a is b or (b.name, a.name) in seen: continue
            if a.name.startswith("standoff") and b.kind == "pcb": continue      # standoffs touch PCB undersides by design
            if a.name.startswith("pad") and b.kind == "pcb": continue
            if a.name == "imu ledge" and b.kind == "pcb": continue
            if a.name.startswith("imu hook") and b.name == "pcb imu": continue
            if a.name == "usb chute" and b.name.startswith("usb plug"): continue
            if a.overlaps(b): problems.append(f"STATIC {a.name}  intersects  {b.name}"); seen.add((a.name, b.name))
    # plug envelopes vs walls/posts handled by clearance_report (walls are 'wall' kind)
    # cable lengths
    table = []
    for name, pts, src, dst, stock in cables():
        L = route_length(pts)
        ok = L <= stock - 10
        table.append((name, round(L), stock, "ok" if ok else "TOO SHORT"))
        if not ok: problems.append(f"{name}: route {L:.0f} mm exceeds {stock} mm stock minus 10 mm slack")
    # geometry sanity
    if X_STK0 - 2.7 - 10 - 8 < 3.0: problems.append("USB lane too narrow for the OLED QT straight + 8 mm bend")
    if LANE_F < 12.7 + 8 + 1.5 + 1.0 or LANE_M < 12.7 + 8 + 1.5 + 1.0: problems.append("a cable lane is narrower than plug reach + bend radius")
    if GPS["x"] < 3.8 + 1.5 + 1.0: problems.append("GPS too close to the left wall for the cable run")
    Et, tp, tn = tray_validate(); problems += tp; notes += tn
    return E, problems, notes, table

# ------------------------------------------------------------------ FeatureScript emission
class FS:
    """FeatureScript emitter. With `local` on, every primitive is also built with CadQuery (same coordinates) so parts can be exported and
    rendered without an Onshape push. Raw opChamfer lines (hook lips) are skipped locally; everything else is mirrored."""
    def __init__(self): self.lines = []; self.n = 0; self.local = False; self.cq = {}; self.parts = {}
    def uid(self, tag): self.n += 1; return f'id + "{tag}{self.n}"'
    def w(self, s): self.lines.append("        " + s)
    def _cq(self):
        import cadquery as cq; return cq
    def box(self, x0, y0, z0, x1, y1, z1, tag="b"):
        v = self.uid(tag); n = v.split()[-1][1:-1]
        self.w(f"var {n} = mkBox(context, {v}, {min(x0,x1):.3f}, {min(y0,y1):.3f}, {min(z0,z1):.3f}, {max(x0,x1):.3f}, {max(y0,y1):.3f}, {max(z0,z1):.3f});")
        if self.local:
            cq = self._cq(); self.cq[n] = cq.Solid.makeBox(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), cq.Vector(min(x0, x1), min(y0, y1), min(z0, z1)))
        return n
    def cylz(self, cx, cy, z0, z1, d, tag="c"):
        v = self.uid(tag); n = v.split()[-1][1:-1]; self.w(f"var {n} = cylZ(context, {v}, {cx:.3f}, {cy:.3f}, {min(z0,z1):.3f}, {max(z0,z1):.3f}, {d:.3f});")
        if self.local: cq = self._cq(); self.cq[n] = cq.Solid.makeCylinder(d / 2, abs(z1 - z0), cq.Vector(cx, cy, min(z0, z1)), cq.Vector(0, 0, 1))
        return n
    def cylx(self, cy, cz, x0, x1, r, tag="cx"):
        v = self.uid(tag); n = v.split()[-1][1:-1]; self.w(f"var {n} = cylX(context, {v}, {cy:.3f}, {cz:.3f}, {x0:.3f}, {x1:.3f}, {r});")
        if self.local: cq = self._cq(); self.cq[n] = cq.Solid.makeCylinder(r, abs(x1 - x0), cq.Vector(min(x0, x1), cy, cz), cq.Vector(1, 0, 0))
        return n
    def cyly(self, cx, cz, y0, y1, r, tag="cy"):
        v = self.uid(tag); n = v.split()[-1][1:-1]; self.w(f"var {n} = cylY(context, {v}, {cx:.3f}, {cz:.3f}, {y0:.3f}, {y1:.3f}, {r});")
        if self.local: cq = self._cq(); self.cq[n] = cq.Solid.makeCylinder(r, abs(y1 - y0), cq.Vector(cx, min(y0, y1), cz), cq.Vector(0, 1, 0))
        return n
    def lip_chamfer(self, body, par, far, w=0.7, tag="lc"):
        """Chamfer the edge of `body` parallel to `par` that lies farthest along `far` (the lip's lower edge facing the board). Not mirrored locally."""
        self.w(f'opChamfer(context, {self.uid(tag)}, {{ "entities" : qFarthestAlong(qParallelEdges(qOwnedByBody({body}, EntityType.EDGE), vector({par[0]}, {par[1]}, {par[2]})), vector({far[0]}, {far[1]}, {far[2]})), "chamferType" : ChamferType.EQUAL_OFFSETS, "width" : {w} * millimeter }});')
    def unite(self, names, tag="u"):
        v = self.uid(tag); n = v.split()[-1][1:-1]; self.w(f"var {n} = mkUnite(context, {v}, [{', '.join(names)}]);")
        if self.local:
            b = self.cq[names[0]]
            if len(names) > 1: b = b.fuse(*[self.cq[k] for k in names[1:]], glue=False).clean()
            self.cq[n] = b
        return n
    def cut(self, target, tools, tag="k"):
        if not tools: return target
        v = self.uid(tag); n = v.split()[-1][1:-1]; self.w(f"var {n} = mkCut(context, {v}, {target}, [{', '.join(tools)}]);")
        if self.local: self.cq[n] = self.cq[target].cut(*[self.cq[k] for k in tools]).clean()
        return n
    def intersect(self, target, tools, tag="i"):
        v = self.uid(tag); n = v.split()[-1][1:-1]; self.w(f"var {n} = mkIntersect(context, {v}, {target}, [{', '.join(tools)}]);")
        if self.local:
            b = self.cq[target]
            for k in tools: b = b.intersect(self.cq[k])
            self.cq[n] = b
        return n
    def _edge_op(self, body, selector, op, val):
        if not self.local: return
        cq = self._cq()
        try:
            wp = cq.Workplane("XY").newObject([self.cq[body]])
            wp = wp.faces(selector).edges() if selector.startswith(("<", ">")) else wp.edges(selector)
            self.cq[body] = (wp.fillet(val) if op == "fillet" else wp.chamfer(val)).val()
        except Exception as e: print(f"  local: {op} {selector} skipped on {body}: {str(e)[:60]}")
    def filletz(self, body, r, tag="f"):
        v = self.uid(tag); self.w(f"filletZ(context, {v}, {body}, {r});"); self._edge_op(body, "|Z", "fillet", r)
    def filletx(self, body, r, tag="fx"):
        v = self.uid(tag); self.w(f"filletX(context, {v}, {body}, {r});"); self._edge_op(body, "|X", "fillet", r)
    def chamfer_bottom(self, body, w, tag="cb"):
        v = self.uid(tag); self.w(f"chamferBottom(context, {v}, {body}, {w});"); self._edge_op(body, "<Z", "chamfer", w)
    def chamfer_top(self, body, w, tag="ch"):
        v = self.uid(tag); self.w(f"chamferTop(context, {v}, {body}, {w});"); self._edge_op(body, ">Z", "chamfer", w)
    def rotz(self, body, cx, cy, ang, tag="r"):
        v = self.uid(tag); self.w(f"rotZ(context, {v}, {body}, {cx:.3f}, {cy:.3f}, {ang});")
        if self.local: cq = self._cq(); self.cq[body] = self.cq[body].rotate(cq.Vector(cx, cy, 0), cq.Vector(cx, cy, 1), ang)
    def name(self, body, label, rgb):
        self.w(f'nameBody(context, {body}, "{label}", color({rgb[0]}, {rgb[1]}, {rgb[2]}));')
        if self.local: self.parts[label] = self.cq[body]

def export_local(fs):
    """Write the locally built parts to output/*.stl with the same names the Onshape export uses, and check each is one manifold body."""
    import cadquery as cq, pyvista as pv
    for label, shape in fs.parts.items():
        fn = OUT / (label.replace(" ", "_").lower() + ".stl")
        cq.exporters.export(cq.Workplane("XY").newObject([shape]), str(fn), tolerance=0.04, angularTolerance=0.08)
        m = pv.read(str(fn)).clean(); bodies = len(set(m.connectivity()["RegionId"]))   # CadQuery writes unmerged triangles; merge before judging
        print(f"  local  {fn.name} ({fn.stat().st_size // 1024} kB) bodies={bodies} manifold={m.is_manifold}  (local mirror: for renders and fit checks; print from the Onshape export)")
        if bodies != 1: raise SystemExit(f"{label} built locally as {bodies} bodies")

def emit_fs(local=False):
    fs = FS()
    # ---------------- SHELL
    fs.w("if (definition.buildShell) {")
    sh = fs.box(-WALL, -WALL, Z_PLATE_TOP, W + WALL, D + WALL, Z_ROOF_TOP, "shell")
    fs.filletz(sh, R_VERT); fs.chamfer_top(sh, CHAMF_ROOF)
    cav = fs.box(0, 0, Z_PLATE_TOP - 0.5, W, D, H_INT, "cav")
    sh = fs.cut(sh, [cav])
    posts = [fs.box(px - 4, py - 4, 0, px + 4, py + 4, H_INT + 0.5, "post") for k, (px, py, kind) in POSTS.items()]
    posts.append(fs.box(PAD_P3[0] - 4, PAD_P3[1] - 4, 0, PAD_P3[0] + 4, PAD_P3[1] + 4, H_INT + 0.5, "padp3"))
    sh = fs.unite([sh] + posts)
    tools = []
    for k, (px, py, kind) in POSTS.items():
        tools.append(fs.cylz(px, py, -0.5, BORE_POST, INSERT_D, "bore")); tools.append(fs.cylz(px, py, -0.5, INSERT_SEAT_H, INSERT_SEAT_D, "seat"))
    # window = glass + 0.3 per side, 1.5 mm corners; 1.0 mm inner-face pocket for an optional 1 mm PC sheet (window + 1.5 per side)
    win = fs.box(GLASS["x0"] - 0.3, GLASS["y0"] - 0.3, H_INT - 1, GLASS["x1"] + 0.3, GLASS["y1"] + 0.3, Z_ROOF_TOP + 1, "win"); fs.filletz(win, R_WIN); tools.append(win)
    pocket = fs.box(GLASS["x0"] - 1.8, GLASS["y0"] - 1.8, H_INT - 1, GLASS["x1"] + 1.8, GLASS["y1"] + 1.8, H_INT + 1.0, "winpocket"); fs.filletz(pocket, R_WIN); tools.append(pocket)
    # flexure keys: three flaps FLAP_L long (hinge at -X), FLAP_T thick, flush with the roof (no top recess: bed face stays flat)
    hinge = BTN_X - 6.5; tip = hinge + FLAP_L
    comb = fs.box(hinge, BTN_Y[0] - FLAP_W/2 - SLOT_W, H_INT - 1, tip + SLOT_W, BTN_Y[-1] + FLAP_W/2 + SLOT_W, Z_ROOF_TOP + 1, "comb")
    flaps = [fs.box(hinge - 1, by - FLAP_W/2, H_INT - 2, tip, by + FLAP_W/2, Z_ROOF_TOP + 2, "flap") for by in BTN_Y]
    tools.append(fs.cut(comb, flaps, "combk"))
    tools.append(fs.box(hinge - 0.01, BTN_Y[0] - FLAP_W/2 - SLOT_W - 0.6, H_INT - 1, tip + SLOT_W + 0.6, BTN_Y[-1] + FLAP_W/2 + SLOT_W + 0.6, H_INT + (ROOF - FLAP_T), "kbpocket"))
    # A B C engraved as one, two, three dots beside the hinge ends
    for i, by in enumerate(BTN_Y):
        for j in range(i + 1): tools.append(fs.cylz(hinge - 2.4 - 1.9 * j, by, Z_ROOF_TOP - 0.4, Z_ROOF_TOP + 1, 1.2, "dot"))
    # reset key: round flap with a stem hinged toward the back wall (visually distinct from the pills)
    rk = RESET_KEY; ro = rk["r"] + SLOT_W
    ring = fs.cylz(rk["cx"], rk["cy"], H_INT - 1, Z_ROOF_TOP + 1, 2 * ro, "rring")
    sl1 = fs.box(rk["hinge_x"], rk["cy"] - rk["stem_w"]/2 - SLOT_W, H_INT - 1, rk["cx"], rk["cy"] - rk["stem_w"]/2, Z_ROOF_TOP + 1, "rsl")
    sl2 = fs.box(rk["hinge_x"], rk["cy"] + rk["stem_w"]/2, H_INT - 1, rk["cx"], rk["cy"] + rk["stem_w"]/2 + SLOT_W, Z_ROOF_TOP + 1, "rsl")
    rtool = fs.unite([ring, sl1, sl2], "ru")
    disc = fs.cylz(rk["cx"], rk["cy"], H_INT - 2, Z_ROOF_TOP + 2, 2 * rk["r"], "rdisc")
    stem = fs.box(rk["hinge_x"] - 1, rk["cy"] - rk["stem_w"]/2, H_INT - 2, rk["cx"] + 1, rk["cy"] + rk["stem_w"]/2, Z_ROOF_TOP + 2, "rstem")
    tools.append(fs.cut(rtool, [disc, stem], "rk"))
    tools.append(fs.box(rk["hinge_x"] - 0.01, rk["cy"] - ro - 0.6, H_INT - 1, rk["cx"] + ro + 0.6, rk["cy"] + ro + 0.6, H_INT + (ROOF - FLAP_T), "rpocket"))
    if LOGO_ON:
        xs = [x for pl in LOGO_POLYS for x, _ in pl]; ys = [y for pl in LOGO_POLYS for _, y in pl]
        sc = LOGO_W / (max(xs) - min(xs)); cx_s, cy_s = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        lh = LOGO_W * (max(ys) - min(ys)) / (max(xs) - min(xs))
        if LOGO_POS == "corner": lcx = FRAME["x1"] - LOGO_W / 2; lcy = 7.0 + lh / 2 - 0.6   # front-right, sharing the chevron's baseline
        else: lcx = FRAME["x1"] - LOGO_W / 2; lcy = GPS_PATCH[1]   # right edge on the frame's right edge, centreline shared with the GPS square
        def tf(x, y): return (lcx - sc * (x - cx_s), lcy + sc * (y - cy_s))   # 180 deg: reads correctly for the driver behind the box
        if LOGO_POS == "back":
            # back wall, facing the driver: sketch on the outer face (y = D + WALL), sketch x -> -X (driver's right), sketch y -> +Z
            lcx, lcz = W / 2, (Z_PLATE_TOP + H_INT) / 2 + 1.0
            def tfb(x, y): return (-(lcx - sc * (x - cx_s)), lcz - sc * (y - cy_s))
            fs.w(f'var lsk = newSketchOnPlane(context, id + "logoSk", {{ "sketchPlane" : plane(vector(0, {D + WALL}, 0) * millimeter, vector(0, 1, 0), vector(-1, 0, 0)) }});')
            for i, pl in enumerate(LOGO_POLYS):
                pts = [tfb(x, y) for x, y in pl]
                if pts[0] != pts[-1]: pts.append(pts[0])
                fs.w(f'skPolyline(lsk, "lp{i}", {{ "points" : [{", ".join(f"vector({x:.3f}, {y:.3f}) * millimeter" for x, y in pts)}] }});')
            fs.w('skSolve(lsk);')
            fs.w(f'opExtrude(context, id + "logoEx", {{ "entities" : qSketchRegion(id + "logoSk"), "direction" : vector(0, -1, 0), "endBound" : BoundingType.BLIND, "endDepth" : 0.4 * millimeter }});')
        else:
            fs.w(f'var lsk = newSketchOnPlane(context, id + "logoSk", {{ "sketchPlane" : plane(vector(0, 0, {Z_ROOF_TOP}) * millimeter, vector(0, 0, 1), vector(1, 0, 0)) }});')
            for i, pl in enumerate(LOGO_POLYS):
                pts = [tf(x, y) for x, y in pl]
                if pts[0] != pts[-1]: pts.append(pts[0])
                fs.w(f'skPolyline(lsk, "lp{i}", {{ "points" : [{", ".join(f"vector({x:.3f}, {y:.3f}) * millimeter" for x, y in pts)}] }});')
            fs.w('skSolve(lsk);')
            fs.w(f'opExtrude(context, id + "logoEx", {{ "entities" : qSketchRegion(id + "logoSk"), "direction" : vector(0, 0, -1), "endBound" : BoundingType.BLIND, "endDepth" : 0.4 * millimeter }});')
        fs.w('var logoBodies = qCreatedBy(id + "logoEx", EntityType.BODY);')
        tools.append("logoBodies")
    if not FRAME_ON: fo = None
    # bezel groove: one 0.8 x 0.4 rounded-rectangle line framing dots, keys and window (fills orange with the layer-3 colour change)
    if FRAME_ON: fo = fs.box(FRAME["x0"], FRAME["y0"], Z_ROOF_TOP - 0.4, FRAME["x1"], FRAME["y1"], Z_ROOF_TOP + 1, "frameo"); fs.filletz(fo, FRAME["r"])
    if FRAME_ON:
        fi = fs.box(FRAME["x0"] + FRAME["w"], FRAME["y0"] + FRAME["w"], Z_ROOF_TOP - 1, FRAME["x1"] - FRAME["w"], FRAME["y1"] - FRAME["w"], Z_ROOF_TOP + 2, "framei"); fs.filletz(fi, FRAME["r"] - FRAME["w"])
        tools.append(fs.cut(fo, [fi], "framek"))
    # GPS mark: 0.4 deep square groove, right edge on the window's left edge
    gx, gy = (GPS_MARK_CX if GPS_MARK >= 20 else GPS_PATCH[0]), GPS_PATCH[1]
    h = GPS_MARK / 2
    ring = fs.box(gx - h, gy - h, Z_ROOF_TOP - 0.4, gx + h, gy + h, Z_ROOF_TOP + 1, "gring"); gin = fs.box(gx - h + 0.8, gy - h + 0.8, Z_ROOF_TOP - 1, gx + h - 0.8, gy + h - 0.8, Z_ROOF_TOP + 2, "gin")
    tools.append(fs.cut(ring, [gin], "gk"))
    # forward chevron on the roof, apex toward -Y (car forward), 11 mm span = half the GPS square
    for sgn in (-1, 1):
        b = fs.box(W/2 + sgn*2.75 - 3.6, 7.0 - 0.6, Z_ROOF_TOP - 0.4, W/2 + sgn*2.75 + 3.6, 7.0 + 0.6, Z_ROOF_TOP + 1, "chev"); fs.rotz(b, W/2 + sgn*2.75, 7.0, sgn*40); tools.append(b)
    # louvers: front and right walls share the SD slot's top datum; back wall chimney over the ESP32 module
    for lx in LOUV_F_X: tools.append(fs.box(lx - LOUV_W/2, -WALL - 1, LOUV_Z[0], lx + LOUV_W/2, 1.0, LOUV_Z[1], "louv"))
    for ly in LOUV_R_Y: tools.append(fs.box(W - 1.0, ly - LOUV_W/2, LOUV_Z[0], W + WALL + 1, ly + LOUV_W/2, LOUV_Z[1], "louv"))
    for lx in LOUV_B_X: tools.append(fs.box(lx - LOUV_W/2, D - 1.0, LOUV_Z_BACK[0], lx + LOUV_W/2, D + WALL + 1, LOUV_Z_BACK[1], "louvb"))
    # USB chute opening (1.5 mm corners) with a 2 mm thumb-pocket lead-in
    usb = fs.box(-WALL - 1, USB_Y - CH_IN_W/2, CH_IN_Z0, 1.0, USB_Y + CH_IN_W/2, CH_IN_Z1, "usb"); fs.filletx(usb, R_WIN); tools.append(usb)
    lead = fs.box(-WALL - 1, USB_Y - CH_IN_W/2 - 2, CH_IN_Z0 - 1.5, -WALL + 1.2, USB_Y + CH_IN_W/2 + 2, CH_IN_Z1 + 1.5, "usblead"); fs.filletx(lead, R_WIN); tools.append(lead)
    sd = fs.box(W - 1.0, SD["y"] - SD["half"], SD["z0"], W + WALL + 1, SD["y"] + SD["half"], SD["z1"], "sd"); fs.filletx(sd, R_WIN); tools.append(sd)
    sh = fs.cut(sh, tools)
    nubs = [fs.cylz(BTN_X, by, Z_BTN_TOP + NUB_GAP, H_INT + (ROOF - FLAP_T) + 0.05, 2.2, "nub") for by in BTN_Y]
    nubs.append(fs.cylz(RESET_KEY["cx"], RESET_KEY["cy"], Z_BTN_TOP + NUB_GAP, H_INT + (ROOF - FLAP_T) + 0.05, RESET_KEY["nub_d"], "rnub"))
    sh = fs.unite([sh] + nubs)
    fs.name(sh, "Shell", (0.17, 0.18, 0.20))
    fs.w("}")
    # ---------------- SLED
    fs.w("if (definition.buildSled) {")
    plate = fs.box(-WALL, -WALL, Z_PLATE_BOT, W + WALL, D + WALL, Z_PLATE_TOP, "plate"); fs.filletz(plate, R_VERT); fs.chamfer_bottom(plate, 0.5)
    plat = fs.box(0.3, 0.3, Z_PLATE_TOP - 0.01, W - 0.3, D - 0.3, 0.0, "plateau"); fs.filletz(plat, R_VERT - WALL + 0.3)
    adds = [plate, plat]
    for t in STANDOFFS:
        x, y, hd, lab = t[:4]; h, d = so_geom(t); adds.append(fs.cylz(x, y, -0.01, h, d, "so"))
    for x, y in PADS: adds.append(fs.cylz(x, y, -0.01, STANDOFF, 5.0, "pad"))
    adds.append(fs.box(IMU_LEDGE["x0"], IMU_LEDGE["y0"], -0.01, IMU_LEDGE["x1"], IMU_LEDGE["y1"], STANDOFF, "ledge"))
    for hx, hy in HOOKS:   # post beside the board edge + lip over it
        adds.append(fs.box(hx, hy - 1.25, -0.01, hx + 1.6, hy + 1.25, ZF + 1.5, "hook"))
        lip = fs.box(hx - 1.2, hy - 1.25, ZF + 0.35, hx + 1.6, hy + 1.25, ZF + 1.5, "hooklip")   # 1.2 mm overlap, 0.35 gap (v1 printed flush at 0.05)
        fs.w(f'opChamfer(context, {fs.uid("lipch")}, {{ "entities" : qFarthestAlong(qParallelEdges(qOwnedByBody({lip}, EntityType.EDGE), vector(0, 1, 0)), vector(-1, 0, -1)), "chamferType" : ChamferType.EQUAL_OFFSETS, "width" : 0.7 * millimeter }});')
        adds.append(lip)
    # USB chute: U channel, open top
    ch = fs.box(CH_X0, CH_Y0, -0.01, CH_X1, CH_Y1, CH_IN_Z1 + 0.6, "chute")
    chin = fs.box(-1.0, CH_Y0 + CH_WALL, CH_IN_Z0, CH_X1 + 1, CH_Y1 - CH_WALL, CH_IN_Z1 + 2, "chutein")
    adds.append(fs.cut(ch, [chin], "chk"))
    # cable guide ribs
    for (x0, y0, x1, y1) in RIBS: adds.append(fs.box(x0, y0, -0.01, x1, y1, RIB_H, "rib"))   # channel walls; the wall / PCB edge is the other side
    sled = fs.unite(adds)
    tools = []
    for t in STANDOFFS:
        x, y, hd, lab = t[:4]; h, d = so_geom(t); tools.append(fs.cylz(x, y, h - 5.5 if h > STANDOFF else -1.5, h + 0.5, hd, "soh"))
    for k, (px, py, kind) in POSTS.items():
        tools.append(fs.cylz(px, py, Z_PLATE_BOT - 1, 0.5, CLR_M25, "thru")); tools.append(fs.cylz(px, py, Z_PLATE_BOT - 1, Z_PLATE_BOT + CBORE_H, CBORE_D, "cb"))
    for k, (sx, sy) in SADDLE_SCREWS.items(): tools.append(fs.cylz(sx, sy, Z_PLATE_BOT - 1, 0.5, CLR_M25, "sthru"))
    tools.append(fs.box(VENT["x"] - VENT["w"]/2, VENT["y"] - VENT["d"]/2, Z_PLATE_BOT - 1, VENT["x"] + VENT["w"]/2, VENT["y"] + VENT["d"]/2, 0.5, "vent"))
    tools.append(fs.box(DROP["x"] - DROP["w"]/2, DROP["y"] - DROP["d"]/2, Z_PLATE_BOT - 1, DROP["x"] + DROP["w"]/2, DROP["y"] + DROP["d"]/2, 0.5, "drop"))
    for fx, fy in FEET: tools.append(fs.cylz(fx, fy, Z_PLATE_BOT - 1, Z_PLATE_BOT + 0.6, 8.0, "foot"))
    for sgn in (-1, 1):   # forward chevron engraved in the plateau
        b = fs.box(W/2 + sgn*2.75 - 3.6, 15.0 - 0.6, -0.4, W/2 + sgn*2.75 + 3.6, 15.0 + 0.6, 1.0, "schev"); fs.rotz(b, W/2 + sgn*2.75, 15.0, sgn*40); tools.append(b)
    sled = fs.cut(sled, tools)
    fs.name(sled, "Sled", (1.0, 0.42, 0.08))
    fs.w("}")
    # ---------------- SADDLE (plate + cradle, tube diameter parametric)
    fs.w("const RL = definition.tubeDia / millimeter / 2 + %.2f - %.2f;   // liner radius minus preload" % (LINER, CLAMP_PRELOAD))
    fs.w(f"const ZC = {Z_SAD_BOT:.3f} - 1.5 - RL;   // tube centre height")
    fs.w("if (definition.buildSaddle) {")
    # plate inset to the shell's inner footprint so the orange sled band is the outermost lower edge
    sp = fs.box(0.0, 0.0, Z_SAD_BOT, W, D, Z_SAD_TOP, "splate"); fs.filletz(sp, R_VERT); fs.chamfer_bottom(sp, 0.5)
    adds = [sp]
    for k, (sx, sy) in SADDLE_SCREWS.items(): adds.append(fs.cylz(sx, sy, Z_SAD_BOT - 3.0, Z_SAD_BOT + 1.0, 8.0, "sboss"))
    fs.w(f'var cradle = mkBox(context, id + "cradle", {CR_X0:.3f}, {CR_Y0:.3f}, ZC, {CR_X1:.3f}, {CR_Y1:.3f}, {Z_SAD_BOT + 1.0:.3f});')
    fs.w(f'filletZ(context, id + "cradlef", cradle, {R_VERT});')
    fs.w(f'var tubeA = cylX(context, id + "tubeA", {TUBE_CY:.3f}, ZC, {CR_X0 - 2:.3f}, {CR_X1 + 2:.3f}, RL);')
    fs.w('cradle = mkCut(context, id + "cradlek", cradle, [tubeA]);')
    adds.append("cradle")
    sad = fs.unite(adds)
    tools = []
    for k, (px, py, kind) in POSTS.items(): tools.append(fs.cylz(px, py, Z_SAD_BOT - 1, Z_SAD_TOP + 1, 6.0, "acc"))
    for k, (sx, sy) in SADDLE_SCREWS.items():
        tools.append(fs.cylz(sx, sy, Z_SAD_TOP - INSERT_DEPTH, Z_SAD_TOP + 1, INSERT_D, "sbore")); tools.append(fs.cylz(sx, sy, Z_SAD_TOP - INSERT_SEAT_H, Z_SAD_TOP + 1, INSERT_SEAT_D, "sseat"))   # insert pressed from the plate top
    tools.append(fs.box(VENT["x"] - VENT["w"]/2 - 1, VENT["y"] - VENT["d"]/2 - 1, Z_SAD_BOT - 1, VENT["x"] + VENT["w"]/2 + 1, VENT["y"] + VENT["d"]/2 + 1, Z_SAD_TOP + 1, "svent"))
    for ex, ey in EAR_PTS:
        fs.w(f'var eb{int(ex)}_{int(ey)} = cylZ(context, id + "ear{int(ex)}_{int(ey)}", {ex:.3f}, {ey:.3f}, ZC - 0.5, ZC + {BORE_EAR}, {INSERT_D});'); tools.append(f"eb{int(ex)}_{int(ey)}")
        fs.w(f'var es{int(ex)}_{int(ey)} = cylZ(context, id + "eseat{int(ex)}_{int(ey)}", {ex:.3f}, {ey:.3f}, ZC - 0.5, ZC + {INSERT_SEAT_H}, {INSERT_SEAT_D});'); tools.append(f"es{int(ex)}_{int(ey)}")
    sad = fs.cut(sad, tools)
    fs.name(sad, "Saddle", (0.17, 0.18, 0.20))
    fs.w("}")
    # ---------------- CAP (lower clamp half): flanges sit 1 mm below the cradle ears until the screws compress the liner
    fs.w("if (definition.buildCap) {")
    fs.w(f'var capCyl = cylX(context, id + "capcyl", {TUBE_CY:.3f}, ZC, {CR_X0:.3f}, {CR_X1:.3f}, RL + 4.0);')
    fs.w(f'var capUpper = mkBox(context, id + "capupper", {CR_X0 - 2:.3f}, {CR_Y0 - 40:.3f}, ZC - 1.0, {CR_X1 + 2:.3f}, {CR_Y1 + 40:.3f}, ZC + RL + 10.0);')
    fs.w('capCyl = mkCut(context, id + "capcylk", capCyl, [capUpper]);')
    fs.w(f'var capSlab = mkBox(context, id + "capslab", {CR_X0:.3f}, {CR_Y0:.3f}, ZC - 7.0, {CR_X1:.3f}, {CR_Y1:.3f}, ZC - 1.0);')
    fs.w(f'filletZ(context, id + "capslabf", capSlab, {R_VERT});')
    fs.w('var cap = mkUnite(context, id + "capu", [capCyl, capSlab]);')
    fs.w(f'var tubeB = cylX(context, id + "tubeB", {TUBE_CY:.3f}, ZC, {CR_X0 - 2:.3f}, {CR_X1 + 2:.3f}, RL);')
    tools = ["tubeB"]
    for ex, ey in EAR_PTS:
        fs.w(f'var ct{int(ex)}_{int(ey)} = cylZ(context, id + "ct{int(ex)}_{int(ey)}", {ex:.3f}, {ey:.3f}, ZC - 8.0, ZC + 0.5, {CLR_M25});'); tools.append(f"ct{int(ex)}_{int(ey)}")
        fs.w(f'var cc{int(ex)}_{int(ey)} = cylZ(context, id + "cc{int(ex)}_{int(ey)}", {ex:.3f}, {ey:.3f}, ZC - 8.0, ZC - 7.0 + {CBORE_H}, {CBORE_D});'); tools.append(f"cc{int(ex)}_{int(ey)}")
    fs.w(f'cap = mkCut(context, id + "capk", cap, [{", ".join(tools)}]);')
    fs.w('nameBody(context, cap, "Clamp cap", color(0.17, 0.18, 0.20));')
    fs.w("}")
    # ---------------- UNIVERSAL BASE (alternative to the saddle): same plate, GoPro 3-finger mount underneath, strap slots
    fs.w("if (definition.buildBase) {")
    bp = fs.box(0.0, 0.0, Z_SAD_BOT, W, D, Z_SAD_TOP, "bplate"); fs.filletz(bp, R_VERT); fs.chamfer_bottom(bp, 0.5)
    badds = [bp]
    for k, (sx, sy) in SADDLE_SCREWS.items(): badds.append(fs.cylz(sx, sy, Z_SAD_BOT - 3.0, Z_SAD_BOT + 1.0, 8.0, "bboss"))
    FINGER_T, FINGER_GAP, FINGER_L, FINGER_H = 3.0, 3.4, 15.0, 14.0
    fx0 = W/2 - (3 * FINGER_T + 2 * FINGER_GAP) / 2
    for i in range(3):
        x0 = fx0 + i * (FINGER_T + FINGER_GAP)
        f = fs.box(x0, D/2 - FINGER_L/2, Z_SAD_BOT - FINGER_H, x0 + FINGER_T, D/2 + FINGER_L/2, Z_SAD_BOT + 1.0, "finger")
        fs.w(f"opFillet(context, {fs.uid('ff')}, {{ \"entities\" : qParallelEdges(qAdjacent(qFarthestAlong(qOwnedByBody({f}, EntityType.FACE), vector(0, 0, -1)), AdjacencyType.EDGE, EntityType.EDGE), vector(1, 0, 0)), \"radius\" : {FINGER_L/2 - 0.1} * millimeter }});")
        badds.append(f)
    bb = fs.unite(badds)
    btools = []
    for k, (px, py, kind) in POSTS.items(): btools.append(fs.cylz(px, py, Z_SAD_BOT - 1, Z_SAD_TOP + 1, 6.0, "bacc"))
    for k, (sx, sy) in SADDLE_SCREWS.items():
        btools.append(fs.cylz(sx, sy, Z_SAD_TOP - INSERT_DEPTH, Z_SAD_TOP + 1, INSERT_D, "bbore")); btools.append(fs.cylz(sx, sy, Z_SAD_TOP - INSERT_SEAT_H, Z_SAD_TOP + 1, INSERT_SEAT_D, "bseat"))
    btools.append(fs.box(VENT["x"] - VENT["w"]/2 - 1, VENT["y"] - VENT["d"]/2 - 1, Z_SAD_BOT - 1, VENT["x"] + VENT["w"]/2 + 1, VENT["y"] + VENT["d"]/2 + 1, Z_SAD_TOP + 1, "bvent"))
    for (sx, sy) in ((12.0, 12.0), (60.0, 12.0), (12.0, D - 12.0), (60.0, D - 12.0)):   # 20 x 4 strap slots for 25 mm Velcro or zip ties
        btools.append(fs.box(sx - 10, sy - 2, Z_SAD_BOT - 1, sx + 10, sy + 2, Z_SAD_TOP + 1, "strap"))
    btools.append(fs.cylx(D/2, Z_SAD_BOT - FINGER_H + FINGER_L/2, fx0 - 2, fx0 + 3 * FINGER_T + 2 * FINGER_GAP + 2, 2.6, "bolt"))   # M5 thumbscrew
    bb = fs.cut(bb, btools)
    fs.name(bb, "Universal base (GoPro)", (0.17, 0.18, 0.20))
    fs.w("}")
    # ---------------- ANALOG TRAY (v2) + connector cards + ADS riser frame. Tray-local coords -> Part Studio at x + TRAY_DX, case z = Z_TRAY_BOT + z
    fs.w("if (definition.buildTray) {")
    fs.local = local   # mirror the tray parts with CadQuery for local export
    DX, DZ = TRAY_DX, Z_TRAY_BOT
    def tb(x0, y0, z0, x1, y1, z1, tag="tb"): return fs.box(x0 + DX, y0, z0 + DZ, x1 + DX, y1, z1 + DZ, tag)
    def tc(cx, cy, z0, z1, d, tag="tc"): return fs.cylz(cx + DX, cy, z0 + DZ, z1 + DZ, d, tag)
    def ty(cx, cz, y0, y1, r, tag="ty"): return fs.cyly(cx + DX, cz + DZ, y0, y1, r, tag)
    outer = tb(-WALL, CARD_Y0, 0, W + WALL, D + WALL, TRAY_H, "touter"); fs.filletz(outer, R_VERT); fs.chamfer_bottom(outer, 0.5)
    cav = tb(0, CARD_Y1, TRAY_FLOOR, W, D, TRAY_H + 1, "tcav")
    cardslice = tb(-WALL - 1, CARD_Y0 - 1, TRAY_FLOOR, W + WALL + 1, CARD_Y1, TRAY_H + 1, "tslice")   # the card is a separate body
    body = fs.cut(outer, [cav, cardslice], "tk0")
    adds = [body]
    zf = TRAY_FLOOR - 1.0   # everything grows out of the floor with 1 mm of overlap
    for k, (cx, cy) in TRAY_COLS.items(): adds.append(tc(cx, cy, zf, TRAY_H, COL_D, "tcol"))
    adds.append(tb(S2_BRIDGE[0], S2_BRIDGE[1], zf, S2_BRIDGE[2] + 1, S2_BRIDGE[3], TRAY_H, "ts2b"))
    adds.append(tb(-1.0, P4_LOW[1], zf, P4_LOW[2], D + 1, P4_LOW[4], "tp4l")); adds.append(tb(-1.0, P4_UP[1], zf, P4_UP[2], D + 1, TRAY_H, "tp4u"))
    adds.append(tb(-1.0, BLOCK_L[1], zf, BLOCK_L[2], BLOCK_L[3], TRAY_H, "tbl")); adds.append(tb(BLOCK_R[0], BLOCK_R[1], zf, W + 1, BLOCK_R[3], TRAY_H, "tbr"))
    for x, y in ADS_HOLES:   # 6 mm tall: the 7.5 mm pilot takes the 6.9 mm of M2.5 x 16 below the stack
        so = tc(x, y, zf, Z_ADS1, ADS_SO_D, "tads")
        if x < ADS_CONN_X: so = fs.cut(so, [tb(ADS_SO_FLAT_X - 10, y - 5, zf - 1, ADS_SO_FLAT_X, y + 5, Z_ADS1 + 1, "tadsflat")], "tadsk")   # D: flat toward the proto
        else: adds.append(tb(x, y - 2.0, zf, W + 1, y + 2.0, Z_ADS1, "tadsbr"))                                                          # bridge into the right wall
        adds.append(so)
    for x, y in PROTO_SCREWS: adds.append(tc(x, y, zf, Z_BRD, 6.0, "tps"))
    for x, y in PROTO_PADS: adds.append(tc(x, y, zf, Z_BRD, 5.0, "tpp"))
    ztop, zlip = Z_PROTO_TOP + 1.5, Z_PROTO_TOP + 0.35
    for edge, c, a in PROTO_HOOKS:   # 1.6 mm post 0.2 off the board edge, lip 1.0 over the board, 0.35 above it, chamfered lead-in
        if edge == "left":
            adds.append(tb(c - 1.8, a - 1.25, zf, c - 0.2, a + 1.25, ztop, "thook")); lip = tb(c - 1.8, a - 1.25, zlip, c + 1.0, a + 1.25, ztop, "thlip"); fs.lip_chamfer(lip, (0, 1, 0), (1, 0, -1))
        else:
            adds.append(tb(a - 1.25, c - 1.8, zf, a + 1.25, c - 0.2, ztop, "thook")); lip = tb(a - 1.25, c - 1.8, zlip, a + 1.25, c + 1.0, ztop, "thlip"); fs.lip_chamfer(lip, (1, 0, 0), (0, 1, -1))
        adds.append(lip)
    yb = PROTO["y"] + PROTO["d"]   # back edge: rigid hook off the back wall (slide the board under it first)
    adds.append(tb(PROTO_BACK_LIP_X[0], yb + 0.2, zf, PROTO_BACK_LIP_X[1], D + 1, ztop, "tbhook"))
    blip = tb(PROTO_BACK_LIP_X[0], yb - 1.0, zlip, PROTO_BACK_LIP_X[1], D + 1, ztop, "tblip"); fs.lip_chamfer(blip, (1, 0, 0), (0, -1, -1)); adds.append(blip)
    tray = fs.unite(adds)
    tools = []
    for k, (cx, cy) in list(TRAY_COLS.items()) + [("P4", P4)]:
        if k.startswith("P"):   # shell screws: 2.7 through the upper column, head seated at P_SEAT, driver channel to the bottom (reached through the base's access holes)
            tools.append(tc(cx, cy, P_SEAT - 1, TRAY_H + 1, CLR_M25, "tthru")); tools.append(tc(cx, cy, -1, P_SEAT, P_CHAN_D, "tchan"))
        else:                   # S columns: insert bore + lead-in at the top for the sled screw, self-tap pilot at the bottom for the base screw from below
            tools.append(tc(cx, cy, TRAY_H - INSERT_DEPTH, TRAY_H + 1, INSERT_D, "tsins")); tools.append(tc(cx, cy, TRAY_H - INSERT_SEAT_H, TRAY_H + 1, INSERT_SEAT_D, "tsseat"))
            tools.append(tc(cx, cy, -1, 5.5, HOLE_M25, "tspil"))
    for x, y in ADS_HOLES: tools.append(tc(x, y, 0.5, Z_ADS1 + 0.5, HOLE_M25, "tadsh"))   # 7.5 deep, 0.5 mm of floor left
    for x, y in PROTO_SCREWS: tools.append(tc(x, y, Z_BRD - 5.5, Z_BRD + 0.5, HOLE_M25, "tpsh"))
    for x, z in CARD_SCREWS: tools.append(ty(x, z, CARD_Y1 - 1.0, CARD_Y1 + 6.0, HOLE_M25 / 2, "tcs"))
    tools.append(tb(-WALL - 1, CARD_Y0 - 1, TRAY_H - FLANGE_T, W + WALL + 1, -WALL, TRAY_H + 1, "tflp"))   # pocket for the card's roof over the step
    tools.append(tb(WALL_RELIEF[0], WALL_RELIEF[1], TRAY_FLOOR, W + 0.5, WALL_RELIEF[2], TRAY_H + 1, "twrel"))   # 0.5 mm relief in the right wall beside the ADS stack
    tray = fs.cut(tray, tools)
    fs.name(tray, "Analog tray", (0.17, 0.18, 0.20))
    # connector cards: the step's front face + a roof over the step, cut from the same filleted footprint so the ends follow the R5 corners
    for variant, conns, dx in (("2x M12", CONNECTORS, 0.0), ("blank", [], CARD2_DX)):
        slab = tb(-WALL + dx, CARD_Y0, TRAY_FLOOR + 0.1, W + WALL + dx, D + WALL, TRAY_H, "cslab"); fs.filletz(slab, R_VERT)
        card = fs.cut(slab, [tb(-WALL - 1 + dx, CARD_Y1, TRAY_FLOOR - 1, W + WALL + 1 + dx, D + WALL + 1, TRAY_H + 1, "ccut")], "ck")
        roof = tb(-WALL + dx, CARD_Y0, TRAY_H - FLANGE_T, W + WALL + dx, D + WALL, TRAY_H, "croof"); fs.filletz(roof, R_VERT)
        roof = fs.cut(roof, [tb(-WALL - 1 + dx, -WALL, TRAY_H - FLANGE_T - 1, W + WALL + 1 + dx, D + WALL + 1, TRAY_H + 1, "crk")], "crk2")
        card = fs.unite([card, roof])
        ctools = [ty(x + dx, z, CARD_Y0 - 1, CARD_Y1 + 1, CLR_M25 / 2, "ccs") for x, z in CARD_SCREWS]
        ctools += [ty(x + dx, CONN_Z, CARD_Y0 - 1, CARD_Y1 + 1, d / 2, "cconn") for x, d, lab in conns]
        card = fs.cut(card, ctools)
        fs.name(card, f"Connector card ({variant})", (0.17, 0.18, 0.20))
    # ADS riser frame: four 5 mm sleeves (6 tall) joined at their TOPS by two bars along the board's long edges and one cross bar at mid-board
    # (4 mm above the lower board, clear of its 1.3 mm parts and its end connectors); the level-2 board rests on sleeves and bars, the M2.5 x 16 pass through
    radds = []
    for x, y in ADS_HOLES: radds.append(tc(x + CARD2_DX, y, 0, RISER_H, 5.0, "rsl"))
    y0, y1 = ADS["y"] + 2.54, ADS["y"] + ADS["d"] - 2.54
    for bx in (ADS["x"] + 0.2, ADS["x"] + ADS["w"] - 0.2 - RISER_BAR): radds.append(tb(bx + CARD2_DX, y0, RISER_H - 2.0, bx + RISER_BAR + CARD2_DX, y1, RISER_H, "rbar"))
    ym = ADS["y"] + ADS["d"] / 2
    radds.append(tb(ADS["x"] + 0.2 + CARD2_DX, ym - 1.0, RISER_H - 2.0, ADS["x"] + ADS["w"] - 0.2 + CARD2_DX, ym + 1.0, RISER_H, "rxbar"))
    riser = fs.unite(radds)
    rtools = [tc(x + CARD2_DX, y, -1, RISER_H + 1, CLR_M25, "rth") for x, y in ADS_HOLES]
    led = (ADS["x"] + 12.573, ADS["y"] + 3.556)   # level-1 LED D1 sits 2.9 mm from the (73.7, 20.5) hole: notch that sleeve's foot
    rtools.append(tb(led[0] - 1.4 + CARD2_DX, led[1] - 1.2, -1, led[0] + 1.4 + CARD2_DX, led[1] + 1.2, 1.0, "rnotch"))
    riser = fs.cut(riser, rtools)
    fs.name(riser, "ADS riser frame", (0.17, 0.18, 0.20))
    fs.local = False
    fs.w("}")
    # ---------------- COUPON (print first, roof-down): 3 flexure keys + nubs, insert bores 3.4/3.6/3.8, pilot holes 1.6/1.75/2.0/2.2/2.4
    fs.w("if (definition.buildCoupon) {")
    cx0, cy0 = -70.0, 0.0
    slab = fs.box(cx0, cy0, Z_ROOF_TOP - ROOF, cx0 + 44, cy0 + 30, Z_ROOF_TOP, "cslab"); fs.filletz(slab, 3.0)
    blk = fs.box(cx0, cy0 + 30, Z_ROOF_TOP - 9.0, cx0 + 44, cy0 + 42, Z_ROOF_TOP, "cblk")
    cadds = [slab, blk]
    for i, hd in enumerate((1.6, 1.75, 2.0, 2.2, 2.4)): cadds.append(fs.cylz(cx0 + 5 + i * 8.5, cy0 + 6, Z_ROOF_TOP - ROOF - 4.0, Z_ROOF_TOP - ROOF + 0.01, 6.0, "cso"))
    cp = fs.unite(cadds)
    ctools = []
    for i, hd in enumerate((1.6, 1.75, 2.0, 2.2, 2.4)): ctools.append(fs.cylz(cx0 + 5 + i * 8.5, cy0 + 6, Z_ROOF_TOP - ROOF - 4.5, Z_ROOF_TOP + 1, hd, "csoh"))
    for i, bd in enumerate((3.4, 3.6, 3.8)): ctools.append(fs.cylz(cx0 + 10 + i * 12, cy0 + 36, Z_ROOF_TOP - 9.5, Z_ROOF_TOP - 9.0 + BORE_POST, bd, "cbore"))
    hinge = cx0 + 12; tip = hinge + FLAP_L; ys = [cy0 + 14 + k * 4.45 for k in range(3)]
    comb = fs.box(hinge, ys[0] - FLAP_W/2 - SLOT_W, Z_ROOF_TOP - ROOF - 1, tip + SLOT_W, ys[-1] + FLAP_W/2 + SLOT_W, Z_ROOF_TOP + 1, "ccomb")
    flaps = [fs.box(hinge - 1, y - FLAP_W/2, Z_ROOF_TOP - ROOF - 2, tip, y + FLAP_W/2, Z_ROOF_TOP + 2, "cflap") for y in ys]
    ctools.append(fs.cut(comb, flaps, "ccombk"))
    ctools.append(fs.box(hinge - 0.01, ys[0] - FLAP_W/2 - SLOT_W - 0.6, Z_ROOF_TOP - ROOF - 1, tip + SLOT_W + 0.6, ys[-1] + FLAP_W/2 + SLOT_W + 0.6, Z_ROOF_TOP - FLAP_T, "ckb"))
    cp = fs.cut(cp, ctools)
    nubs = [fs.cylz(hinge + 6.5, y, Z_ROOF_TOP - FLAP_T - 3.0, Z_ROOF_TOP - FLAP_T + 0.05, 2.2, "cnub") for y in ys]
    cp = fs.unite([cp] + nubs)
    fs.name(cp, "Test coupon", (0.6, 0.6, 0.62))
    fs.w("}")
    # ---------------- BOARD BLOCKS (visual)
    fs.w("if (definition.showBoards) {")
    # Only the boards without STEP models (IMU, SHT41); the Feather stack and GPS are real models in Assembly 1.
    blocks = []
    def blk(x0, y0, z0, x1, y1, z1, tag="bd"): blocks.append(fs.box(x0, y0, z0, x1, y1, z1, tag))
    for b in (IMU, SHT): blk(b["x"], b["y"], STANDOFF, b["x"] + b["w"], b["y"] + b["d"], ZF)
    for cx, cy in ((IMU_CONN_X, IMU["y"] + 2.54), (IMU_CONN_X, IMU["y"] + 22.86), (SHT_CONN_X, SHT["y"] + 3.175), (SHT_CONN_X, SHT["y"] + 22.225)):
        blk(cx - 3.05, cy - 2.3, ZF, cx + 3.05, cy + 2.3, ZF + 4.3)
    for i, b in enumerate(blocks): fs.name(b, f"Board envelope {i+1}", (0.2, 0.7, 0.3))
    fs.w("}")

    code = '''FeatureScript 3070;
import(path : "onshape/std/common.fs", version : "3070.0");

// GENERATED by mechanical/generate_onshape.py. Edit the Python constants, not this file.
// ESP32 race logger enclosure, concept B: shell (printed upside down) + sled + saddle + clamp cap.

function mkBox(context is Context, id is Id, x0 is number, y0 is number, z0 is number, x1 is number, y1 is number, z1 is number) returns Query
{
    fCuboid(context, id, { "corner1" : vector(x0, y0, z0) * millimeter, "corner2" : vector(x1, y1, z1) * millimeter });
    return qCreatedBy(id, EntityType.BODY);
}
function cylZ(context is Context, id is Id, cx is number, cy is number, z0 is number, z1 is number, d is number) returns Query
{
    fCylinder(context, id, { "topCenter" : vector(cx, cy, z1) * millimeter, "bottomCenter" : vector(cx, cy, z0) * millimeter, "radius" : d / 2 * millimeter });
    return qCreatedBy(id, EntityType.BODY);
}
function cylX(context is Context, id is Id, cy is number, cz is number, x0 is number, x1 is number, r is number) returns Query
{
    fCylinder(context, id, { "topCenter" : vector(x1, cy, cz) * millimeter, "bottomCenter" : vector(x0, cy, cz) * millimeter, "radius" : r * millimeter });
    return qCreatedBy(id, EntityType.BODY);
}
function cylY(context is Context, id is Id, cx is number, cz is number, y0 is number, y1 is number, r is number) returns Query
{
    fCylinder(context, id, { "topCenter" : vector(cx, y1, cz) * millimeter, "bottomCenter" : vector(cx, y0, cz) * millimeter, "radius" : r * millimeter });
    return qCreatedBy(id, EntityType.BODY);
}
function mkUnite(context is Context, id is Id, bodies is array) returns Query
{
    if (size(bodies) > 1)
        opBoolean(context, id, { "tools" : qUnion(bodies), "operationType" : BooleanOperationType.UNION });
    return qUnion(bodies);
}
function mkCut(context is Context, id is Id, target is Query, tools is array) returns Query
{
    opBoolean(context, id, { "targets" : target, "tools" : qUnion(tools), "operationType" : BooleanOperationType.SUBTRACTION });
    return target;
}
function mkIntersect(context is Context, id is Id, target is Query, tools is array) returns Query
{
    opBoolean(context, id, { "targets" : target, "tools" : qUnion(tools), "operationType" : BooleanOperationType.INTERSECTION });
    return target;
}
function filletZ(context is Context, id is Id, body is Query, r is number)
{
    opFillet(context, id, { "entities" : qParallelEdges(qOwnedByBody(body, EntityType.EDGE), vector(0, 0, 1)), "radius" : r * millimeter });
}
function filletX(context is Context, id is Id, body is Query, r is number)
{
    opFillet(context, id, { "entities" : qParallelEdges(qOwnedByBody(body, EntityType.EDGE), vector(1, 0, 0)), "radius" : r * millimeter });
}
function chamferBottom(context is Context, id is Id, body is Query, w is number)
{
    const bot = qFarthestAlong(qOwnedByBody(body, EntityType.FACE), vector(0, 0, -1));
    opChamfer(context, id, { "entities" : qAdjacent(bot, AdjacencyType.EDGE, EntityType.EDGE), "chamferType" : ChamferType.EQUAL_OFFSETS, "width" : w * millimeter });
}
function chamferTop(context is Context, id is Id, body is Query, w is number)
{
    const top = qFarthestAlong(qOwnedByBody(body, EntityType.FACE), vector(0, 0, 1));
    opChamfer(context, id, { "entities" : qAdjacent(top, AdjacencyType.EDGE, EntityType.EDGE), "chamferType" : ChamferType.EQUAL_OFFSETS, "width" : w * millimeter });
}
function rotZ(context is Context, id is Id, body is Query, cx is number, cy is number, deg is number)
{
    opTransform(context, id, { "bodies" : body, "transform" : rotationAround(line(vector(cx, cy, 0) * millimeter, vector(0, 0, 1)), deg * degree) });
}
function nameBody(context is Context, body is Query, name is string, c is Color)
{
    setProperty(context, { "entities" : body, "propertyType" : PropertyType.NAME, "value" : name });
    setProperty(context, { "entities" : body, "propertyType" : PropertyType.APPEARANCE, "value" : c });
}

annotation { "Feature Type Name" : "Race logger enclosure" }
export const raceLoggerEnclosure = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Roll bar tube diameter" }
        isLength(definition.tubeDia, { (millimeter) : [20, %(tube)s, 80] } as LengthBoundSpec);
        annotation { "Name" : "Build shell", "Default" : true } definition.buildShell is boolean;
        annotation { "Name" : "Build sled", "Default" : true } definition.buildSled is boolean;
        annotation { "Name" : "Build saddle", "Default" : true } definition.buildSaddle is boolean;
        annotation { "Name" : "Build clamp cap", "Default" : true } definition.buildCap is boolean;
        annotation { "Name" : "Show IMU / SHT41 envelopes (no STEP models)", "Default" : true } definition.showBoards is boolean;
        annotation { "Name" : "Build test coupon", "Default" : true } definition.buildCoupon is boolean;
        annotation { "Name" : "Build universal base (GoPro fingers)", "Default" : true } definition.buildBase is boolean;
        annotation { "Name" : "Build analog tray (v2: tray, connector cards, ADS riser)", "Default" : true } definition.buildTray is boolean;
    }
    {
%(body)s
    });
''' % dict(tube=TUBE_D_DEFAULT, body="\n".join(fs.lines))
    emit_fs.last = fs
    return code

# ------------------------------------------------------------------ layout drawing
def layout_png(E, table):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    fig, ax = plt.subplots(figsize=(9.5, 11)); ax.set_aspect("equal")
    ax.add_patch(Rectangle((-WALL, -WALL), W + 2*WALL, D + 2*WALL, fc="#e6e6e6", ec="#333", lw=2))
    ax.add_patch(Rectangle((0, 0), W, D, fc="white", ec="#aaa"))
    for (a, b), n in (((0, LANE_F), f"front lane {LANE_F}"), ((Y_ROW1, Y_STK0), f"middle lane {LANE_M}")):
        ax.add_patch(Rectangle((0, a), W, b - a, fc="#fff3e0", ec="none")); ax.text(W - 2, (a + b)/2, n, ha="right", va="center", fontsize=8, color="#b26a00")
    colors = {"pcb": "#cfe3ff", "conn": "#ffd54f", "plug": "#ff8a80", "boss": "#bdbdbd", "tower": "#616161", "part": "#d7ccc8", "cable": None, "wall": None}
    for e in E:
        if e.kind in ("wall",) or e.name == "roof": continue
        if e.kind == "cable": continue
        c = colors.get(e.kind, "#eee")
        alpha = 0.5 if e.kind in ("plug",) else 0.9
        ax.add_patch(Rectangle((e.lo[0], e.lo[1]), e.hi[0]-e.lo[0], e.hi[1]-e.lo[1], fc=c, ec="#333", lw=0.6, alpha=alpha))
        if e.kind in ("pcb", "tower") or e.name.startswith(("usb chute", "gps patch", "esp32")):
            ax.text((e.lo[0]+e.hi[0])/2, (e.lo[1]+e.hi[1])/2, e.name.replace("pcb ", ""), ha="center", va="center", fontsize=6.5)
    for name, pts, src, dst, stock in cables():
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        ax.plot(xs, ys, color="#e53935", lw=2.2); ax.annotate(name.split(" ")[0], pts[len(pts)//2][:2], fontsize=7, color="#b71c1c", xytext=(3, 3), textcoords="offset points")
    ax.add_patch(Rectangle((GLASS["x0"], GLASS["y0"]), GLASS["x1"]-GLASS["x0"], GLASS["y1"]-GLASS["y0"], fc="#222", alpha=0.6))
    for by in BTN_Y: ax.add_patch(Circle((BTN_X, by), 1.6, fc="#ff6a13", ec="#222"))
    for k, (sx, sy) in SADDLE_SCREWS.items(): ax.add_patch(Circle((sx, sy), 2.5, fc="none", ec="#1565c0", lw=1.5)); ax.text(sx + 3, sy, k, fontsize=7, color="#1565c0")
    for lx in LOUV_F_X: ax.add_patch(Rectangle((lx - 0.6, -WALL), 1.2, WALL, fc="white", ec="#333", lw=0.5))
    for lx in LOUV_B_X: ax.add_patch(Rectangle((lx - 0.6, D), 1.2, WALL, fc="white", ec="#333", lw=0.5))
    for ly in LOUV_R_Y: ax.add_patch(Rectangle((W, ly - 0.6), WALL, 1.2, fc="white", ec="#333", lw=0.5))
    ax.add_patch(Rectangle((-WALL, USB_Y - CH_IN_W/2), WALL, CH_IN_W, fc="white", ec="#333")); ax.text(-WALL - 1, USB_Y, "USB-C\nchute", ha="right", va="center", fontsize=7)
    ax.add_patch(Rectangle((W, SD["y"] - 8), WALL, 16, fc="white", ec="#333")); ax.text(W + WALL + 1, SD["y"], "SD", va="center", fontsize=7)
    ax.annotate("", (-9, -1), (-9, 14), arrowprops=dict(arrowstyle="->", lw=2.5)); ax.text(-11, 7, "CAR FWD", rotation=90, ha="right", va="center", fontsize=8)
    rows = "\n".join(f"{n}: route {L} mm, stock {s} mm ({ok})" for n, L, s, ok in table)
    ax.set_title(f"Layout (roof removed). Interior {W} x {D} x {H_INT}; exterior {W+2*WALL:.1f} x {D+2*WALL:.1f} x {Z_ROOF_TOP - Z_SAD_BOT:.1f} incl. saddle plate\n{rows}", fontsize=8)
    ax.set_xlim(-16, W + 10); ax.set_ylim(-6, D + 6); ax.axis("off")
    fig.savefig(OUT / "layout.png", dpi=170, bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------------------------ Onshape push
DID, WID = "1b4839c0672e56d3fe2d75a5", "651198dd97e5ab64f0fe8355"
PS, FSID = "d2465e2f81e22401d1641c98", "140e3740917b1d9ce55f8791"
API = "https://cad.onshape.com/api/v10"
def api(method, path, body=None, raw=False):
    import requests
    auth = (os.environ["ONSHAPE_ACCESS_KEY"], os.environ["ONSHAPE_SECRET_KEY"])
    for attempt in range(6):   # Onshape returns 429 when the per-minute allocation is exhausted; back off and retry
        r = requests.request(method, API + path, json=body, auth=auth, headers={"Accept": "application/json;charset=UTF-8; qs=0.09" if not raw else "*/*"}, timeout=120, allow_redirects=False)
        if r.status_code != 429: break
        print(f"  429 rate limited, waiting {30 * (attempt + 1)} s"); time.sleep(30 * (attempt + 1))
    if r.status_code in (301, 302, 303, 307, 308):   # export downloads redirect to another host; re-send auth explicitly
        r = requests.get(r.headers["Location"], auth=auth, timeout=300)
    if r.status_code >= 400: raise SystemExit(f"{method} {path} -> {r.status_code}: {r.text[:400]}")
    if raw: return r.content
    return r.json() if r.content.strip() else {}

def push(code):
    api("POST", f"/featurestudios/d/{DID}/w/{WID}/e/{FSID}", {"contents": code})
    specs = api("GET", f"/featurestudios/d/{DID}/w/{WID}/e/{FSID}/featurespecs")
    names = [s.get("featureType") for s in specs.get("featureSpecs", [])]
    if "raceLoggerEnclosure" not in names:
        raise SystemExit("FeatureScript did not compile: " + json.dumps(specs)[:1500])
    feats = api("GET", f"/partstudios/d/{DID}/w/{WID}/e/{PS}/features")
    existing = [f for f in feats["features"] if f.get("featureType") == "raceLoggerEnclosure"]
    if not existing:
        mv = api("GET", f"/documents/d/{DID}/w/{WID}/currentmicroversion")["microversion"]
        feat = {"btType": "BTMFeature-134", "featureType": "raceLoggerEnclosure", "name": "Race logger enclosure", "namespace": f"e{FSID}::m{mv}",
                "parameters": [{"btType": "BTMParameterQuantity-147", "parameterId": "tubeDia", "expression": f"{TUBE_D_DEFAULT} mm", "units": "millimeter", "value": TUBE_D_DEFAULT/1000},
                               *[{"btType": "BTMParameterBoolean-144", "parameterId": p, "value": True} for p in ("buildShell", "buildSled", "buildSaddle", "buildCap", "showBoards")]]}
        api("POST", f"/partstudios/d/{DID}/w/{WID}/e/{PS}/features", {"feature": feat})
    else:
        feat = existing[0]
        for p in feat["parameters"]:
            if p.get("parameterId") in ("buildShell", "buildSled", "buildSaddle", "buildCap", "showBoards", "buildCoupon", "buildBase", "buildTray"): p["value"] = True
        for pid in ("buildCoupon", "buildBase", "buildTray"):
            if not any(p.get("parameterId") == pid for p in feat["parameters"]):
                feat["parameters"].append({"btType": "BTMParameterBoolean-144", "parameterId": pid, "value": True})
        api("POST", f"/partstudios/d/{DID}/w/{WID}/e/{PS}/features/featureid/{feat['featureId']}", {"feature": feat})
    for _ in range(20):
        feats = api("GET", f"/partstudios/d/{DID}/w/{WID}/e/{PS}/features")
        st = {f["name"]: feats["featureStates"].get(f["featureId"], {}).get("featureStatus") for f in feats["features"]}
        if all(v in ("OK", "WARNING") for v in st.values()): break
        time.sleep(3)
    print("feature states:", st)
    if any(v not in ("OK", "WARNING") for v in st.values()):
        # fetch the error message via the feature list with messages
        msgs = api("GET", f"/partstudios/d/{DID}/w/{WID}/e/{PS}/features?noSketchGeometry=true")
        raise SystemExit("Feature regeneration failed: " + json.dumps(msgs.get("featureStates"))[:2000])
    parts = api("GET", f"/parts/d/{DID}/w/{WID}/e/{PS}")
    for p in parts: print(f"  part {p['name']:<22} id={p['partId']}")
    return parts

def export_stl(parts, only=None):
    for p in parts:
        if p["name"].startswith("Board envelope"): continue
        if only and not any(o.lower() in p["name"].lower() for o in only): continue
        data = api("GET", f"/partstudios/d/{DID}/w/{WID}/e/{PS}/stl?units=millimeter&mode=binary&angleTolerance=0.08&chordTolerance=0.04&partIds={p['partId']}", raw=True)
        fn = OUT / (p["name"].replace(" ", "_").lower() + ".stl"); fn.write_bytes(data)
        import pyvista as pv
        m = pv.read(str(fn)); bodies = len(set(m.connectivity()["RegionId"]))
        print(f"  wrote {fn.name} ({len(data)//1024} kB) bodies={bodies} manifold={m.is_manifold}")
        if bodies != 1 or not m.is_manifold: raise SystemExit(f"{p['name']} exported as {bodies} bodies / manifold={m.is_manifold}: not printable")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--only", help="comma-separated part-name substrings to export (saves API calls)")
    ap.add_argument("--local", action="store_true", help="build the tray parts with CadQuery and export their STLs; no Onshape calls"); a = ap.parse_args()
    E, problems, notes, table = validate()
    print(f"interior {W} x {D} x {H_INT} mm, exterior {W+2*WALL:.1f} x {D+2*WALL:.1f}, roof top z {Z_ROOF_TOP}, saddle plate bottom z {Z_SAD_BOT}")
    print(f"v2 tray: {TRAY_H} tall ({TRAY_H - TRAY_FLOOR} inside), footprint {W+2*WALL:.1f} x {D+2*WALL+CHIN_D:.1f}, tray bottom z {Z_TRAY_BOT}; proto headroom {TRAY_H - Z_PROTO_TOP - 0.5:.1f}")
    for n in notes: print("  note", n)
    for row in table: print("  cable", row)
    layout_png(E, table)
    for k, (px, py, kind) in POSTS.items():
        if abs(py - TUBE_CY) < TUBE_D_DEFAULT / 2 + 5: problems.append(f"shell screw {k} sits over the roll bar (no driver access)")
    if problems:
        print("\nCLEARANCE PROBLEMS:"); [print("  -", p) for p in problems]; sys.exit(2)
    print("clearance report: clean")
    code = emit_fs(local=a.local); (HERE / "enclosure.fs").write_text(code); print(f"wrote enclosure.fs ({len(code.splitlines())} lines)")
    if a.local: export_local(emit_fs.last); sys.exit(0)
    if a.dry: sys.exit(0)
    parts = push(code)
    if not a.no_export: export_stl(parts, only=a.only.split(",") if a.only else None)
