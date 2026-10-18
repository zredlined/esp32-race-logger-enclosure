"""Render the display mount STLs (pyvista offscreen): per-part views, assembled backpack + puck + crown with a glass slab, stand set."""
import numpy as np, pyvista as pv, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import generate_display as g
from pathlib import Path
pv.OFF_SCREEN = True; pv.global_theme.allow_empty_mesh = True
OUT = Path(__file__).parent / "output"; R = OUT / "renders"; R.mkdir(exist_ok=True)
COL = {"backpack": "#2f3136", "gopro_puck": "#3a3d42", "bench_stand": "#2f3136"}
VIEWS = {"iso": (1, -1, 0.8), "iso_back": (-1, 1, 0.8), "iso_back2": (1, 1, -0.8), "top": (0, 0, 1), "bottom": (0, 0, -1), "front": (0, -1, 0.15), "right": (1, 0, 0.15)}
def shot(meshes, fn, pos, up=(0, 0, 1), zoom=1.3, clip=None, size=(1400, 1000), focus=None):
    pl = pv.Plotter(off_screen=True, window_size=size); pl.set_background("#f2f2f0")
    for m, c, op in meshes:
        mm = m.clip(normal=clip[0], origin=clip[1], invert=False) if clip else m
        pl.add_mesh(mm, color=c, opacity=op, smooth_shading=False, specular=0.2, show_edges=False)
    c = np.array(focus) if focus is not None else np.array(meshes[0][0].center)
    d = np.array(pos, float); d /= np.linalg.norm(d)
    if abs(d[2]) > 0.99: up = (0, 1, 0)
    pl.camera_position = [tuple(c + d * 500), tuple(c), up]; pl.camera.zoom(zoom)
    pl.add_light(pv.Light(position=(200, -300, 400), intensity=0.8)); pl.add_light(pv.Light(position=(-300, 200, 200), intensity=0.5))
    pl.screenshot(str(fn)); pl.close()
parts = {p: pv.read(str(OUT / f"{p}.stl")) for p in COL}
# AMS colour change: the top band of the backpack wall (z >= Z_CROWN0) renders orange
bp = parts["backpack"]
parts["crown_ring"] = bp.clip(normal=(0, 0, 1), origin=(0, 0, g.Z_CROWN0), invert=False)   # keeps z > Z_CROWN0
parts["backpack"] = bp.clip(normal=(0, 0, -1), origin=(0, 0, g.Z_CROWN0), invert=False)
COL["crown_ring"] = "#ff6a13"
for p in ("gopro_puck", "bench_stand"):
    for v, pos in VIEWS.items(): shot([(parts[p], COL[p], 1.0)], R / f"{p}_{v}.png", pos)
for v, pos in VIEWS.items(): shot([(parts["backpack"], COL["backpack"], 1.0), (parts["crown_ring"], COL["crown_ring"], 1.0)], R / f"backpack_{v}.png", pos, focus=(0, 1, 12))
# glass slab stand-in for the display
glass = pv.Cube(center=(0, 0, g.Z_GLASS - 2.5), x_length=g.GLASS_W, y_length=g.GLASS_H, z_length=5.0)
asm = [(parts["backpack"], COL["backpack"], 1.0), (parts["crown_ring"], COL["crown_ring"], 1.0), (parts["gopro_puck"], COL["gopro_puck"], 1.0)]
shot(asm + [(glass, "#0b0c0e", 1.0)], R / "asm_front_iso.png", (0.6, -0.8, 1.0), zoom=1.1, focus=(0, 0, 12))
shot(asm + [(glass, "#0b0c0e", 1.0)], R / "asm_front.png", (0, -0.2, 1), zoom=1.1, focus=(0, 0, 12))
shot(asm, R / "asm_back_iso.png", (0.6, -0.8, -1.0), zoom=1.1, focus=(0, 0, 5))
shot(asm, R / "asm_back.png", (0, -0.2, -1), zoom=1.1, focus=(0, 0, 5))
shot(asm, R / "asm_top_edge.png", (0.2, 1, -0.2), zoom=2.5, focus=(15, 58, 10))
shot(asm, R / "asm_section_usb.png", (-1, 0.6, 0.6), clip=((1, 0, 0), (14.8, 0, 0)), zoom=2.2, focus=(15, 45, 10))   # keep x<-14.8: cut through the USB-C notch and slot
shot(asm, R / "asm_section_boss.png", (0, -1, 0.4), clip=((0, 1, 0), (0, 32.9, 0)), zoom=2.0, focus=(0, 33, 10))       # keep y>32.9: cut through the upper bosses
shot([(parts["backpack"], COL["backpack"], 1.0), (parts["crown_ring"], COL["crown_ring"], 1.0)], R / "crown_corner_zoom.png", (1, -1, 0.7), zoom=3.0, focus=(85, -45, 15))
shot([(parts["backpack"], COL["backpack"], 1.0)], R / "plateau_zoom.png", (0.4, -0.6, -1), zoom=3.5, focus=(0, -5, -2))
shot([(parts["backpack"], COL["backpack"], 1.0)], R / "louver_zoom.png", (0.4, -0.6, -1), zoom=3.5, focus=(44, -34, 0))
shot([(parts["backpack"], COL["backpack"], 1.0), (parts["crown_ring"], COL["crown_ring"], 1.0)], R / "rib_zoom.png", (1, -0.5, 0.35), zoom=3.5, focus=(99, 1, 11))
shot([(parts["backpack"], COL["backpack"], 1.0), (parts["crown_ring"], COL["crown_ring"], 1.0)], R / "ledge_section.png", (1, -0.4, 0.5), clip=((0, 1, 0), (0, 1.0, 0)), zoom=5.0, focus=(96, 1, 18))   # keep y>1: section through the right wall and ledge stairs
shot([(parts["backpack"], COL["backpack"], 1.0)], R / "recess_zoom.png", (0.4, -0.6, -1), zoom=3.5, focus=(0, -5, 0))
shot([(parts["bench_stand"], COL["bench_stand"], 1.0)], R / "stand_top.png", (0.15, -0.6, 1), zoom=1.6, focus=(260, 0, 6))
print("rendered", len(list(R.glob("*.png"))), "images")
