"""v2 renders: enclosure + analog tray + connector card + GoPro base, from output/*.stl. Boards drawn as blocks for context."""
import numpy as np, pyvista as pv, sys, os
sys.path.insert(0, os.path.dirname(__file__)); import generate_onshape as g
pv.OFF_SCREEN = True
OUT = g.OUT; R = OUT / "renders"; R.mkdir(exist_ok=True)
GRAY, PURPLE, GRAY2 = "#2f3136", "#6f3fbf", "#3a3d42"
def load(n, t=(0, 0, 0)): return pv.read(str(OUT / f"{n}.stl")).translate(t, inplace=False)
shell, sled = load("shell"), load("sled")
base = load("universal_base_(gopro)", (0, 0, -g.TRAY_H))
tray = load("analog_tray", (-g.TRAY_DX, 0, 0)); card = load("connector_card_(2x_m12)", (-g.TRAY_DX, 0, 0))
riser = load("ads_riser_frame", (-(g.TRAY_DX + g.CARD2_DX), 0, g.Z_ADS1 + g.PCB))
def blk(x0, y0, z0, x1, y1, z1): return pv.Cube(bounds=(x0, x1, y0, y1, z0, z1))
zb = g.Z_TRAY_BOT
boards = [(blk(g.PROTO["x"], g.PROTO["y"], zb + g.Z_BRD, g.PROTO["x"] + g.PROTO["w"], g.PROTO["y"] + g.PROTO["d"], zb + g.Z_PROTO_TOP), "#3f6fb5", 1.0),
          (blk(g.ADS["x"], g.ADS["y"], zb + g.Z_ADS1, g.ADS["x"] + g.ADS["w"], g.ADS["y"] + g.ADS["d"], zb + g.Z_ADS1 + g.PCB), "#2e8b57", 1.0),
          (blk(g.ADS["x"], g.ADS["y"], zb + g.Z_ADS2, g.ADS["x"] + g.ADS["w"], g.ADS["y"] + g.ADS["d"], zb + g.Z_ADS2 + g.PCB), "#2e8b57", 1.0)]
for x, d, lab in g.CONNECTORS:   # connector bodies as cylinders through the card
    boards.append((pv.Cylinder(center=(x, g.CARD_Y0 + 4, zb + g.CONN_Z), direction=(0, 1, 0), radius=g.CONN_BODY_D / 2, height=g.CONN_DEPTH + 10), "#9a9da3", 1.0))
def shot(meshes, fn, pos, up=(0, 0, 1), zoom=1.2, clip=None, size=(1400, 1000), focus=(38.4, 45, -5)):
    pl = pv.Plotter(off_screen=True, window_size=size); pl.set_background("#f2f2f0")
    for m, c, op in meshes:
        mm = m.clip(normal=clip[0], origin=clip[1], invert=False) if clip else m
        if mm.n_points == 0: continue
        pl.add_mesh(mm, color=c, opacity=op, smooth_shading=False, specular=0.2)
    c = np.array(focus, float); d = np.array(pos, float); d /= np.linalg.norm(d)
    if abs(d[2]) > 0.99: up = (0, 1, 0)
    pl.camera_position = [tuple(c + d * 320), tuple(c), up]; pl.camera.zoom(zoom)
    pl.add_light(pv.Light(position=(200, -300, 400), intensity=0.8)); pl.add_light(pv.Light(position=(-300, 200, 200), intensity=0.5))
    pl.screenshot(str(fn)); pl.close()
full = [(shell, GRAY, 1), (sled, PURPLE, 1), (tray, GRAY, 1), (card, GRAY2, 1), (base, GRAY2, 1)]
for v, pos in {"iso": (1, -1, 0.7), "iso_back": (-1, 1, 0.7), "front": (0, -1, 0.12), "right": (1, 0, 0.12), "front_low": (0.6, -1, -0.3)}.items(): shot(full, R / f"v2_{v}.png", pos)
expl = [(shell.translate((0, 0, 50), inplace=False), GRAY, 1), (sled.translate((0, 0, 20), inplace=False), PURPLE, 1), (tray, GRAY, 1),
        (card.translate((0, -30, 0), inplace=False), GRAY2, 1), (riser, GRAY2, 1), (base.translate((0, 0, -30), inplace=False), GRAY2, 1)] + boards
shot(expl, R / "v2_exploded.png", (1, -1, 0.45), zoom=0.85, focus=(38.4, 45, 0))
# tray with boards, sled removed
tb = [(tray, GRAY, 1), (card, GRAY2, 1), (riser, GRAY2, 1)] + boards
shot(tb, R / "tray_top.png", (0, 0, 1), zoom=1.3, focus=(38.4, 45, zb + 10))
shot(tb, R / "tray_iso.png", (1, -1, 0.9), zoom=1.3, focus=(38.4, 45, zb + 10))
shot(tb, R / "tray_iso_back.png", (-1, 1, 0.9), zoom=1.3, focus=(38.4, 45, zb + 10))
shot([(tray, GRAY, 1)], R / "tray_empty_iso.png", (1, -1, 0.9), zoom=1.3, focus=(38.4, 45, zb + 10))
shot([(tray, GRAY, 1)], R / "tray_bottom.png", (0, 0, -1), zoom=1.3, focus=(38.4, 45, zb))
shot(tb, R / "tray_ads_zoom.png", (1, -0.6, 0.7), zoom=3.2, focus=(67, 30, zb + 12))
shot(tb, R / "tray_step_zoom.png", (0.5, -1, 0.5), zoom=2.6, focus=(38, -8, zb + 10))
shot([(card, GRAY2, 1)], R / "card_front.png", (0, -1, 0.2), zoom=1.6, focus=(38.4, -12, zb + 11))
shot([(card, GRAY2, 1)], R / "card_back_iso.png", (0.6, 1, 0.6), zoom=1.6, focus=(38.4, -8, zb + 11))
shot([(riser, GRAY2, 1)], R / "riser_iso.png", (1, -1, 0.9), zoom=2.5, focus=(67, 30, zb + g.Z_ADS1 + 4))
# sections: through the ADS stack and the drop slot (x = 67), and through the proto screws (x = 32.4)
sec = full + boards + [(riser, GRAY2, 1)]
shot(sec, R / "v2_section_ads.png", (-1, -0.3, 0.3), clip=((1, 0, 0), (66.0, 0, 0)), zoom=1.3, focus=(67, 50, 0))
shot(sec, R / "v2_section_proto.png", (1, -0.3, 0.3), clip=((-1, 0, 0), (33.5, 0, 0)), zoom=1.3, focus=(32, 50, 0))
shot(sec, R / "v2_section_y.png", (0.3, -1, 0.3), clip=((0, 1, 0), (0, 4.0, 0)), zoom=1.3, focus=(38, 4, 0))   # through P1/P2 columns: the long screws' path
print("v2 renders done")
