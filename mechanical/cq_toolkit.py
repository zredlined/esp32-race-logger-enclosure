"""Reusable CadQuery helpers and the envelope-based clearance checker.

Import next to your generate.py:
    from cq_toolkit import *
All dimensions in millimetres. Coordinates: x right, y forward, z up, origin at
the lower-left corner of the base plate.
"""
from math import sqrt
from pathlib import Path

import cadquery as cq
from cadquery import exporters


# ---------------------------------------------------------------- primitives
def rounded_plate(w, l, t, r):
    """Plate with vertical-edge fillets, lower-left corner at the origin."""
    return cq.Workplane("XY").box(w, l, t).translate((w / 2, l / 2, t / 2)).edges("|Z").fillet(r)


def boss(x, y, z0, h, od, fillet=1.5, chamfer=0.45):
    """Standoff with a quarter-round root fillet and a lead-in chamfer, as a revolved profile."""
    r, f = od / 2, min(fillet, h / 3)
    prof = (cq.Workplane("XZ").moveTo(0, 0).lineTo(r + f, 0)
            .threePointArc((r + f - f * 0.7071, f - f * 0.7071), (r, f))
            .lineTo(r, h - chamfer).lineTo(r - chamfer, h).lineTo(0, h).close())
    return prof.revolve(360, (0, 0, 0), (0, 1, 0)).translate((x, y, z0))


def insert_bore(x, y, top_z, depth=4.5, top_d=3.8, bottom_d=3.4, from_below=False):
    """Tapered heat-set pocket. from_below=True opens on the bed face at z=top_z and rises."""
    if from_below:
        return cq.Solid.makeCone(top_d / 2, bottom_d / 2, depth + 0.02, cq.Vector(x, y, top_z - 0.01), cq.Vector(0, 0, 1))
    return cq.Solid.makeCone(bottom_d / 2, top_d / 2, depth + 0.02, cq.Vector(x, y, top_z - depth), cq.Vector(0, 0, 1))


def cyl(x, y, z0, h, d):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(d / 2).extrude(h)


def slot(x, y, z0, t, length, width, angle=0):
    """Through slot; length is end to end including rounded ends."""
    return cq.Workplane("XY").workplane(offset=z0 - 0.1).center(x, y).slot2D(length, width, angle).extrude(t + 0.2)


def countersunk_hole(part, x, y, t, clear_d=2.9, head_d=5.3, head_depth=1.2):
    return part.cut(cyl(x, y, -0.1, t + 0.2, clear_d)).cut(cyl(x, y, t - head_depth, head_depth + 0.1, head_d))


def box(origin, size):
    return cq.Workplane("XY").box(*size).translate(tuple(origin[i] + size[i] / 2 for i in range(3)))


def shell_box(w, l, h, wall=2.4, r=4.5, floor=3.0):
    """Open-top tray with filleted vertical edges."""
    outer = rounded_plate(w, l, h, r)
    inner = rounded_plate(w - 2 * wall, l - 2 * wall, h, max(r - wall, 0.5)).translate((wall, wall, floor))
    return outer.cut(inner)


def perimeter_lip(w, l, t, lip_h, lip_t=2.0, r=4.5):
    """Ring to union onto a plate of thickness t; returns the ring positioned at z=t."""
    ring = rounded_plate(w, l, lip_h, r).cut(
        rounded_plate(w - 2 * lip_t, l - 2 * lip_t, lip_h + 0.2, max(r - lip_t, 0.5)).translate((lip_t, lip_t, -0.1)))
    return ring.translate((0, 0, t))


def louvers(x, y, n, length, pitch, width, z0, t, angle=0):
    """n parallel slots centred on (x, y); returns a cutting solid."""
    cut = None
    for i in range(n):
        off = (i - (n - 1) / 2) * pitch
        c = slot(x, y + off, z0, t, length, width, angle) if angle == 0 else slot(x + off, y, z0, t, length, width, angle)
        cut = c if cut is None else cut.union(c)
    return cut


def raised_text(text, x, y, z, size=2.4, h=0.55):
    return cq.Workplane("XY").workplane(offset=z).center(x, y).text(text, size, h, halign="center", valign="center")


# ---------------------------------------------------------------- envelopes
class Env:
    """Axis-aligned envelope for clearance checks and assembly display."""

    def __init__(self, name, lo, hi, kind, owner=None):
        self.name, self.kind, self.owner = name, kind, owner
        self.lo = tuple(min(lo[i], hi[i]) for i in range(3))
        self.hi = tuple(max(lo[i], hi[i]) for i in range(3))

    def overlaps(self, o, eps=0.05):
        return all(self.lo[i] < o.hi[i] - eps and o.lo[i] < self.hi[i] - eps for i in range(3))

    def size(self):
        return tuple(self.hi[i] - self.lo[i] for i in range(3))

    def centre_xy(self):
        return (self.lo[0] + self.hi[0]) / 2, (self.lo[1] + self.hi[1]) / 2

    def plan(self, z0, z1):
        return Env(self.name, (self.lo[0], self.lo[1], z0), (self.hi[0], self.hi[1], z1), self.kind)

    def solid(self):
        return box(self.lo, self.size()).val()


SIDE_PLUG = dict(start=2.7, reach=12.7, width=6.6, z=(-0.3, 5.0))   # JST SH side entry, from connector centre
TOP_PLUG = dict(x=3.0, y=6.0, height=4.3, plug_h=4.5, bend=5.0)     # JST SH top entry


def side_connector_envs(name, centre, facing, used, owner, pcb_top, depth=4.25, width=6.1, height=4.3):
    """Connector body plus, if used, its plug keep-out."""
    cx, cy = centre
    dx, dy = facing
    ex, ey = (depth / 2, width / 2) if dx else (width / 2, depth / 2)
    envs = [Env(f"conn {name}", (cx - ex, cy - ey, pcb_top), (cx + ex, cy + ey, pcb_top + height), "conn", owner)]
    if used:
        sx, sy = cx + dx * SIDE_PLUG["start"], cy + dy * SIDE_PLUG["start"]
        px, py = cx + dx * SIDE_PLUG["reach"], cy + dy * SIDE_PLUG["reach"]
        hw = SIDE_PLUG["width"] / 2
        lo = (min(sx, px) if dx else cx - hw, min(sy, py) if dy else cy - hw, pcb_top + SIDE_PLUG["z"][0])
        hi = (max(sx, px) if dx else cx + hw, max(sy, py) if dy else cy + hw, pcb_top + SIDE_PLUG["z"][1])
        envs.append(Env(f"plug {name}", lo, hi, "plug", owner))
    return envs


def add_route(E, name, pts, owner, z_deck, z_plug_bottom, pad=2.75, hug=10.0, z_lo_first=None):
    """Cable polyline as per-segment boxes: runs hug the deck underside, final approach descends."""
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        last = i == len(pts) - 2
        zlo = z_plug_bottom if last else z_deck - hug
        if i == 0 and z_lo_first is not None:
            zlo = min(zlo, z_lo_first)
        E.append(Env(f"{name} seg{i + 1}", (min(x0, x1) - pad, min(y0, y1) - pad, zlo), (max(x0, x1) + pad, max(y0, y1) + pad, z_deck), "cable", owner))


def polyline_length(pts):
    return sum(sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) for a, b in zip(pts, pts[1:]))


def head_hits(x, y, env, head_d=5.3, z0=None, z1=None):
    """Countersunk screw head at (x, y) vs a round boss (circle test) or a slot (box test)."""
    if env.kind == "boss":
        cx, cy = env.centre_xy()
        r = env.size()[0] / 2
        return sqrt((x - cx) ** 2 + (y - cy) ** 2) < r + head_d / 2
    if env.kind == "slot":
        head = Env("h", (x - head_d / 2, y - head_d / 2, z0), (x + head_d / 2, y + head_d / 2, z1), "t")
        return head.overlaps(env.plan(z0, z1))
    return False


def clearance_report(E, screw_heads=(), deck_z=None, deck_top=None, skip_pairs=()):
    """Return (problems, notes).

    E: list of Env. screw_heads: iterable of (x, y, label) for countersunk heads in the deck top.
    skip_pairs: iterable of (mover_kind, solid_name_substring) to ignore, e.g. ("cable", "hub").
    """
    problems, notes = [], []
    solids = [e for e in E if e.kind in ("pcb", "conn", "boss", "lip", "wall", "part", "metro", "tower", "carrier")]
    movers = [e for e in E if e.kind in ("plug", "cable")]
    for m in movers:
        for s in solids:
            if s.name == m.owner or any(m.kind == mk and sub in s.name for mk, sub in skip_pairs):
                continue
            if m.overlaps(s):
                problems.append(f"{m.name}  hits  {s.name}")
        for q in movers:
            if q is not m and m.kind == "plug" and q.kind == "plug" and m.name < q.name and m.overlaps(q):
                problems.append(f"{m.name}  hits  {q.name}")
    if deck_z is not None:
        for sl in (e for e in E if e.kind == "slot"):
            for s in solids:
                if s.kind in ("boss", "carrier") or (s.kind == "pcb" and s.lo[2] >= deck_z):
                    if sl.overlaps(s.plan(deck_z, deck_top)):
                        problems.append(f"{sl.name}  overlaps  {s.name} (plan view)")
        for x, y, label in screw_heads:
            for s in E:
                if head_hits(x, y, s, z0=deck_z, z1=deck_top):
                    problems.append(f"screw head {label} at {x:.1f},{y:.1f}  overlaps  {s.name}")
    for h in (e for e in E if e.kind == "carrier" or (e.kind == "pcb" and "hub" in e.name.lower())):
        for s in (e for e in E if e.kind == "metro"):
            if h.overlaps(s):
                problems.append(f"{h.name}  hits  {s.name}")
    return problems, notes


# ---------------------------------------------------------------- export
def export_part(part, name, out_dir, expected_bbox=None, tol=0.08, ang=0.2):
    """STL + STEP with a validity gate. expected_bbox=(w, l, h) flags flares poking past the plate."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    val = part.val()
    if not val.isValid() or part.solids().size() != 1:
        raise RuntimeError(f"{name}: valid={val.isValid()} solids={part.solids().size()}")
    bb = val.BoundingBox()
    if expected_bbox and any(abs(got - want) > 0.05 for got, want in zip((bb.xlen, bb.ylen, bb.zlen), expected_bbox) if want is not None):
        raise RuntimeError(f"{name}: bbox {bb.xlen:.2f} x {bb.ylen:.2f} x {bb.zlen:.2f} differs from expected {expected_bbox}")
    exporters.export(part, str(out / f"{name}.stl"), tolerance=tol, angularTolerance=ang)
    exporters.export(part, str(out / f"{name}.step"))
    print(f"   {name}: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, valid")
    return bb


def through_hole_check(part, points, z_samples):
    """Assert the part is hollow at each (x, y) for every z sample (catches bosses closing holes)."""
    val = part.val()
    bad = [(x, y, z) for x, y in points for z in z_samples if val.isInside(cq.Vector(x, y, z))]
    if bad:
        raise RuntimeError("through holes blocked at: " + ", ".join(f"({x:.1f},{y:.1f},z{z:.1f})" for x, y, z in bad))
