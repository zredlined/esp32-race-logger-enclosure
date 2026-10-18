"""Render the exported STLs: six views per part, assembly iso/exploded, and a section through the stack. pyvista offscreen."""
import numpy as np, pyvista as pv, sys
from pathlib import Path
pv.OFF_SCREEN = True
OUT = Path(__file__).parent / "output"; R = OUT / "renders"; R.mkdir(exist_ok=True)
COL = {"shell": "#2f3136", "sled": "#6f3fbf", "saddle": "#2f3136", "clamp_cap": "#3a3d42", "test_coupon": "#9a9da3", "universal_base_(gopro)": "#2f3136"}
VIEWS = {"iso": (1, -1, 0.8), "iso_back": (-1, 1, 0.8), "top": (0, 0, 1), "bottom": (0, 0, -1), "front": (0, -1, 0.15), "right": (1, 0, 0.15)}
def shot(meshes, fn, pos, up=(0, 0, 1), zoom=1.3, clip=None, size=(1400, 1000), focus=None):
    pl = pv.Plotter(off_screen=True, window_size=size); pl.set_background("#f2f2f0")
    for m, c, op in meshes:
        mm = m.clip(normal=clip[0], origin=clip[1], invert=False) if clip else m
        pl.add_mesh(mm, color=c, opacity=op, smooth_shading=False, specular=0.2, show_edges=False)
    c = np.array(focus) if focus is not None else (np.array(meshes[0][0].center) if len(meshes) == 1 else np.array([38.4, 50, -5]))
    d = np.array(pos, float); d /= np.linalg.norm(d)
    if abs(d[2]) > 0.99: up = (0, 1, 0)
    pl.camera_position = [tuple(c + d * 300), tuple(c), up]; pl.camera.zoom(zoom)
    pl.add_light(pv.Light(position=(200, -300, 400), intensity=0.8)); pl.add_light(pv.Light(position=(-300, 200, 200), intensity=0.5))
    pl.screenshot(str(fn)); pl.close()
parts = {p: pv.read(str(OUT / f"{p}.stl")) for p in COL}
for p, m in parts.items():
    for v, pos in VIEWS.items(): shot([(m, COL[p], 1.0)], R / f"{p}_{v}.png", pos)
asm = [(parts[p], COL[p], 1.0) for p in COL if p not in ("test_coupon", "universal_base_(gopro)")]
shot([(parts["shell"], COL["shell"], 1.0), (parts["sled"], COL["sled"], 1.0), (parts["universal_base_(gopro)"], "#3a3d42", 1.0)], R / "assembly_base_iso_low.png", (1, -1, -0.35), zoom=1.1)
shot(asm, R / "assembly_iso.png", VIEWS["iso"], zoom=1.1); shot(asm, R / "assembly_iso_back.png", VIEWS["iso_back"], zoom=1.1)
expl = [(parts["shell"].translate((0, 0, 45), inplace=False), COL["shell"], 1.0), (parts["sled"], COL["sled"], 1.0),
        (parts["saddle"].translate((0, 0, -25), inplace=False), COL["saddle"], 1.0), (parts["clamp_cap"].translate((0, 0, -60), inplace=False), COL["clamp_cap"], 1.0)]
shot(expl, R / "assembly_exploded.png", (1, -1, 0.5), zoom=0.9)
shot(asm, R / "assembly_section_x.png", (-1, -0.25, 0.35), clip=((1, 0, 0), (28.8, 0, 0)), zoom=1.2, focus=(40, 50, 0))   # keep x>28.8, look from -X: buttons, chute mouth
shot(asm, R / "assembly_section_y.png", (0.25, 1, 0.35), clip=((0, -1, 0), (0, 84.3, 0)), zoom=1.2, focus=(38, 84, 0))  # keep y<84.3, look from +Y at the cut: USB chute, QT, stack standoffs
shot([(parts["shell"], COL["shell"], 1.0)], R / "shell_keys_top_zoom.png", (0.3, -0.5, 1), zoom=3.5, focus=(31, 88, 37))
shot([(parts["shell"], COL["shell"], 1.0)], R / "shell_keys_bottom_zoom.png", (0.3, -0.5, -1), zoom=3.5, focus=(31, 88, 35))
shot([(parts["shell"], COL["shell"], 1.0)], R / "shell_usb_zoom.png", (-1, -0.6, 0.4), zoom=3.5, focus=(0, 84, 8))
shot([(parts["sled"], COL["sled"], 1.0)], R / "sled_imu_zoom.png", (0.6, -1, 0.8), zoom=5, focus=(54, 36, 5))
shot([(parts["sled"], COL["sled"], 1.0), (parts["shell"], COL["shell"], 0.25)], R / "sled_in_shell_top.png", (0, 0, 1), zoom=1.2)
print("rendered", len(list(R.glob("*.png"))), "images")
# v1 configuration set (shell + sled + GoPro base)
v1 = [(parts["shell"], COL["shell"], 1.0), (parts["sled"], COL["sled"], 1.0), (parts["universal_base_(gopro)"], "#3a3d42", 1.0)]
for v, pos in {"iso": (1, -1, 0.8), "iso_back": (-1, 1, 0.8), "front": (0, -1, 0.15), "right": (1, 0, 0.15), "left": (-1, 0, 0.15), "bottom": (0, 0, -1)}.items():
    shot(v1, R / f"v1_{v}.png", pos, zoom=1.15, focus=(38.4, 50, 5))
shot([(parts["shell"].translate((0, 0, 40), inplace=False), COL["shell"], 1.0), (parts["sled"], COL["sled"], 1.0), (parts["universal_base_(gopro)"].translate((0, 0, -25), inplace=False), "#3a3d42", 1.0)], R / "v1_exploded.png", (1, -1, 0.5), zoom=0.9, focus=(38.4, 50, 0))
shot(v1, R / "v1_section_x.png", (-1, -0.25, 0.35), clip=((1, 0, 0), (38.4, 0, 0)), zoom=1.2, focus=(40, 50, 0))
shot(v1, R / "v1_section_y.png", (0.25, 1, 0.35), clip=((0, -1, 0), (0, 36.7, 0)), zoom=1.2, focus=(38, 36, 0))   # through GPS patch / IMU / SHT41 / vent
shot([(parts["sled"], COL["sled"], 1.0)], R / "sled_top_zoom_stack.png", (0.2, -0.4, 1), zoom=2.6, focus=(50, 84, 4))
shot([(parts["sled"], COL["sled"], 1.0)], R / "sled_top_zoom_front.png", (0.2, -0.4, 1), zoom=2.6, focus=(38, 20, 4))
shot([(parts["universal_base_(gopro)"], "#3a3d42", 1.0)], R / "base_bottom_zoom.png", (0.3, -0.6, -1), zoom=2.2, focus=(38.4, 50, -12))
print("v1 set rendered")
