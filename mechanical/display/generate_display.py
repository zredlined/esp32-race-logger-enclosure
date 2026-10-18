#!/usr/bin/env python
"""Waveshare ESP32-S3-Touch-LCD-7B display mount: constants -> checks -> FeatureScript -> Onshape (race-display document).

Frame: X = display width as seen from the FRONT (viewer's right is +X), Y = up (connector edge is the bottom, -Y),
Z = toward the viewer. Z = 0 is the backpack's rear face (print bed). Origin at the cover-glass center.
Mapping from the Waveshare STEP (Xs width, Ys thickness toward viewer, Zs height): X = Xs, Y = -Zs, Z = Ys + Z_STEP_OFF.
(Rotated 180 deg on 2026-09-15: the panel's native image is upright with the connector edge at the TOP.)
Parts: Backpack (charcoal), Crown ring (orange, glued on pegs), GoPro puck (charcoal, 4 x M2.5 into inserts),
Bench stand (charcoal, 2-finger tab). Display mounts with 4 x M3 into its own frame lugs.

Usage: generate_display.py [--dry] [--no-export]
"""
import sys, os, json, argparse, time
from urllib.parse import quote
from pathlib import Path
HERE = Path(__file__).parent
OUT = HERE / "output"; OUT.mkdir(exist_ok=True)

# ------------------------------------------------------------------ display (from mechanical/reference/waveshare-7b/dimensions.md)
GLASS_W, GLASS_H, GLASS_R = 192.96, 110.76, 7.88
GLASS_CY = -1.02                                         # glass center (STEP Zs -54.36..56.40, negated); the wall is centered on the glass
GLASS_T_TO_FRAME = 8.5                                  # glass face to LCD frame back
FRAME = dict(x0=-81.05, x1=84.35, y0=-51.18, y1=46.42)  # LCD metal frame outline
PCB = dict(x0=-55.09, x1=50.93, y0=-26.79, y1=46.22, t=1.6)
COMP_H = 8.3                                            # tallest part below the PCB back (terminal blocks)
LUGS = [(-61.6, 32.8), (-61.6, -32.9), (64.6, 32.8), (64.6, -32.9)]   # M3 threaded lugs on the frame back, 15 x 8 pads
LUG_PAD = (15.0, 8.0)
USB_X, USB_W = 14.8, 9.0                                # USB-C receptacle center on the TOP PCB edge
ESP32 = dict(x0=-52.7, x1=-34.7, y0=20.8, y1=46.3)     # module (antenna at the top edge, viewer's left)
TERM = dict(x0=45.4, x1=50.4, y0=-23.9, y1=23.0)        # terminal block row, faces +X

# ------------------------------------------------------------------ backpack
PLATE_T, WALL = 3.0, 2.4
CLR_GLASS = 0.6                                          # wall inner face to glass edge (v1 had 1.0: visible dark gap)
GLASS_T = 1.0                                            # cover glass thickness at the overhang (STEP probe)
CLR_COMP = 1.5                                           # plate front to tallest component
BOSS_D = 9.0                                             # 1.4 mm wall around the 6.2 counterbore (was 8.0 / 0.9 mm with the deeper counterbore)
Z_FRAME = PLATE_T + PCB["t"] + COMP_H + CLR_COMP        # 14.4 -> round up
Z_FRAME = 15.0
Z_GLASS = Z_FRAME + GLASS_T_TO_FRAME                    # 23.5 glass face
Z_STEP_OFF = Z_GLASS - 0.8                               # STEP glass face is at Ys = +0.8
REVEAL, CROWN_H = 0.5, 2.0                               # glass face stands REVEAL proud of the wall top (never flush, never sunk)
Z_CROWN1 = Z_GLASS - REVEAL; Z_CROWN0 = Z_CROWN1 - CROWN_H; Z_WALL = Z_CROWN0
IN_W, IN_H, IN_R = GLASS_W + 2 * CLR_GLASS, GLASS_H + 2 * CLR_GLASS, GLASS_R + CLR_GLASS
OUT_W, OUT_H, OUT_R = IN_W + 2 * WALL, IN_H + 2 * WALL, IN_R + WALL
CHAMF_REAR = 1.5
PEGS = [(x, GLASS_CY + y) for x in (-60.0, 0.0, 60.0) for y in (-(IN_H/2 + WALL/2), IN_H/2 + WALL/2)] + [(sgn * (IN_W/2 + WALL/2), GLASS_CY) for sgn in (-1, 1)]
PEG_D, PEG_H, PEG_HOLE = 1.8, 1.2, 2.1
# M3 screws through the bosses into the lugs. Measured 2026-09-13: an M3 screw goes ~3 mm into a lug; engage 2.5, 0.5 short of bottoming.
M3_CLR, M3_HEAD_D = 3.4, 6.2
SCREW_LEN_DEFAULT, ENGAGE = 10.0, 4.5                    # counterbore depth = Z_FRAME - (screwLen - ENGAGE) = 9.5. Depth coupon 2026-09-15: 9.5 seats firmly, 8.5 gives only ~1.6 mm of thread; the lug thread starts ~2 mm below the STEP surface.
# USB-C: straight-plug notch in the bottom wall (bench) + right-angle cable slot through the plate (car)
NOTCH_W, NOTCH_Z0, NOTCH_Z1 = 16.0, 6.0, 17.5
SLOT = dict(x0=-6.0, x1=6.0, y0=-52.0, y1=-47.0)
# louvers over the ESP32 module (right) and mirrored over the terminal row (left)
LOUV_W, LOUV_L, LOUV_P, LOUV_N = 1.2, 14.0, 3.2, 7
LOUV_Y0 = 24.0; LOUV_CX = (ESP32["x0"] + ESP32["x1"]) / 2
# ribbed grip zones on the two short end walls: vertical grooves, centred on the glass centre, stopping short of the rear chamfer and the orange band
RIB_RUN, RIB_PITCH, RIB_W, RIB_D = 30.0, 1.2, 0.6, 0.6
RIB_Z0, RIB_Z1 = CHAMF_REAR + 1.0, Z_CROWN0 - 1.0
# glass ledge: the glass overhang rests on ASA, no foam. Bosses are the hard stop; the ledge sits 0.1 under the glass so the screws
# never preload the glass. Built as 6 stair steps (0.5 rise / 0.5 run) so it prints without support.
LEDGE_W, LEDGE_STEPS = 3.0, 6
LEDGE_GAP = 0.1                                          # user prefers the tight fit (2026-09-14); the tape liner may lightly touch the ledge. Set ~0 and shorten the bosses 0.2 if the glass is ever bonded.
Z_LEDGE = Z_GLASS - GLASS_T - LEDGE_GAP                  # 22.4
# plateau with M2.5 inserts for the puck: a raised block on the INSIDE of the plate (display components clear it by 4.6 mm), so the rear face stays flat
PLAT_W, PLAT_H, PLAT_T, PLAT_R = 40.0, 36.0, 3.5, 5.0
HOLE_M25, PILOT_DEPTH, LEADIN_D, LEADIN_H = 2.4, 5.0, 3.2, 0.4   # M2.5 self-tapping pilots (coupon 2026-09-12: 2.4 best), no inserts
PUCK_SCREWS = [(sx * 13.0, sy * 11.0) for sx in (-1, 1) for sy in (-1, 1)]
RECESS_CLR, RECESS_D = 0.25, 0.6                          # puck nests in a recess in the rear face: self-aligning, marks the spot
DOTS = [(-6.0, -24.0), (-2.0, -24.0), (2.0, -24.0), (6.0, -24.0)]   # engraved 4-dot mark
DOT_D, DOT_DEPTH = 1.5, 0.4
# ------------------------------------------------------------------ GoPro puck and stand
FINGER_T, FINGER_GAP, FINGER_L, FINGER_H = 2.9, 3.6, 15.0, 18.0   # v3: fingers 0.1 thinner, gaps 0.2 wider (printed v2 bound), fingers 4 mm longer so the M5 knob clears the backpack
PUCK_W, PUCK_H, PUCK_T, PUCK_R = 36.0, 32.0, 4.0, 5.0
CLR_M25, CBORE_D, CBORE_H = 2.7, 5.0, 1.5
BOLT_R = 2.8                                             # M5 thumbscrew: 5.6 mm hole (v2's 5.2 printed tight and the two parts did not line up)
STAND_W, STAND_D, STAND_T, STAND_R = 130.0, 90.0, 6.0, 5.0
FIN_W, FIN_D, Z_FIN = 30.0, 12.0, 52.0
FIN_Y = 0.0                                              # fin centred on the base (no branding, user's call 2026-09-13)
SLOTS_N, SLOT_L, SLOT_W_B, SLOT_PITCH, SLOT_ANG, SLOT_CX = 5, 40.0, 3.5, 6.0, 70.0, 40.0   # angled through-slots, one parallelogram field each side of the fin
Z_PIVOT = 68.0                                           # display bottom edge is OUT_H/2 - 1 below the pivot -> ~9 mm off the desk
Z_FINGER_TOP = Z_PIVOT + FINGER_L / 2

FRAME_RIM_Z1 = 18.0                                      # the frame's outer rim occupies Z 17.5..18.0 (STEP probe)

def checks():
    p = []
    if Z_FRAME - PLATE_T < PCB["t"] + COMP_H + 1.0: p.append("bosses too short for the terminal blocks")
    if NOTCH_Z1 > Z_WALL - 3.0: p.append("USB notch leaves less than 3 mm of wall bridge under the orange band")
    # the cable runs between the plate (z 3) and the LCD frame back (z 15); the slot only has to clear the wall and the PCB footprint
    if SLOT["y0"] < GLASS_CY - IN_H/2 + 0.5 or SLOT["y1"] > PCB["y0"] - 0.5: p.append("cable slot is under the wall or the PCB")
    for lx, ly in LUGS:
        if abs(lx) + BOSS_D/2 > IN_W/2 - 0.5: p.append("boss outside the wall")
        if PCB["x0"] - BOSS_D/2 < lx < PCB["x1"] + BOSS_D/2 and PCB["y0"] < ly < PCB["y1"]: p.append(f"boss at {lx},{ly} overlaps the PCB")
    for sx, sy in PUCK_SCREWS:
        if abs(sx) < (3 * FINGER_T + 2 * FINGER_GAP) / 2 + CBORE_D/2 and abs(sy) < FINGER_L/2 + CBORE_D/2: p.append("puck screw head under a finger")
    if PLAT_T + PLATE_T - RECESS_D - PILOT_DEPTH < 0.8: p.append("pilot hole breaks into the cavity")
    if Z_LEDGE >= Z_GLASS - GLASS_T: p.append("ledge would preload the glass")
    if Z_LEDGE - LEDGE_W < FRAME_RIM_Z1 + 1.0: p.append("ledge stairs reach down to the LCD frame rim")
    if IN_H/2 - LEDGE_W < FRAME["y1"] - GLASS_CY + 1.0 or IN_H/2 - LEDGE_W < -FRAME["y0"] + GLASS_CY + 1.0: p.append("ledge overlaps the LCD frame outline (Y)")
    if IN_W/2 - LEDGE_W < max(FRAME["x1"], -FRAME["x0"]) + 1.0: p.append("ledge overlaps the LCD frame outline (X)")
    if NOTCH_Z1 > Z_LEDGE - LEDGE_W - 0.5: p.append("USB notch cuts into the ledge stairs")
    if WALL - RIB_D < 1.2: p.append("rib grooves leave less than 1.2 mm of wall")
    if RIB_RUN / 2 > IN_H / 2 - IN_R: p.append("rib zone runs into the corner radius")
    import math
    ext_x = (SLOTS_N - 1) / 2 * SLOT_PITCH + SLOT_L/2 * math.cos(math.radians(SLOT_ANG)) + SLOT_W_B/2
    ext_y = SLOT_L/2 * math.sin(math.radians(SLOT_ANG)) + SLOT_W_B/2
    if SLOT_CX - ext_x < FIN_W/2 + 4.0: p.append("base slots run into the fin")
    if SLOT_CX + ext_x > STAND_W/2 - 4.0 or ext_y > STAND_D/2 - 4.0: p.append("base slots run off the base")
    if OUT_H/2 + GLASS_CY > Z_PIVOT - 5: p.append("display bottom edge hits the desk on the stand")
    return p

# ------------------------------------------------------------------ FeatureScript emission (same helper set as the enclosure)
class FS:
    def __init__(self): self.lines = []; self.n = 0
    def uid(self, tag): self.n += 1; return f'id + "{tag}{self.n}"'
    def w(self, s): self.lines.append("        " + s)
    def _n(self, v): return v.split()[-1][1:-1]
    def box(self, x0, y0, z0, x1, y1, z1, tag="b"):
        v = self.uid(tag); n = self._n(v); self.w(f"var {n} = mkBox(context, {v}, {min(x0,x1):.3f}, {min(y0,y1):.3f}, {min(z0,z1):.3f}, {max(x0,x1):.3f}, {max(y0,y1):.3f}, {max(z0,z1):.3f});"); return n
    def rbox(self, x0, y0, z0, x1, y1, z1, r, tag="rb"):
        n = self.box(x0, y0, z0, x1, y1, z1, tag); self.filletz(n, r); return n
    def cylz(self, cx, cy, z0, z1, d, tag="c"):
        v = self.uid(tag); n = self._n(v); self.w(f"var {n} = cylZ(context, {v}, {cx:.3f}, {cy:.3f}, {min(z0,z1):.3f}, {max(z0,z1):.3f}, {d:.3f});"); return n
    def cylx(self, cy, cz, x0, x1, r, tag="cx"):
        v = self.uid(tag); n = self._n(v); self.w(f"var {n} = cylX(context, {v}, {cy:.3f}, {cz:.3f}, {x0:.3f}, {x1:.3f}, {r});"); return n
    def unite(self, names, tag="u"):
        v = self.uid(tag); n = self._n(v); self.w(f"var {n} = mkUnite(context, {v}, [{', '.join(names)}]);"); return n
    def cut(self, target, tools, tag="k"):
        if not tools: return target
        v = self.uid(tag); n = self._n(v); self.w(f"var {n} = mkCut(context, {v}, {target}, [{', '.join(tools)}]);"); return n
    def filletz(self, body, r, tag="f"): v = self.uid(tag); self.w(f"filletZ(context, {v}, {body}, {r});")
    def chamfer_bottom(self, body, w, tag="cb"): v = self.uid(tag); self.w(f"chamferBottom(context, {v}, {body}, {w});")
    def chamfer_top(self, body, w, tag="ch"): v = self.uid(tag); self.w(f"chamferTop(context, {v}, {body}, {w});")
    def round_top_x(self, body, r, tag="ft"):
        v = self.uid(tag); self.w(f"opFillet(context, {v}, {{ \"entities\" : qParallelEdges(qAdjacent(qFarthestAlong(qOwnedByBody({body}, EntityType.FACE), vector(0, 0, 1)), AdjacencyType.EDGE, EntityType.EDGE), vector(1, 0, 0)), \"radius\" : {r} * millimeter }});")
    def rotz(self, body, cx, cy, ang, tag="r"): v = self.uid(tag); self.w(f"rotZ(context, {v}, {body}, {cx:.3f}, {cy:.3f}, {ang});")
    def name(self, body, label, rgb): self.w(f'nameBody(context, {body}, "{label}", color({rgb[0]}, {rgb[1]}, {rgb[2]}));')

CHARCOAL, ORANGE, GREY = (0.17, 0.18, 0.20), (1.0, 0.42, 0.07), (0.6, 0.6, 0.62)

def emit_fs():
    fs = FS()
    hw, hh, cy = OUT_W/2, OUT_H/2, GLASS_CY
    # ---------------- BACKPACK
    fs.w("if (definition.buildBackpack) {")
    fs.w(f"const cbDepth = {Z_FRAME:.3f} - (definition.screwLen / millimeter - {ENGAGE:.3f});")
    fs.w("const wallTop = definition.separateCrown ? %.3f : %.3f;" % (Z_WALL, Z_CROWN1))
    body = fs.rbox(-hw, cy - hh, 0, hw, cy + hh, Z_CROWN1, OUT_R, "bp"); fs.chamfer_bottom(body, CHAMF_REAR); fs.chamfer_top(body, 0.5)
    fs.w("if (definition.separateCrown) {")
    trim = fs.box(-hw - 1, cy - hh - 1, Z_WALL, hw + 1, cy + hh + 1, Z_CROWN1 + 1, "trim")
    fs.w(f"var bpt = mkCut(context, {fs.uid('kt')}, {body}, [{trim}]);")
    fs.w("}")
    cav = fs.rbox(-IN_W/2, cy - IN_H/2, PLATE_T, IN_W/2, cy + IN_H/2, Z_CROWN1 + 1, IN_R, "cav")
    body = fs.cut(body, [cav])
    adds = [body]
    for lx, ly in LUGS: adds.append(fs.cylz(lx, ly, PLATE_T - 0.01, Z_FRAME, BOSS_D, "boss"))
    adds.append(fs.rbox(-PLAT_W/2, -PLAT_H/2, PLATE_T - 0.01, PLAT_W/2, PLAT_H/2, PLATE_T + PLAT_T, PLAT_R, "plat"))   # inside the cavity: keeps the rear face flat for the print bed
    fs.w("if (definition.separateCrown) {")
    pegs = [fs.cylz(px, py, Z_WALL - 0.01, Z_WALL + PEG_H, PEG_D, "peg") for px, py in PEGS]
    fs.w(f"var bpp = mkUnite(context, {fs.uid('up')}, [{body}, {', '.join(pegs)}]);")
    fs.w("}")
    for k in range(LEDGE_STEPS):   # ledge stairs, widest step on top
        w = LEDGE_W * (k + 1) / LEDGE_STEPS; rise = LEDGE_W / LEDGE_STEPS
        z0 = Z_LEDGE - LEDGE_W + k * rise; z1 = z0 + rise + (0.01 if k < LEDGE_STEPS - 1 else 0.0)
        ring = fs.rbox(-IN_W/2 - 0.5, cy - IN_H/2 - 0.5, z0, IN_W/2 + 0.5, cy + IN_H/2 + 0.5, z1, IN_R + 0.5, "ledge")
        hole = fs.rbox(-IN_W/2 + w, cy - IN_H/2 + w, z0 - 1, IN_W/2 - w, cy + IN_H/2 - w, z1 + 1, max(IN_R - w, 0.5), "ledgeh")
        adds.append(fs.cut(ring, [hole], "ledgek"))
    body = fs.unite(adds)
    tools = []
    rec = fs.rbox(-(PUCK_W/2 + RECESS_CLR), -(PUCK_H/2 + RECESS_CLR), -1, PUCK_W/2 + RECESS_CLR, PUCK_H/2 + RECESS_CLR, RECESS_D, PUCK_R + RECESS_CLR, "recess"); tools.append(rec)
    for lx, ly in LUGS:
        tools.append(fs.cylz(lx, ly, -1, Z_FRAME + 1, M3_CLR, "m3"))
        fs.w(f"var cb{len(tools)} = cylZ(context, {fs.uid('cbore')}, {lx:.3f}, {ly:.3f}, -1.0, cbDepth, {M3_HEAD_D:.3f});"); tools.append(f"cb{len(tools)}")
    for sx, sy in PUCK_SCREWS:   # self-tapping pilots from the recess floor into the inward plateau, with a lead-in
        tools.append(fs.cylz(sx, sy, -1, RECESS_D + PILOT_DEPTH, HOLE_M25, "pilot"))
        tools.append(fs.cylz(sx, sy, -1, RECESS_D + LEADIN_H, LEADIN_D, "leadin"))
    for dx, dy in DOTS: tools.append(fs.cylz(dx, dy, -1, DOT_DEPTH, DOT_D, "dot"))
    for sgn in (1, -1):
        for k in range(LOUV_N):
            y = LOUV_Y0 + k * LOUV_P
            s = fs.box(sgn * LOUV_CX - LOUV_L/2, y - LOUV_W/2, -1, sgn * LOUV_CX + LOUV_L/2, y + LOUV_W/2, PLATE_T + 1, "louv"); tools.append(s)
    slot = fs.box(SLOT["x0"], SLOT["y0"], -1, SLOT["x1"], SLOT["y1"], PLATE_T + 1, "slot"); fs.filletz(slot, 2.0); tools.append(slot)
    n_rib = int(RIB_RUN / RIB_PITCH) + 1
    for sgn in (1, -1):
        for k in range(n_rib):
            y = cy - RIB_RUN / 2 + k * RIB_PITCH
            tools.append(fs.box(sgn * (hw - RIB_D), y - RIB_W/2, RIB_Z0, sgn * (hw + 1.0), y + RIB_W/2, RIB_Z1, "rib"))
    fs.w("if (definition.usbNotch) {")
    notch = fs.box(USB_X - NOTCH_W/2, cy + IN_H/2 - 1, NOTCH_Z0, USB_X + NOTCH_W/2, cy + hh + 1, NOTCH_Z1, "notch"); fs.w(f"filletX(context, {fs.uid('nf')}, {notch}, 1.5);")
    fs.w(f"var bpn = mkCut(context, {fs.uid('kn')}, {body}, [{notch}]);")
    fs.w("}")
    body = fs.cut(body, tools)
    fs.name(body, "Backpack", CHARCOAL)
    fs.w("}")
    # ---------------- CROWN RING (orange, printed flat, glued on the pegs)
    fs.w("if (definition.separateCrown) {")
    cr = fs.rbox(-hw, cy - hh, Z_CROWN0, hw, cy + hh, Z_CROWN1, OUT_R, "crown")
    crin = fs.rbox(-IN_W/2, cy - IN_H/2, Z_CROWN0 - 1, IN_W/2, cy + IN_H/2, Z_CROWN1 + 1, IN_R, "crin")
    holes = [fs.cylz(px, py, Z_CROWN0 - 1, Z_CROWN0 + PEG_H + 0.3, PEG_HOLE, "ph") for px, py in PEGS]
    cr = fs.cut(cr, [crin] + holes); fs.chamfer_top(cr, 0.5)
    fs.name(cr, "Crown ring", ORANGE)
    fs.w("}")
    # ---------------- GOPRO PUCK (3 fingers, screws to the plateau inserts). Modeled in place behind the backpack.
    fs.w("if (definition.buildPuck) {")
    z1 = RECESS_D; z0 = z1 - PUCK_T   # puck sits in the rear-face recess
    pk = fs.rbox(-PUCK_W/2, -PUCK_H/2, z0, PUCK_W/2, PUCK_H/2, z1, PUCK_R, "puck"); fs.chamfer_top(pk, 0.5)
    fx0 = -(3 * FINGER_T + 2 * FINGER_GAP) / 2
    padds = [pk]
    for i in range(3):
        x0 = fx0 + i * (FINGER_T + FINGER_GAP)
        f = fs.box(x0, -FINGER_L/2, z0 - FINGER_H, x0 + FINGER_T, FINGER_L/2, z0 + 0.5, "finger")
        fs.w(f"opFillet(context, {fs.uid('ff')}, {{ \"entities\" : qParallelEdges(qAdjacent(qFarthestAlong(qOwnedByBody({f}, EntityType.FACE), vector(0, 0, -1)), AdjacencyType.EDGE, EntityType.EDGE), vector(1, 0, 0)), \"radius\" : {FINGER_L/2 - 0.1} * millimeter }});")
        padds.append(f)
    pk = fs.unite(padds)
    ptools = []
    for sx, sy in PUCK_SCREWS:
        ptools.append(fs.cylz(sx, sy, z0 - 1, z1 + 1, CLR_M25, "pclr"))
        ptools.append(fs.cylz(sx, sy, z0 - 1, z0 + CBORE_H, CBORE_D, "pcb"))
    ptools.append(fs.cylx(0.0, z0 - FINGER_H + FINGER_L/2, fx0 - 2, -fx0 + 2, BOLT_R, "bolt"))
    pk = fs.cut(pk, ptools)
    fs.name(pk, "GoPro puck", CHARCOAL)
    fs.w("}")
    # ---------------- BENCH STAND (own frame: desk at Z = 0, offset +260 mm in X so it sits beside the backpack)
    fs.w("if (definition.buildStand) {")
    ox = 260.0
    st = fs.rbox(ox - STAND_W/2, -STAND_D/2, 0, ox + STAND_W/2, STAND_D/2, STAND_T, STAND_R, "stand"); fs.chamfer_bottom(st, 0.5)
    fin = fs.rbox(ox - FIN_W/2, FIN_Y - FIN_D/2, STAND_T - 0.01, ox + FIN_W/2, FIN_Y + FIN_D/2, Z_FIN, FIN_D/2 - 0.1, "fin")
    sadds = [st, fin]
    for cx in (-(FINGER_T + FINGER_GAP) / 2, (FINGER_T + FINGER_GAP) / 2):
        f = fs.box(ox + cx - FINGER_T/2, FIN_Y - FINGER_L/2, Z_FIN - 0.5, ox + cx + FINGER_T/2, FIN_Y + FINGER_L/2, Z_FINGER_TOP, "sfinger")
        fs.round_top_x(f, FINGER_L/2 - 0.1); sadds.append(f)
    st = fs.unite(sadds)
    stools = [fs.cylx(FIN_Y, Z_PIVOT, ox - FIN_W/2 - 1, ox + FIN_W/2 + 1, BOLT_R, "sbolt")]
    for sgn in (-1, 1):
        for k in range(SLOTS_N):
            cx = ox + sgn * SLOT_CX + (k - (SLOTS_N - 1) / 2) * SLOT_PITCH
            sl = fs.box(cx - SLOT_W_B/2, -SLOT_L/2, -1, cx + SLOT_W_B/2, SLOT_L/2, STAND_T + 1, "bslot"); fs.filletz(sl, SLOT_W_B/2 - 0.05)
            fs.rotz(sl, cx, 0.0, 90.0 - SLOT_ANG); stools.append(sl)
    st = fs.cut(st, stools)
    fs.name(st, "Bench stand", CHARCOAL)
    fs.w("}")
    # ---------------- DEPTH COUPON: 5 columns at the real rear-face-to-lug height (Z_FRAME), counterbores 1 mm apart.
    # Screw an M3 x 10 through each onto a display lug; the first column whose head seats firmly without bottoming is the answer.
    fs.w("if (definition.buildCoupon) {")
    COUP_DEPTHS = [7.5, 8.5, 9.5, 10.5, 11.5]; cxo, cyo, pitch = 0.0, -130.0, 14.0
    bar = fs.rbox(cxo - pitch * len(COUP_DEPTHS) / 2, cyo - 7.0, 0.0, cxo + pitch * len(COUP_DEPTHS) / 2, cyo + 7.0, Z_FRAME, 4.0, "coupon"); fs.chamfer_bottom(bar, 0.5)
    ctools = []
    for i, d in enumerate(COUP_DEPTHS):
        x = cxo - pitch * (len(COUP_DEPTHS) - 1) / 2 + i * pitch
        ctools.append(fs.cylz(x, cyo, -1, Z_FRAME + 1, M3_CLR, "cclr"))
        ctools.append(fs.cylz(x, cyo, -1, d, M3_HEAD_D, "ccb"))
        for k in range(i + 1):   # 1..5 dots on the lug-side face, beside the hole: dot count = column index
            ctools.append(fs.cylz(x - 4.5 + k * 2.2, cyo + 5.0, Z_FRAME - DOT_DEPTH, Z_FRAME + 1, 1.2, "cdot"))
    bar = fs.cut(bar, ctools)
    fs.name(bar, "Depth coupon", GREY)
    fs.w("}")
    # ---------------- DISPLAY ENVELOPE (visual): glass slab, LCD frame, PCB + component block
    fs.w("if (definition.showDisplay) {")
    g = fs.rbox(-GLASS_W/2, cy - GLASS_H/2, Z_GLASS - 5.0, GLASS_W/2, cy + GLASS_H/2, Z_GLASS, GLASS_R, "glass"); fs.name(g, "Display envelope glass", (0.05, 0.05, 0.06))
    fr = fs.box(FRAME["x0"], FRAME["y0"], Z_FRAME, FRAME["x1"], FRAME["y1"], Z_GLASS - 5.0, "lcdframe"); fs.name(fr, "Display envelope frame", GREY)
    pc = fs.box(PCB["x0"], PCB["y0"], Z_FRAME - PCB["t"], PCB["x1"], PCB["y1"], Z_FRAME, "pcb"); fs.name(pc, "Display envelope PCB", (0.1, 0.35, 0.2))
    tb = fs.box(TERM["x0"], TERM["y0"], Z_FRAME - PCB["t"] - COMP_H, TERM["x1"], TERM["y1"], Z_FRAME - PCB["t"], "term"); fs.name(tb, "Display envelope terminals", (0.2, 0.5, 0.3))
    us = fs.box(USB_X - USB_W/2, PCB["y1"] - 7.0, Z_FRAME - PCB["t"] - 3.2, USB_X + USB_W/2, PCB["y1"] + 0.5, Z_FRAME - PCB["t"], "usbc"); fs.name(us, "Display envelope USB-C", (0.8, 0.8, 0.2))
    fs.w("}")

    code = '''FeatureScript 3070;
import(path : "onshape/std/common.fs", version : "3070.0");

// GENERATED by mechanical/display/generate_display.py. Edit the Python constants, not this file.
// Waveshare ESP32-S3-Touch-LCD-7B mount: backpack + crown ring + GoPro puck + bench stand.

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

annotation { "Feature Type Name" : "Race display mount" }
export const raceDisplayMount = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "M3 screw length (display lugs)" }
        isLength(definition.screwLen, { (millimeter) : [6, %(screw)s, 20] } as LengthBoundSpec);
        annotation { "Name" : "Build backpack", "Default" : true } definition.buildBackpack is boolean;
        annotation { "Name" : "Straight USB-C plug notch in the bottom wall", "Default" : true } definition.usbNotch is boolean;
        annotation { "Name" : "Separate crown ring (no AMS: glue-on part instead of a layer colour change)", "Default" : false } definition.separateCrown is boolean;
        annotation { "Name" : "Build GoPro puck", "Default" : true } definition.buildPuck is boolean;
        annotation { "Name" : "Build bench stand", "Default" : true } definition.buildStand is boolean;
        annotation { "Name" : "Show display envelope", "Default" : true } definition.showDisplay is boolean;
        annotation { "Name" : "Build M3 depth coupon", "Default" : true } definition.buildCoupon is boolean;
    }
    {
%(body)s
    });
''' % {"screw": SCREW_LEN_DEFAULT, "body": "\n".join(fs.lines)}
    return code

# ------------------------------------------------------------------ Onshape push (race-display document)
DID, WID = "f0ee92e6ca4b95fa969eb547", "709418fae93574f00ecbe68a"
PS = "abaed47a0bff127df8ddc54b"
FSID_FILE = HERE / ".featurestudio_eid"
API = "https://cad.onshape.com/api/v10"
def api(method, path, body=None, raw=False):
    import requests
    auth = (os.environ["ONSHAPE_ACCESS_KEY"], os.environ["ONSHAPE_SECRET_KEY"])
    r = requests.request(method, API + path, json=body, auth=auth, headers={"Accept": "application/json;charset=UTF-8; qs=0.09" if not raw else "*/*"}, timeout=120, allow_redirects=False)
    if r.status_code in (301, 302, 303, 307, 308):
        r = requests.get(r.headers["Location"], auth=auth, timeout=300)
    if r.status_code >= 400: raise SystemExit(f"{method} {path} -> {r.status_code}: {r.text[:400]}")
    if raw: return r.content
    return r.json() if r.content.strip() else {}

def feature_studio():
    if FSID_FILE.exists(): return FSID_FILE.read_text().strip()
    for e in api("GET", f"/documents/d/{DID}/w/{WID}/elements"):
        if e["elementType"] == "FEATURESTUDIO" and e["name"] == "Display mount FeatureScript": FSID_FILE.write_text(e["id"]); return e["id"]
    fsid = api("POST", f"/featurestudios/d/{DID}/w/{WID}", {"name": "Display mount FeatureScript"})["id"]
    FSID_FILE.write_text(fsid); return fsid

BOOLS = ("buildBackpack", "usbNotch", "buildPuck", "buildStand", "showDisplay", "buildCoupon")
FALSE_BOOLS = ("separateCrown",)
def push(code):
    fsid = feature_studio()
    api("POST", f"/featurestudios/d/{DID}/w/{WID}/e/{fsid}", {"contents": code})
    specs = api("GET", f"/featurestudios/d/{DID}/w/{WID}/e/{fsid}/featurespecs")
    names = [s.get("featureType") for s in specs.get("featureSpecs", [])]
    if "raceDisplayMount" not in names: raise SystemExit("FeatureScript did not compile: " + json.dumps(specs)[:1500])
    feats = api("GET", f"/partstudios/d/{DID}/w/{WID}/e/{PS}/features")
    existing = [f for f in feats["features"] if f.get("featureType") == "raceDisplayMount"]
    if not existing:
        mv = api("GET", f"/documents/d/{DID}/w/{WID}/currentmicroversion")["microversion"]
        feat = {"btType": "BTMFeature-134", "featureType": "raceDisplayMount", "name": "Race display mount", "namespace": f"e{fsid}::m{mv}",
                "parameters": [{"btType": "BTMParameterQuantity-147", "parameterId": "screwLen", "expression": f"{SCREW_LEN_DEFAULT} mm", "units": "millimeter", "value": SCREW_LEN_DEFAULT/1000},
                               *[{"btType": "BTMParameterBoolean-144", "parameterId": p, "value": True} for p in BOOLS], *[{"btType": "BTMParameterBoolean-144", "parameterId": p, "value": False} for p in FALSE_BOOLS]]}
        api("POST", f"/partstudios/d/{DID}/w/{WID}/e/{PS}/features", {"feature": feat})
    else:
        feat = existing[0]
        for p in feat["parameters"]:
            if p.get("parameterId") in BOOLS: p["value"] = True
            if p.get("parameterId") in FALSE_BOOLS: p["value"] = False
            if p.get("parameterId") == "screwLen": p["expression"] = f"{SCREW_LEN_DEFAULT} mm"; p["value"] = SCREW_LEN_DEFAULT / 1000
        for pid in BOOLS:
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
        raise SystemExit("Feature regeneration failed: " + json.dumps(feats.get("featureStates"))[:2000])
    parts = api("GET", f"/parts/d/{DID}/w/{WID}/e/{PS}")
    for p in parts: print(f"  part {p['name']:<28} id={p['partId']}")
    return parts

def export_stl(parts):
    import pyvista as pv
    for p in parts:
        if p["name"].startswith("Display envelope"): continue
        data = api("GET", f"/partstudios/d/{DID}/w/{WID}/e/{PS}/stl?units=millimeter&mode=binary&angleTolerance=0.08&chordTolerance=0.04&partIds={quote(p['partId'], safe='')}", raw=True)
        fn = OUT / (p["name"].replace(" ", "_").lower() + ".stl"); fn.write_bytes(data)
        m = pv.read(str(fn)); bodies = len(set(m.connectivity()["RegionId"]))
        pr = m.rotate_x(180, inplace=False) if p["name"] == "GoPro puck" else m.copy()
        pr.translate((0, 0, -pr.bounds[4]), inplace=True); pr.save(str(OUT / ("print_" + fn.name)))
        print(f"  wrote {fn.name} ({len(data)//1024} kB) bodies={bodies} manifold={m.is_manifold}")
        if bodies != 1 or not m.is_manifold: raise SystemExit(f"{p['name']} exported as {bodies} bodies / manifold={m.is_manifold}: not printable")
        if p["name"] == "Backpack":   # the cavity must be open: no triangle at the wall top may span the interior
            import numpy as np
            pts = m.points; faces = m.faces.reshape(-1, 4)[:, 1:]; tri = pts[faces]
            top = np.all(np.abs(tri[:, :, 2] - Z_CROWN1) < 0.01, axis=1); a = 0.5 * np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
            if top.any() and a[top].max() > 200: raise SystemExit("Backpack has a lid over the cavity (top-face triangle area %.0f)" % a[top].max())
            print("  backpack cavity open: largest wall-top triangle %.0f mm2" % a[top].max())

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); ap.add_argument("--no-export", action="store_true"); a = ap.parse_args()
    print(f"backpack {OUT_W:.2f} x {OUT_H:.2f} x {Z_CROWN1:.1f} (wall top {Z_CROWN1}), glass face at z {Z_GLASS}, frame back at z {Z_FRAME}; AMS colour change to orange at z {Z_CROWN0} (print height {Z_CROWN0} from the bed)")
    print(f"assembled depth glass face to puck finger tips: {Z_GLASS + PUCK_T + FINGER_H:.1f} mm; stand pivot {Z_PIVOT}, display bottom edge {Z_PIVOT - (OUT_H/2 - GLASS_CY):.1f} above the desk")
    problems = checks()
    if problems: print("PROBLEMS:"); [print("  -", p) for p in problems]; sys.exit(2)
    print("checks: clean")
    code = emit_fs(); (HERE / "display_mount.fs").write_text(code); print(f"wrote display_mount.fs ({len(code.splitlines())} lines)")
    if a.dry: sys.exit(0)
    parts = push(code)
    if not a.no_export: export_stl(parts)
