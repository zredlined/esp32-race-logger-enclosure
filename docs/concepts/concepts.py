"""Concept massing models + layout drawing for the race logger enclosure.
Not the real CAD (that is Onshape). These are proportion studies from true board dimensions.
Run: $PY docs/concepts/concepts.py   -> writes PNGs next to this file.
"""
import math, os
from pathlib import Path
import cadquery as cq
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch
import pyvista as pv
pv.OFF_SCREEN = True
OUT = Path(__file__).parent

# ---------------- shared layout (mm, interior coords: origin inner front-left corner on the floor) ----------------
WALL, FLOOR, ROOF = 2.4, 2.5, 2.0
W, D = 75.2, 77.2                      # interior
STANDOFF = 4.0; PCB = 1.57
LANE_F = (0, 14); ROW_S = (14, 39.4); LANE_M = (39.4, 53.4); ROW_STACK = (53.4, 76.26)
STACK = dict(x=(W-3-50.8, W-3), y=ROW_STACK)                 # Feather stack, USB end toward -X
GPS   = dict(x=(3, 28.4),  y=(14, 39.4), conn_x=15.7)         # connectors face +-Y
IMU   = dict(x=(32, 49.8), y=(14, 39.4), conn_x=40.9)
SHT   = dict(x=(54, 71.8), y=(14, 39.4), conn_x=62.9)
Z_FEATHER_TOP = STANDOFF + PCB
Z_GLASS_TOP = Z_FEATHER_TOP + 22.2
H_INT = Z_GLASS_TOP + 0.5
H_EXT = FLOOR + H_INT + ROOF           # ~32.8
W_EXT, D_EXT = W + 2*WALL, D + 2*WALL   # 80 x 82
sx0 = STACK["x"][0]; sy0 = STACK["y"][0]
WINDOW = (sx0+9.97, sy0+2.93, 37.1, 17.0)               # x, y, w, h over OLED glass
BUTTONS = [(sx0+4.3, sy0+yy) for yy in (7.0, 11.4, 15.9)]
RESET = (sx0+7.4, sy0+20.8)
GPS_PATCH = (GPS["x"][0]+12.7, GPS["y"][0]+12.7)
USB = dict(y=sy0+11.43, z=Z_FEATHER_TOP+1.1)
SD  = dict(y=sy0+11.4,  z=Z_FEATHER_TOP+8.5+PCB+0.5)
TUBE_D = 38.1

def snake():
    """Cable polyline (x, y) in plan for the daisy chain OLED->GPS->IMU->SHT41."""
    zq = Z_FEATHER_TOP + 17
    pts = [("OLED QT", (sx0, sy0+11.43)), (None,(sx0-10, sy0+11.43)), (None,(sx0-6, LANE_M[1]-6)), (None,(GPS["conn_x"], LANE_M[0]+6)),
           ("GPS in", (GPS["conn_x"], GPS["y"][1])), ("GPS out", (GPS["conn_x"], GPS["y"][0])), (None,(GPS["conn_x"], 6)), (None,(IMU["conn_x"], 6)),
           ("IMU in", (IMU["conn_x"], IMU["y"][0])), ("IMU out", (IMU["conn_x"], IMU["y"][1])), (None,(IMU["conn_x"], LANE_M[0]+7)), (None,(SHT["conn_x"], LANE_M[0]+7)),
           ("SHT41 in", (SHT["conn_x"], SHT["y"][1]))]
    return pts

# ---------------- layout drawing ----------------
def layout_png():
    fig, ax = plt.subplots(figsize=(9, 9)); ax.set_aspect("equal")
    ax.add_patch(Rectangle((-WALL,-WALL), W_EXT, D_EXT, fc="#e9e9e9", ec="#333", lw=2))
    ax.add_patch(Rectangle((0,0), W, D, fc="white", ec="#999", lw=1))
    for (a,b),c,n in ((LANE_F,"#fff3e0","front cable lane 14"),(LANE_M,"#fff3e0","middle cable lane 14")):
        ax.add_patch(Rectangle((0,a), W, b-a, fc=c, ec="none")); ax.text(W/2, (a+b)/2, n, ha="center", va="center", fontsize=8, color="#b26a00")
    ax.add_patch(Rectangle((0, sy0), sx0, 22.86, fc="#fff3e0", ec="none")); ax.text(sx0/2, sy0+11, "USB +\nQT drop\nlane", ha="center", va="center", fontsize=7, color="#b26a00")
    def board(b, name, color):
        x0,x1 = b["x"]; y0,y1 = b["y"]
        ax.add_patch(Rectangle((x0,y0), x1-x0, y1-y0, fc=color, ec="#222", lw=1.2)); ax.text((x0+x1)/2, (y0+y1)/2, name, ha="center", va="center", fontsize=8, weight="bold")
    board(STACK, "", "#cfe3ff"); ax.text(sx0+25.4, sy0+22.86+1.2, "Feather 5477 + Adalogger 2922 + OLED Wing 6313  (stack 50.8 x 22.86, glass top 27.8 above floor)", ha="center", va="bottom", fontsize=7.5, weight="bold")
    board(GPS, "PA1010D GPS\n25.4 x 25.4", "#d9f2d0"); board(IMU, "LSM6DSOX\n17.78 x 25.4\n(2 screws + ledge)", "#f9d9d9"); board(SHT, "SHT41\n17.78 x 25.4", "#efe0ff")
    ax.add_patch(Rectangle(WINDOW[:2], WINDOW[2], WINDOW[3], fc="#222", ec="none", alpha=.85)); ax.text(WINDOW[0]+WINDOW[2]/2, WINDOW[1]+WINDOW[3]/2, "OLED window", color="w", ha="center", va="center", fontsize=8)
    for bx,by in BUTTONS: ax.add_patch(Circle((bx,by), 2.2, fc="#ff6a13", ec="#222"))
    ax.add_patch(Circle(RESET, 1.0, fc="#fff", ec="#222")); ax.text(RESET[0]+2, RESET[1], "rst", fontsize=6, va="center")
    ax.add_patch(Rectangle((GPS_PATCH[0]-5, GPS_PATCH[1]-5), 10, 10, fc="#7cb342", ec="#222")); ax.text(GPS_PATCH[0], GPS_PATCH[1]-8.5, "patch antenna (sky)", ha="center", fontsize=7)
    # connectors
    for b in (GPS, IMU, SHT):
        for yy in (b["y"][0]-0.5, b["y"][1]-4.1): ax.add_patch(Rectangle((b["conn_x"]-3.05, yy), 6.1, 4.6, fc="#ffd54f", ec="#222", lw=.8))
    ax.add_patch(Rectangle((sx0-1.1, USB["y"]-4.5), 8, 9, fc="#bbb", ec="#222")); ax.text(sx0-1.5, USB["y"]-7, "USB-C", fontsize=7, ha="right")
    ax.add_patch(Rectangle((sx0+33.5, sy0+4.3), 15.2, 14.1, fc="none", ec="#222", ls="--")); ax.text(sx0+41, sy0+2, "microSD (card exits ->)", fontsize=6.5, ha="center")
    ax.add_patch(Rectangle((sx0+30.6, sy0+3.7), 20.5, 15.4, fc="none", ec="#1565c0", ls=":")); ax.text(sx0+41, sy0+20.5, "Wi-Fi module keep-out", fontsize=6.5, ha="center", color="#1565c0")
    # cable snake
    pts = snake(); xy = np.array([p for _,p in pts])
    ax.plot(xy[:,0], xy[:,1], color="#e53935", lw=2.5, solid_capstyle="round")
    for lbl,(x,y) in pts:
        if lbl: ax.plot(x,y,"o",color="#e53935",ms=5); ax.annotate(lbl,(x,y),xytext=(4,4),textcoords="offset points",fontsize=7,color="#b71c1c")
    # louvers, openings
    for i in range(5): ax.add_patch(Rectangle((55+i*3.2, -WALL-0.2), 1.4, WALL+0.4, fc="#fff", ec="#222", lw=.6))
    ax.text(63, -WALL-4, "louvers (SHT41 airflow)", ha="center", fontsize=7)
    ax.add_patch(Rectangle((W, SD["y"]-8), WALL, 16, fc="#fff", ec="#222")); ax.text(W+WALL+1, SD["y"], "SD slot", fontsize=7, va="center")
    ax.add_patch(Rectangle((-WALL, USB["y"]-7), WALL, 14, fc="#fff", ec="#222"))
    ax.annotate("", (W, -WALL-9), (0, -WALL-9), arrowprops=dict(arrowstyle="<->")); ax.text(W/2, -WALL-12, f"interior {W:.1f}  /  exterior {W_EXT:.1f}", ha="center", fontsize=8)
    ax.annotate("", (W+WALL+9, D), (W+WALL+9, 0), arrowprops=dict(arrowstyle="<->")); ax.text(W+WALL+11, D/2, f"interior {D:.1f}\nexterior {D_EXT:.1f}", va="center", fontsize=8)
    ax.text(W/2, D+WALL+3, f"TOP VIEW, roof removed. Height: exterior {H_EXT:.1f} (floor {FLOOR}, standoffs {STANDOFF}, stack pins-to-glass 26.8, roof {ROOF}). Cables: 3 x 100 mm (red), all bends >= 8 mm radius.", ha="center", fontsize=8)
    ax.annotate("", (-9, -8), (-9, 18), arrowprops=dict(arrowstyle="->", lw=2.5)); ax.text(-11, 5, "CAR FORWARD\n(case -Y; bar runs along X)", ha="right", va="center", fontsize=8, rotation=90)
    ax.set_xlim(-20, W+22); ax.set_ylim(-16, D+16); ax.axis("off")
    fig.savefig(OUT/"layout_top.png", dpi=170, bbox_inches="tight"); plt.close(fig)

# ---------------- massing models ----------------
def rbox(w, d, h, r_vert=4.0, r_top=1.2):
    b = cq.Workplane("XY").box(w, d, h, centered=(False, False, False)).edges("|Z").fillet(r_vert)
    if r_top: b = b.faces(">Z").edges().fillet(r_top)
    return b

def common_cuts(body, z_top, tilt=0.0):
    """Window, buttons, GPS mark, louvers, USB, SD on a body whose exterior origin is (-WALL,-WALL,-FLOOR)."""
    wx, wy, ww, wh = WINDOW
    body = body.cut(cq.Workplane("XY").box(ww+1.2, wh+1.2, 10, centered=(False,False,False)).translate((wx-0.6, wy-0.6, z_top-ROOF-0.01)))
    for bx,by in BUTTONS: body = body.cut(cq.Workplane("XY").circle(2.6).extrude(10).translate((bx,by,z_top-ROOF-0.01)))
    body = body.cut(cq.Workplane("XY").circle(0.9).extrude(10).translate((RESET[0],RESET[1],z_top-ROOF-0.01)))
    body = body.cut(cq.Workplane("XY").rect(22,22).extrude(0.6).translate((GPS_PATCH[0],GPS_PATCH[1],z_top-0.6)))  # GPS mark, shallow recess
    for i in range(5): body = body.cut(cq.Workplane("XY").box(1.4, WALL+2, 12, centered=(False,False,False)).translate((55+i*3.2, -WALL-1, 6)))
    body = body.cut(cq.Workplane("XY").box(WALL+2, 14, 9, centered=(False,False,False)).translate((-WALL-1, USB["y"]-7, USB["z"]-4.5)))
    body = body.cut(cq.Workplane("XY").box(WALL+2, 16, 3, centered=(False,False,False)).translate((W-1, SD["y"]-8, SD["z"]-1.5)))
    return body

def saddle_and_tube(z_bottom, along="x"):
    """Cradle under the box + roll bar tube, tube axis along case X (across the car)."""
    L = 56; Wd = 44; Hs = 14
    cx, cy = W/2, D/2
    s = cq.Workplane("XY").box(L, Wd, Hs, centered=(True,True,False)).translate((cx, cy, z_bottom-Hs)).edges("|Z").fillet(3)
    tube = cq.Workplane("YZ").circle(TUBE_D/2).extrude(160).translate((cx-80, cy, z_bottom-Hs-TUBE_D/2+5))
    s = s.cut(tube)
    for dx in (-18, 18):  # strap slots
        s = s.cut(cq.Workplane("XY").box(4, Wd+4, 3, centered=(True,True,False)).translate((cx+dx, cy, z_bottom-Hs+1)))
    return s, tube

def concept_a():
    """A. Slab: tray + top lid, screws visible on top."""
    body = rbox(W_EXT, D_EXT, H_EXT).translate((-WALL,-WALL,-FLOOR))
    body = common_cuts(body, H_EXT-FLOOR)
    body = body.cut(cq.Workplane("XY").box(W_EXT+2, D_EXT+2, 0.6, centered=(False,False,False)).translate((-WALL-1,-WALL-1,H_EXT-FLOOR-ROOF-2.5)))  # lid seam
    screws=[]
    for (x,y) in ((2.5,2.5),(W-2.5,2.5),(2.5,D-2.5),(W-2.5,D-2.5)):
        body = body.cut(cq.Workplane("XY").circle(2.3).extrude(1.5).translate((x,y,H_EXT-FLOOR-1.5)))
        screws.append(cq.Workplane("XY").circle(2.2).extrude(1.2).translate((x,y,H_EXT-FLOOR-1.4)))
    sad, tube = saddle_and_tube(-FLOOR)
    return dict(body=body, accents=[sad]+[cq.Workplane("XY").circle(2.2).extrude(1.6).translate((bx,by,H_EXT-FLOOR-1.2)) for bx,by in BUTTONS], screws=screws, tube=tube, window=cq.Workplane("XY").box(WINDOW[2],WINDOW[3],0.8,centered=(False,False,False)).translate((WINDOW[0],WINDOW[1],H_EXT-FLOOR-1.0)))

def concept_b():
    """B. Shell + sled: seamless wrap-around shell printed upside down, sled plate screwed from below."""
    body = rbox(W_EXT, D_EXT, H_EXT, r_vert=5.0, r_top=2.5).translate((-WALL,-WALL,-FLOOR))
    body = common_cuts(body, H_EXT-FLOOR)
    body = body.cut(cq.Workplane("XY").box(W_EXT+2, D_EXT+2, 0.6, centered=(False,False,False)).translate((-WALL-1,-WALL-1,-FLOOR+FLOOR)))  # sled seam at the very bottom
    sad, tube = saddle_and_tube(-FLOOR)
    caps=[cq.Workplane("XY").circle(2.2).extrude(1.6).translate((bx,by,H_EXT-FLOOR-1.2)) for bx,by in BUTTONS]
    return dict(body=body, accents=[sad]+caps, screws=[], tube=tube, window=cq.Workplane("XY").box(WINDOW[2],WINDOW[3],0.8,centered=(False,False,False)).translate((WINDOW[0],WINDOW[1],H_EXT-FLOOR-1.0)))

def concept_c():
    """C. Wedge: shell + sled, roof sloped 10 deg toward the front, visor lip over the OLED."""
    ang = 10.0; extra = math.tan(math.radians(ang))*D_EXT
    Hb = H_EXT + extra
    body = rbox(W_EXT, D_EXT, Hb, r_vert=5.0, r_top=0).translate((-WALL,-WALL,-FLOOR))
    cutter = cq.Workplane("XY").box(W_EXT+20, D_EXT*2, 40, centered=(False,False,False)).translate((-WALL-10, -WALL, H_EXT-FLOOR)).rotate((0,-WALL,H_EXT-FLOOR),(1,-WALL,H_EXT-FLOOR), ang)
    body = body.cut(cutter)
    try: body = body.faces(">Z").edges().fillet(2.0)
    except Exception: pass
    # window and buttons cut normal to the sloped roof
    def z_at(y): return H_EXT-FLOOR + math.tan(math.radians(ang))*(y+WALL)
    wx, wy, ww, wh = WINDOW
    win = cq.Workplane("XY").box(ww+1.2, wh+1.2, 14, centered=(False,False,False)).translate((wx-0.6, wy-0.6, z_at(wy)-ROOF-2))
    body = body.cut(win)
    for bx,by in BUTTONS: body = body.cut(cq.Workplane("XY").circle(2.6).extrude(14).translate((bx,by,z_at(by)-ROOF-2)))
    body = body.cut(cq.Workplane("XY").rect(22,22).extrude(0.6).translate((GPS_PATCH[0],GPS_PATCH[1],z_at(GPS_PATCH[1])-0.6)).rotate((0,GPS_PATCH[1],z_at(GPS_PATCH[1])),(1,GPS_PATCH[1],z_at(GPS_PATCH[1])),ang))
    for i in range(5): body = body.cut(cq.Workplane("XY").box(1.4, WALL+2, 12, centered=(False,False,False)).translate((55+i*3.2, -WALL-1, 6)))
    body = body.cut(cq.Workplane("XY").box(WALL+2, 14, 9, centered=(False,False,False)).translate((-WALL-1, USB["y"]-7, USB["z"]-4.5)))
    body = body.cut(cq.Workplane("XY").box(WALL+2, 16, 3, centered=(False,False,False)).translate((W-1, SD["y"]-8, SD["z"]-1.5)))
    body = body.cut(cq.Workplane("XY").box(W_EXT+2, D_EXT+2, 0.6, centered=(False,False,False)).translate((-WALL-1,-WALL-1,0)))
    sad, tube = saddle_and_tube(-FLOOR)
    caps=[cq.Workplane("XY").circle(2.2).extrude(1.6).translate((bx,by,z_at(by)-1.2)) for bx,by in BUTTONS]
    window = cq.Workplane("XY").box(ww,wh,0.8,centered=(False,False,False)).translate((wx,wy,z_at(wy+wh/2)-1.0)).rotate((0,wy+wh/2,z_at(wy+wh/2)),(1,wy+wh/2,z_at(wy+wh/2)), ang)
    return dict(body=body, accents=[sad]+caps, screws=[], tube=tube, window=window)

def mesh(shape):
    verts, faces = shape.val().tessellate(0.05, 0.15)
    v = np.array([(p.x,p.y,p.z) for p in verts]); f = np.hstack([[3,*t] for t in faces])
    return pv.PolyData(v, f).compute_normals(auto_orient_normals=True)

def render(parts, name, views):
    for vname, pos in views.items():
        pl = pv.Plotter(off_screen=True, window_size=(1400, 1000)); pl.set_background("#f2f2f0")
        pl.add_mesh(mesh(parts["body"]), color="#2f3136", smooth_shading=True, specular=0.25, specular_power=20)
        for a in parts["accents"]: pl.add_mesh(mesh(a), color="#ff6a13", smooth_shading=True)
        for s in parts["screws"]: pl.add_mesh(mesh(s), color="#b0b3b8", smooth_shading=True, specular=0.6)
        pl.add_mesh(mesh(parts["window"]), color="#0b0c0e", smooth_shading=True, specular=0.9, specular_power=60)
        pl.add_mesh(mesh(parts["tube"]), color="#9a9da3", smooth_shading=True, specular=0.4)
        pl.enable_eye_dome_lighting() if False else None
        c = np.array([W/2, D/2, 8]); pl.camera_position = [tuple(c + np.array(pos)*220), tuple(c), (0,0,1)]
        pl.camera.zoom(1.35 if vname!="top" else 1.2)
        pl.add_light(pv.Light(position=(200, -250, 400), intensity=0.9)); pl.add_light(pv.Light(position=(-300, 200, 250), intensity=0.5))
        pl.screenshot(str(OUT/f"{name}_{vname}.png")); pl.close()

if __name__ == "__main__":
    layout_png(); print("layout_top.png")
    views = {"iso": (0.9, -1.0, 0.75), "front": (0.15, -1.0, 0.35)}
    for fn, name in ((concept_a,"A_slab"), (concept_b,"B_shell_sled"), (concept_c,"C_wedge")):
        parts = fn(); render(parts, name, views); print(name, "rendered")
