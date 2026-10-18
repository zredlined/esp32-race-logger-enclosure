"""Annotated assembly maps drawn from the generator constants (exact positions), saved to docs/assembly/."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import generate_onshape as g
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
OUT = g.HERE.parent / "docs" / "assembly"; OUT.mkdir(exist_ok=True)
W, D, WALL = g.W, g.D, g.WALL
def plate(ax, title):
    ax.set_aspect("equal"); ax.add_patch(FancyBboxPatch((-WALL, -WALL), W + 2*WALL, D + 2*WALL, boxstyle="round,pad=0,rounding_size=5", fc="#ececec", ec="#333", lw=1.5))
    ax.set_xlim(-12, W + 12); ax.set_ylim(-10, D + 8); ax.axis("off"); ax.set_title(title, fontsize=11, loc="left")
    ax.annotate("", (-7, 2), (-7, 20), arrowprops=dict(arrowstyle="->", lw=2)); ax.text(-9, 11, "car\nforward", fontsize=7, ha="right", va="center")
def label(ax, x, y, text, dx=6, dy=6, fs=7, color="#111"):
    ax.annotate(text, (x, y), xytext=(x + dx, y + dy), fontsize=fs, color=color, arrowprops=dict(arrowstyle="-", lw=0.6, color="#555"), ha="left", va="center",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#999", lw=0.5))

# ---------- Figure 1: sled, top view
fig, ax = plt.subplots(figsize=(9, 10.5)); plate(ax, "Fig. 1  Sled, seen from above (boards side). Standoffs take self-tapping screws, no inserts.")
ax.add_patch(Rectangle((0.3, 0.3), W - 0.6, D - 0.6, fc="#f7f7f7", ec="#bbb", lw=0.8))
for b, name, c in ((g.GPS, "GPS PA1010D\non 26 mm pillars", "#d9f2d0"), (g.IMU, "IMU LSM6DSOX", "#f9d9d9"), (g.SHT, "SHT41", "#efe0ff")):
    ax.add_patch(Rectangle((b["x"], b["y"]), b["w"], b["d"], fc=c, ec="#777", lw=0.8, ls="--")); ax.text(b["x"] + b["w"]/2, b["y"] + b["d"]/2, name, ha="center", va="center", fontsize=7)
ax.add_patch(Rectangle((g.X_STK0, g.Y_STK0), g.STACK_L, g.STACK_D, fc="#cfe3ff", ec="#777", lw=0.8, ls="--")); ax.text(g.X_STK0 + 25, g.Y_STK0 + 11.4, "Feather stack: Feather + Adalogger + OLED Wing\nUSB-C end this side  <--", ha="center", va="center", fontsize=7)
for t in g.STANDOFFS:
    x, y, hd, lab = t[:4]; h, d = g.so_geom(t)
    ax.add_patch(Circle((x, y), d/2, fc="#ffb74d" if hd > 2 else "#90caf9", ec="#333", lw=0.8)); ax.add_patch(Circle((x, y), hd/2, fc="white", ec="#333", lw=0.5))
for x, y in g.PADS: ax.add_patch(Circle((x, y), 2.5, fc="#e0e0e0", ec="#333", lw=0.8))
label(ax, g.X_STK0 + 2.54, g.Y_STK0 + 20.32, "Feather, USB end: 2 x M2.5 x 6 self-tap (2.4 mm pilots)", dx=-22, dy=8)
label(ax, g.X_STK0 + 48.26, g.Y_STK0 + 1.84, "Feather, far end: 2 x NYLON M2 x 6 self-tap (1.9 mm pilots)", dx=-52, dy=-7)
label(ax, g.GPS["x"] + 2.54, g.GPS["y"] + 2.54, "GPS: 4 x M2.5 x 6 on the tall pillars", dx=-3, dy=-8)
label(ax, g.IMU["x"] + 2.54, g.IMU["y"] + 2.54, "IMU: 2 x M2.5 x 6 on its left edge;\nright edge slides under the two hooks", dx=-14, dy=-13)
label(ax, g.SHT["x"] + 15.24, g.SHT["y"] + 22.86, "SHT41: 2 x M2.5 x 6 (diagonal);\ngrey pads support the other corners", dx=-30, dy=12)
# chute, ribs, hooks, ledge
ax.add_patch(Rectangle((g.CH_X0, g.CH_Y0), g.CH_X1 - g.CH_X0, g.CH_Y1 - g.CH_Y0, fc="#ddd", ec="#333")); ax.text(11, g.USB_Y, "USB-C\nchute", ha="center", va="center", fontsize=7)
for (x0, y0, x1, y1) in g.RIBS: ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#bbb", ec="#333"))
label(ax, g.RIBS[1][0], 58, "cable guide rib", dx=2, dy=8)
ax.add_patch(Rectangle((g.IMU_LEDGE["x0"], g.IMU_LEDGE["y0"]), g.IMU_LEDGE["x1"] - g.IMU_LEDGE["x0"], g.IMU_LEDGE["y1"] - g.IMU_LEDGE["y0"], fc="#bbb", ec="#333"))
for hx, hy in g.HOOKS: ax.add_patch(Rectangle((hx, hy - 1.25), 1.6, 2.5, fc="#333"))
# holes
for k, (px, py, kind) in g.POSTS.items(): ax.add_patch(Circle((px, py), 2.5, fc="white", ec="#333", lw=1)); ax.add_patch(Circle((px, py), 1.35, fc="#666"))
label(ax, g.POSTS["P1"][0], g.POSTS["P1"][1], "3 counterbored holes (P1, P2, P4): shell screws M2.5 x 8 enter from BELOW", dx=6, dy=-7)
for k, (sx, sy) in g.SADDLE_SCREWS.items(): ax.add_patch(Circle((sx, sy), 1.35, fc="#6f3fbf", ec="#333"))
label(ax, *g.SADDLE_SCREWS["S1"], "S1: base screw M2.5 x 12 from ABOVE, before boards", dx=8, dy=-6)
label(ax, *g.SADDLE_SCREWS["S2"], "S2: base screw M2.5 x 12 from ABOVE", dx=-42, dy=-6)
ax.add_patch(Rectangle((g.VENT["x"] - 3, g.VENT["y"] - 6.75), 6, 13.5, fc="white", ec="#333")); label(ax, g.VENT["x"], g.VENT["y"], "vent (through)", dx=-16, dy=-14)
ax.add_patch(Rectangle((g.DROP["x"] - 5, g.DROP["y"] - 2.5), 10, 5, fc="white", ec="#333")); label(ax, g.DROP["x"], g.DROP["y"], "future cable slot (blanked by the base)", dx=-48, dy=-6)
fig.savefig(OUT / "fig1_sled_map.png", dpi=160, bbox_inches="tight"); plt.close(fig)

# ---------- Figure 2: base, top view (the face the sled sits on)
fig, ax = plt.subplots(figsize=(9, 10.5)); plate(ax, "Fig. 2  Universal base, seen from above (sled side). GoPro fingers are underneath.")
ax.add_patch(FancyBboxPatch((0, 0), W, D, boxstyle="round,pad=0,rounding_size=5", fc="#f0f0f0", ec="#555", lw=1))
for k, (sx, sy) in g.SADDLE_SCREWS.items(): ax.add_patch(Circle((sx, sy), 1.7, fc="#c8a951", ec="#333", lw=1))
label(ax, *g.SADDLE_SCREWS["S1"], "insert: M2.5 heat-set, pressed from THIS face", dx=8, dy=6)
label(ax, *g.SADDLE_SCREWS["S2"], "insert: M2.5 heat-set", dx=-30, dy=8)
for k, (px, py, kind) in g.POSTS.items(): ax.add_patch(Circle((px, py), 3.0, fc="white", ec="#333", lw=1))
label(ax, g.POSTS["P2"][0], g.POSTS["P2"][1], "6 mm access holes (3): screwdriver reaches the shell screws; nothing goes in them", dx=-70, dy=-7)
for (sx, sy) in ((12.0, 12.0), (60.0, 12.0), (12.0, D - 12.0), (60.0, D - 12.0)): ax.add_patch(Rectangle((sx - 10, sy - 2), 20, 4, fc="white", ec="#333"))
label(ax, 12.0, D - 12.0, "strap slots (4): 25 mm Velcro or zip ties, optional", dx=6, dy=6)
ax.add_patch(Rectangle((g.VENT["x"] - 4, g.VENT["y"] - 7.75), 8, 15.5, fc="white", ec="#333")); label(ax, g.VENT["x"], g.VENT["y"], "vent, matches the sled", dx=-26, dy=-14)
fx0 = W/2 - (3*3.0 + 2*3.4)/2
for i in range(3): ax.add_patch(Rectangle((fx0 + i*6.4, D/2 - 7.5), 3.0, 15, fc="#999", ec="#333", ls=":"))
label(ax, W/2, D/2 + 7.5, "GoPro fingers (underneath): M5 thumbscrew, any GoPro mount", dx=-30, dy=10)
fig.savefig(OUT / "fig2_base_map.png", dpi=160, bbox_inches="tight"); plt.close(fig)

# ---------- Figure 3: shell, seen from below (open side)
fig, ax = plt.subplots(figsize=(9, 10.5)); plate(ax, "Fig. 3  Shell, roof made transparent, same orientation as Fig. 1. Three posts take inserts; the pad has none.")
ax.add_patch(Rectangle((0, 0), W, D, fc="#e2e2e2", ec="#555", lw=1))
for k, (px, py, kind) in g.POSTS.items():
    ax.add_patch(Rectangle((px - 4, py - 4), 8, 8, fc="#bbb", ec="#333")); ax.add_patch(Circle((px, py), 1.7, fc="#c8a951", ec="#333"))
ax.add_patch(Rectangle((g.PAD_P3[0] - 4, g.PAD_P3[1] - 4), 8, 8, fc="#bbb", ec="#333"))
label(ax, g.POSTS["P1"][0], g.POSTS["P1"][1], "post P1: M2.5 insert", dx=-30, dy=7); label(ax, g.POSTS["P2"][0], g.POSTS["P2"][1], "post P2: M2.5 insert", dx=-14, dy=9)
label(ax, g.POSTS["P4"][0], g.POSTS["P4"][1], "post P4: M2.5 insert", dx=8, dy=-6); label(ax, *g.PAD_P3, "bearing pad only, no insert", dx=-36, dy=6)
ax.add_patch(Rectangle((g.GLASS["x0"] - 0.3, g.GLASS["y0"] - 0.3), g.GLASS["x1"] - g.GLASS["x0"] + 0.6, g.GLASS["y1"] - g.GLASS["y0"] + 0.6, fc="white", ec="#333")); ax.text((g.GLASS["x0"] + g.GLASS["x1"])/2, (g.GLASS["y0"] + g.GLASS["y1"])/2, "OLED window\n(optional 1 mm smoked lens in the pocket around it)", ha="center", va="center", fontsize=7)
for by in g.BTN_Y: ax.add_patch(Rectangle((g.BTN_X - 6.5, by - g.FLAP_W/2), g.FLAP_L, g.FLAP_W, fc="#ccc", ec="#333")); ax.add_patch(Circle((g.BTN_X, by), 1.1, fc="#333"))
ax.add_patch(Circle((g.RESET_KEY["cx"], g.RESET_KEY["cy"]), g.RESET_KEY["r"], fc="#ccc", ec="#333")); ax.add_patch(Circle((g.RESET_KEY["cx"], g.RESET_KEY["cy"]), 0.9, fc="#333"))
label(ax, g.BTN_X, g.BTN_Y[1], "keys A/B/C with nubs (print-in-place, nothing to add)", dx=-45, dy=-14); label(ax, g.RESET_KEY["cx"], g.RESET_KEY["cy"], "reset key", dx=-22, dy=6)
ax.add_patch(Rectangle((-WALL, g.USB_Y - 6.75), WALL, 13.5, fc="white", ec="#333")); label(ax, -WALL, g.USB_Y, "USB-C opening", dx=-4, dy=-10)
ax.add_patch(Rectangle((W, g.SD["y"] - 8), WALL, 16, fc="white", ec="#333")); label(ax, W + WALL, g.SD["y"], "microSD slot", dx=2, dy=-9)
fig.savefig(OUT / "fig3_shell_map.png", dpi=160, bbox_inches="tight"); plt.close(fig)
print("figures written to", OUT)

# ---------- Figure 4: analog tray (v2), top view, tray frame (same x/y as the case; the step is in front)
fig, ax = plt.subplots(figsize=(9, 11.5)); ax.set_aspect("equal")
ax.add_patch(FancyBboxPatch((-WALL, g.CARD_Y0), W + 2*WALL, D + 2*WALL + g.CHIN_D, boxstyle="round,pad=0,rounding_size=5", fc="#ececec", ec="#333", lw=1.5))
ax.add_patch(Rectangle((0, g.CARD_Y1), W, D - g.CARD_Y1, fc="#f7f7f7", ec="#bbb", lw=0.8))
ax.add_patch(Rectangle((-WALL, g.CARD_Y0), W + 2*WALL, g.CARD_T, fc="#6f3fbf", ec="#333", lw=0.8)); ax.text(W/2, g.CARD_Y0 - 17, "connector card (front face of the step; its roof covers the step)", ha="center", fontsize=7)
for x, dia, lab in g.CONNECTORS: ax.add_patch(Circle((x, g.CARD_Y0 + g.CARD_T/2), dia/2, fc="white", ec="#333", lw=1, clip_on=False)); ax.text(x, g.CARD_Y0 - 12, f"{lab}\n{dia} mm hole", ha="center", va="top", fontsize=6.5)
ax.set_xlim(-14, W + 30); ax.set_ylim(g.CARD_Y0 - 20, D + 8); ax.axis("off")
ax.set_title("Fig. 4  Analog tray (v2), seen from above with the sled removed. Five screw columns, proto board + stacked ADS1115s.", fontsize=11, loc="left")
ax.annotate("", (-7, 2), (-7, 20), arrowprops=dict(arrowstyle="->", lw=2)); ax.text(-9, 11, "car\nforward", fontsize=7, ha="right", va="center")
# boards
P = g.PROTO; ax.add_patch(Rectangle((P["x"], P["y"]), P["w"], P["d"], fc="#dfeaf7", ec="#777", lw=0.8, ls="--"))
ax.text(P["x"] + P["w"]/2, P["y"] + P["d"]/2, "half-size perma-proto 51 x 81.5\n(Brian's conditioning)\n2 x M2.5 x 6 in the centreline holes,\nhooks on the left and front edges,\nback edge slides under the wall lip", ha="center", va="center", fontsize=7)
A = g.ADS; ax.add_patch(Rectangle((A["x"], A["y"]), A["w"], A["d"], fc="#d9f2d0", ec="#777", lw=0.8, ls="--"))
ax.text(A["x"] + A["w"]/2, A["y"] + A["d"]/2, "ADS1115 x2\nstacked\n0x48 below\n0x49 above", ha="center", va="center", fontsize=6.5)
for x, y in g.ADS_HOLES: ax.add_patch(Circle((x, y), g.ADS_SO_D/2, fc="#ffb74d", ec="#333", lw=0.8)); ax.add_patch(Circle((x, y), 1.2, fc="white", ec="#333", lw=0.5))
for x, y in g.PROTO_SCREWS: ax.add_patch(Circle((x, y), 3.0, fc="#ffb74d", ec="#333", lw=0.8)); ax.add_patch(Circle((x, y), 1.2, fc="white", ec="#333", lw=0.5))
for x, y in g.PROTO_PADS: ax.add_patch(Circle((x, y), 2.5, fc="#e0e0e0", ec="#333", lw=0.8))
for edge, c, a in g.PROTO_HOOKS:
    if edge == "left": ax.add_patch(Rectangle((c - 1.8, a - 1.25), 1.6, 2.5, fc="#333"))
    else: ax.add_patch(Rectangle((a - 1.25, c - 1.8), 2.5, 1.6, fc="#333"))
ax.add_patch(Rectangle((g.PROTO_BACK_LIP_X[0], P["y"] + P["d"] - 1.0), 2.5, D - (P["y"] + P["d"] - 1.0), fc="#333"))
# columns and blocks
for k, (cx, cy) in g.TRAY_COLS.items():
    ax.add_patch(Circle((cx, cy), g.COL_D/2, fc="#c8c8c8", ec="#333", lw=1)); ax.add_patch(Circle((cx, cy), 1.35, fc="#666")); ax.text(cx, cy + 5.2, k, ha="center", fontsize=7, fontweight="bold")
ax.add_patch(Rectangle((g.P4_UP[0], g.P4_UP[1]), g.P4_UP[2], D - g.P4_UP[1], fc="#c8c8c8", ec="#333", lw=1)); ax.add_patch(Circle(g.P4, 1.35, fc="#666")); ax.text(g.P4[0] + 1, g.P4[1] - 6, "P4", fontsize=7, fontweight="bold")
ax.add_patch(Rectangle((g.BLOCK_L[0], g.BLOCK_L[1]), g.BLOCK_L[2] - g.BLOCK_L[0], g.BLOCK_L[3] - g.BLOCK_L[1], fc="#c8c8c8", ec="#333", lw=1))
ax.add_patch(Rectangle((g.BLOCK_R[0], g.BLOCK_R[1]), g.BLOCK_R[2] - g.BLOCK_R[0], g.BLOCK_R[3] - g.BLOCK_R[1], fc="#c8c8c8", ec="#333", lw=1))
ax.add_patch(Rectangle((g.S2_BRIDGE[0], g.S2_BRIDGE[1]), g.S2_BRIDGE[2] - g.S2_BRIDGE[0], g.S2_BRIDGE[3] - g.S2_BRIDGE[1], fc="#c8c8c8", ec="#333", lw=1))
for x, z in g.CARD_SCREWS: ax.add_patch(Circle((x, g.CARD_Y0 + 1.2), 1.35, fc="#6f3fbf", ec="#333", clip_on=False))
# drop slot projection and cables
ax.add_patch(Rectangle((g.DROP["x"] - g.DROP["w"]/2, g.DROP["y"] - g.DROP["d"]/2), g.DROP["w"], g.DROP["d"], fc="none", ec="#d32f2f", lw=1.2, ls=":"))
for name, pts in g.tray_cables(): ax.plot([q[0] for q in pts], [q[1] for q in pts], color="#d32f2f", lw=1.8, alpha=0.8)
label(ax, g.DROP["x"], g.DROP["y"], "drop slot in the sled above: 100 mm cable from the\nSHT41's rear connector down to the UPPER ADS's rear connector", dx=-56, dy=14)
label(ax, g.ADS_CONN_X, A["y"] - 6, "50 mm hairpin: lower ADS front -> upper ADS front\n(vertical loop in front of the stack)", dx=14, dy=-20)
label(ax, g.TRAY_COLS["P2"][0], g.TRAY_COLS["P2"][1], "P1, P2, P4: shell screws M2.5 x 25 from BELOW\n(heads seat 7 mm up the column, reached through the base)", dx=8, dy=16)
label(ax, g.TRAY_COLS["S1"][0], g.TRAY_COLS["S1"][1], "S1, S2: insert in the column top, M2.5 x 8 from the sled;\nM2.5 x 10 from below through the base insert into the column bottom", dx=-34, dy=-6)
label(ax, g.CARD_SCREWS[0][0], g.CARD_Y0 + 1.2, "card: 2 x M2.5 x 8 self-tap\ninto the corner blocks", dx=-14, dy=-9)
label(ax, g.CONNECTORS[0][0], g.CARD_Y1 + 9, "connector bodies up to 18 mm deep and\n17 mm across fit under the step roof", dx=-8, dy=-4)
fig.savefig(OUT / "fig4_tray_map.png", dpi=160, bbox_inches="tight"); plt.close(fig)
print("figures written to", OUT)
