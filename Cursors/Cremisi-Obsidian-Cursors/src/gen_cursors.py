#!/usr/bin/env python3
"""Generate the Cremisi Obsidian XCursor theme: spearheads, lances, blades
and a rose window, in crypt stone, bone and blood.

Usage: gen_cursors.py <theme-dir>
Needs rsvg-convert (librsvg) and xcursorgen (xorg-xcursorgen).
"""
import math
import os
import shutil
import subprocess
import sys
import tempfile

# Cremisi Obsidian palette
BLOOD = "#e2586a"
CRYPT = "#17171c"
BONE = "#e9e1d1"
INK = "#0f0f13"

BOX = 32                       # design grid; rendered at every size below
SIZES = (24, 32, 48, 64, 96)
HALO = 2                       # dark outline (half of it shows outside)


# ---------------------------------------------------------------- geometry

def f(n):
    s = f"{n:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def poly(pts):
    return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"


def diamond(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    return [(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)]


def rot(pts, deg, cx=0.0, cy=0.0):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def move(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


def mirror_x(pts, axis=BOX / 2):
    return [(2 * axis - x, y) for x, y in pts][::-1]


def inset(pts, d):
    """Shrink a convex polygon by d (offset every edge towards the centre)."""
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    lines = []
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        l = math.hypot(x1 - x0, y1 - y0)
        nx, ny = (y1 - y0) / l, -(x1 - x0) / l
        if nx * (cx - x0) + ny * (cy - y0) < 0:
            nx, ny = -nx, -ny
        lines.append(((x0 + nx * d, y0 + ny * d), (x1 - x0, y1 - y0)))
    out = []
    for i in range(n):
        (p, r), (q, s) = lines[i - 1], lines[i]
        den = r[0] * s[1] - r[1] * s[0]
        t = ((q[0] - p[0]) * s[1] - (q[1] - p[1]) * s[0]) / den
        out.append((p[0] + r[0] * t, p[1] + r[1] * t))
    return out


def blade(points, hw, tip=None):
    """Polyline stroked with half-width hw, miter joins, pointed ends."""
    tip = hw * 2.2 if tip is None else tip
    n = len(points)
    dirs = []
    for i in range(n - 1):
        (x0, y0), (x1, y1) = points[i], points[i + 1]
        l = math.hypot(x1 - x0, y1 - y0)
        dirs.append(((x1 - x0) / l, (y1 - y0) / l))

    def offset(side):
        out = []
        for i, (x, y) in enumerate(points):
            if i in (0, n - 1):
                tx, ty = dirs[0] if i == 0 else dirs[-1]
                out.append((x - ty * hw * side, y + tx * hw * side))
            else:
                (ax, ay), (bx, by) = dirs[i - 1], dirs[i]
                mx, my = -(ay + by), ax + bx
                ml = math.hypot(mx, my)
                mx, my = mx / ml, my / ml
                cos = mx * -ay + my * ax
                out.append((x + mx * hw * side / cos, y + my * hw * side / cos))
        return out

    left, right = offset(1), offset(-1)
    (sx, sy), (ex, ey) = points[0], points[-1]
    start = (sx - dirs[0][0] * tip, sy - dirs[0][1] * tip)
    end = (ex + dirs[-1][0] * tip, ey + dirs[-1][1] * tip)
    return [start] + left + [end] + right[::-1]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# The spearhead of scale-horz-marks-after-slider.svg: tip, shoulders at 7/12
# of the length, half-width a little under a third of the length.
def spear(length, tip=(0.0, 0.0), angle=0.0):
    w, sh = length * 0.305, length * 0.583
    pts = [(0, 0), (w, sh), (0, length), (-w, sh)]
    return move(rot(pts, angle), *tip)


def spear_pip(length, tip=(0.0, 0.0), angle=0.0, k=1.0):
    pts = diamond(0, length * 0.583, length * 0.08 * k, length * 0.11 * k)
    return move(rot(pts, angle), *tip)


# ----------------------------------------------------------------- drawing

class Glyph:
    """Layers drawn in order; every shape added with halo=True also gets a
    dark outline, and all outlines sit below all fills."""

    def __init__(self):
        self.halos, self.fills, self.raw = [], [], []

    def add(self, pts, fill, halo=True, **attrs):
        d = pts if isinstance(pts, str) else poly(pts)
        if halo:
            self.halos.append(d)
        self.fills.append((d, fill, attrs))
        return self

    def plate(self, pts, outer=BLOOD, inner=CRYPT, rim=1.5):
        """A shape with a coloured rim and a stone core."""
        self.add(pts, outer)
        return self.add(inset(pts, rim), inner, halo=False)

    def text(self, svg):
        self.raw.append(svg)
        return self

    def svg(self):
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{BOX}" height="{BOX}" '
               f'viewBox="0 0 {BOX} {BOX}">',
               '<defs><filter id="s" x="-20%" y="-20%" width="140%" height="140%">'
               '<feGaussianBlur in="SourceAlpha" stdDeviation="0.9"/>'
               '<feOffset dx="0.6" dy="1.1"/>'
               '<feComponentTransfer><feFuncA type="linear" slope="0.4"/></feComponentTransfer>'
               '<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>'
               '</filter></defs><g filter="url(#s)">']
        for d in self.halos:
            out.append(f'<path d="{d}" fill="{INK}" stroke="{INK}" stroke-width="{HALO}" '
                       f'stroke-linejoin="round" opacity="0.9"/>')
        for d, fill, attrs in self.fills:
            a = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items())
            out.append(f'<path d="{d}" fill="{fill}"{a}/>')
        out += self.raw
        out.append("</g></svg>")
        return "\n".join(out)


# ----------------------------------------------------------------- cursors

ARROW_LEN, ARROW_TILT, ARROW_TIP = 24, -28, (3.5, 2.5)


def arrow(g=None, tip=ARROW_TIP, angle=ARROW_TILT, length=ARROW_LEN):
    g = g or Glyph()
    g.plate(spear(length, tip, angle), rim=length * 0.09)
    return g.add(spear_pip(length, tip, angle, k=1.25), BLOOD, halo=False)


def badge(g, glyph):
    """Small blood diamond at the lower right carrying a sign."""
    g.add(diamond(24, 24, 7, 7), BLOOD)
    return glyph(g)


def rose(g, cx, cy, r, frame, frames):
    """Rose window: a ring of eight petals, one of them lit, with a trail."""
    g.add([(cx + r * math.cos(t), cy + r * math.sin(t))
           for t in (i * math.pi / 24 for i in range(48))], CRYPT)
    ring = [(cx + (r - 0.9) * math.cos(t), cy + (r - 0.9) * math.sin(t))
            for t in (i * math.pi / 24 for i in range(48))]
    g.add(poly(ring), "none", halo=False, stroke=BLOOD, stroke_width=f(r * 0.11))
    head = frame * 8 / frames
    for i in range(8):
        lag = (head - i) % 8
        a = i * 45 - 90
        petal = rot([(cx, cy - r * 0.28), (cx + r * 0.17, cy - r * 0.55),
                     (cx, cy - r * 0.84), (cx - r * 0.17, cy - r * 0.55)], a + 90, cx, cy)
        if lag < 1:
            g.add(petal, BLOOD, halo=False)
        elif lag < 4:
            g.add(petal, BLOOD, halo=False, fill_opacity=f(0.85 - lag * 0.18))
        else:
            g.add(petal, BONE, halo=False, fill_opacity="0.16")
    return g.add(diamond(cx, cy, r * 0.13, r * 0.13), BONE, halo=False)


def double_lance(angle, bars=False):
    """Resize: a shaft with a spearhead at both ends and a pip in the middle."""
    g = Glyph()
    head = [(2, 16), (8.6, 11.4), (11.2, 16), (8.6, 20.6)]
    parts = [head, mirror_x(head), rect(9.5, 14.9, 22.5, 17.1)]
    if bars:
        parts = [head, mirror_x(head), rect(9.5, 15.1, 12.4, 16.9), rect(19.6, 15.1, 22.5, 16.9)]
    for p in parts:
        g.add(rot(p, angle, 16, 16), BLOOD)
    for p in parts[:2]:
        g.add(rot(inset(p, 1.5), angle, 16, 16), CRYPT, halo=False)
    if bars:
        for x in (14.2, 17.8):
            g.add(rot(blade([(x, 8), (x, 24)], 0.95, 1.6), angle, 16, 16), BONE)
    else:
        g.add(rot(diamond(16, 16, 1.5, 1.5), angle, 16, 16), CRYPT, halo=False)
    return g


def edge_lance(angle, corner=False):
    """Resize towards one edge (or corner): lance aimed at a bone rampart."""
    g = Glyph()
    if corner:  # canonical: towards the top-left corner
        rampart = blade([(4, 15), (4, 4), (15, 4)], 1.0, 1.6)
        parts = [rot([(0, 0), (4.6, 6.6), (0, 9.8), (-4.6, 6.6)], -45),
                 rot(rect(-1.1, 9, 1.1, 21), -45)]
        parts = [move(p, 8, 8) for p in parts]
        pommel = move(rot(diamond(0, 22.5, 1.8, 2.4), -45), 8, 8)
    else:       # canonical: towards the top edge
        rampart = blade([(7, 3.5), (25, 3.5)], 1.0, 1.6)
        parts = [[(16, 7), (20.6, 13.6), (16, 16.8), (11.4, 13.6)], rect(14.9, 16, 17.1, 27)]
        pommel = diamond(16, 28.5, 1.8, 2.4)
    g.add(rot(rampart, angle, 16, 16), BONE)
    for p in parts + [pommel]:
        g.add(rot(p, angle, 16, 16), BLOOD)
    g.add(rot(inset(parts[0], 1.5), angle, 16, 16), CRYPT, halo=False)
    return g


def build():
    cur = {}  # name -> (frames, hotspot, delay)

    def static(name, g, hot):
        cur[name] = ([g.svg()], hot, 0)

    tip = ARROW_TIP
    static("default", arrow(), tip)

    # pointer: an upright crimson lance with a bone crossguard
    g = Glyph()
    head = [(16, 2), (21.2, 10.8), (16, 16.6), (10.8, 10.8)]
    g.add(rect(14.9, 16, 17.1, 26.5), BONE)
    g.add(blade([(9.6, 18), (22.4, 18)], 1.25, 2.2), BONE)
    g.add(diamond(16, 28.2, 2.1, 2.6), BLOOD)
    g.add(head, BLOOD)
    g.add(inset(head, 1.6), "none", halo=False, stroke=INK, stroke_opacity="0.35",
          stroke_width="0.8", stroke_linejoin="miter")
    g.add(diamond(16, 10.8, 1.5, 2.1), CRYPT, halo=False)
    static("pointer", g, (16, 2))

    # text: bone I-beam with blade serifs and a blood caret
    g = Glyph()
    g.add(rect(15.1, 6.5, 16.9, 25.5), BONE)
    g.add(blade([(12, 6), (20, 6)], 1.0, 1.8), BONE)
    g.add(blade([(12, 26), (20, 26)], 1.0, 1.8), BONE)
    g.add(diamond(16, 16, 1.9, 2.8), BLOOD, halo=False)
    static("text", g, (16, 16))
    vt = Glyph()
    for d, fill, a in g.fills:
        vt.fills.append((poly(rot(_pts(d), 90, 16, 16)), fill, a))
    vt.halos = [poly(rot(_pts(d), 90, 16, 16)) for d in g.halos]
    static("vertical-text", vt, (16, 16))

    # wait / progress: rose window turning
    frames = 16
    cur["wait"] = ([rose(Glyph(), 16, 16, 13, i, frames).svg() for i in range(frames)], (16, 16), 55)
    cur["progress"] = ([rose(arrow(), 24.5, 24.5, 6.6, i, frames).svg() for i in range(frames)],
                       tip, 55)

    # arrow + badge family
    q = ('<text x="24" y="27.4" font-family="serif" font-weight="bold" font-size="10.5" '
         f'text-anchor="middle" fill="{INK}">?</text>')
    static("help", badge(arrow(), lambda g: g.text(q)), tip)
    static("copy", badge(arrow(), lambda g: g.add(blade([(20.6, 24), (27.4, 24)], 0.75, 1.1), INK, halo=False)
                         .add(blade([(24, 20.6), (24, 27.4)], 0.75, 1.1), INK, halo=False)), tip)
    static("alias", badge(arrow(), lambda g: g
                          .add(poly(diamond(22.4, 24, 2.6, 2.6)) + " " + poly(diamond(22.4, 24, 1.5, 1.5)),
                               INK, halo=False, fill_rule="evenodd")
                          .add(poly(diamond(25.6, 24, 2.6, 2.6)) + " " + poly(diamond(25.6, 24, 1.5, 1.5)),
                               INK, halo=False, fill_rule="evenodd")), tip)
    static("context-menu", badge(arrow(), lambda g: [
        g.add(blade([(21.2, y), (26.8, y)], 0.55, 0.8), INK, halo=False) for y in (22, 24, 26)][0]), tip)

    def no_entry(g, cx, cy, r):
        g.plate(diamond(cx, cy, r, r), rim=r * 0.2)
        return g.add(blade([(cx - r * 0.62, cy), (cx + r * 0.62, cy)], r * 0.13, r * 0.2), BLOOD, halo=False)

    static("not-allowed", no_entry(Glyph(), 16, 16, 13), (16, 16))
    static("no-drop", no_entry(arrow(), 24, 24, 7.2), tip)

    # crosshair: four bone blades around a blood diamond
    g = Glyph()
    for a in (0, 90, 180, 270):
        g.add(rot(blade([(16, 2.5), (16, 11.5)], 0.95, 1.6), a, 16, 16), BONE)
    g.add(poly(diamond(16, 16, 2.6, 2.6)) + " " + poly(diamond(16, 16, 1.4, 1.4)),
          BLOOD, fill_rule="evenodd")
    static("crosshair", g, (16, 16))
    g = Glyph()
    for a in (0, 90):
        g.add(rot(rect(13.6, 4, 18.4, 28), a, 16, 16), BLOOD)
    g.add(diamond(16, 16, 2.2, 2.2), CRYPT, halo=False)
    static("cell", g, (16, 16))
    g = Glyph()
    for a in (45, -45):
        g.add(rot(blade([(16, 4), (16, 28)], 1.6, 2.4), a, 16, 16), BLOOD)
    static("X_cursor", g, (16, 16))

    # move: four spearheads round a blood heart
    g = Glyph()
    for a in (0, 90, 180, 270):
        g.plate(rot([(16, 1.5), (20.4, 8.4), (16, 11.2), (11.6, 8.4)], a, 16, 16), rim=1.4)
    g.add(diamond(16, 16, 2.8, 2.8), BLOOD)
    static("move", g, (16, 16))

    # grab / grabbing: four bone claws open, then clutching a blood diamond
    def claws(r, inner):
        g = Glyph()
        for a in (0, 90, 180, 270):
            g.add(rot(blade([(16 - 4.2, 16 - r + 4.2), (16, 16 - r), (16 + 4.2, 16 - r + 4.2)], 1.05, 1.5),
                      a, 16, 16), BONE)
        g.add(diamond(16, 16, inner, inner), BLOOD)
        return g
    static("grab", claws(13, 1.8), (16, 16))
    static("grabbing", claws(9.8, 4.4), (16, 16))

    # zoom: a diamond lens with a bone handle
    def lens(sign):
        g = Glyph()
        g.add(blade([(19.6, 19.6), (27.6, 27.6)], 1.7, 2.2), BONE)
        g.plate(diamond(13, 13, 10.5, 10.5), rim=2)
        g.add(blade([(9.2, 13), (16.8, 13)], 0.85, 1.2), BONE, halo=False)
        if sign == "+":
            g.add(blade([(13, 9.2), (13, 16.8)], 0.85, 1.2), BONE, halo=False)
        return g
    static("zoom-in", lens("+"), (13, 13))
    static("zoom-out", lens("-"), (13, 13))

    # pencil: a bone nib with a slit and a blood breather hole
    g = Glyph()
    nib = rot([(0, 0), (3.8, 9), (2.8, 26), (-2.8, 26), (-3.8, 9)], 225, 0, 0)
    nib = move(nib, 4, 28)
    g.add(nib, BONE)
    g.add(move(rot(blade([(0, 1.5), (0, 9)], 0.35, 0.4), 225), 4, 28), INK, halo=False)
    g.add(move(rot(diamond(0, 10.5, 1.3, 1.8), 225), 4, 28), BLOOD, halo=False)
    static("pencil", g, (4, 28))

    # arrows in other directions
    static("center_ptr", arrow(tip=(16, 3), angle=0), (16, 3))
    m = Glyph()
    a = arrow()
    m.halos = [poly(mirror_x(_pts(d))) for d in a.halos]
    m.fills = [(poly(mirror_x(_pts(d))), fill, at) for d, fill, at in a.fills]
    static("right_ptr", m, (BOX - tip[0], tip[1]))
    for name, ang, hot in (("up-arrow", 0, (16, 4)), ("right-arrow", 90, (28, 16)),
                           ("down-arrow", 180, (16, 28)), ("left-arrow", 270, (4, 16))):
        static(name, arrow(tip=rot([(16, 4)], ang, 16, 16)[0], angle=ang, length=22), hot)

    # resize
    static("ew-resize", double_lance(0), (16, 16))
    static("ns-resize", double_lance(90), (16, 16))
    static("nwse-resize", double_lance(45), (16, 16))
    static("nesw-resize", double_lance(-45), (16, 16))
    static("col-resize", double_lance(0, bars=True), (16, 16))
    static("row-resize", double_lance(90, bars=True), (16, 16))
    for name, ang in (("n-resize", 0), ("e-resize", 90), ("s-resize", 180), ("w-resize", 270)):
        static(name, edge_lance(ang), rot([(16, 3.5)], ang, 16, 16)[0])
    for name, ang in (("nw-resize", 0), ("ne-resize", 90), ("se-resize", 180), ("sw-resize", 270)):
        static(name, edge_lance(ang, corner=True), rot([(4, 4)], ang, 16, 16)[0])
    return cur


def _pts(d):
    """Back from an 'M x y L x y ... Z' path to points (single sub-path)."""
    nums = d.replace("M", " ").replace("L", " ").replace("Z", " ").split()
    v = list(map(float, nums))
    return list(zip(v[0::2], v[1::2]))


ALIASES = {
    "default": "arrow left_ptr top_left_arrow wayland-cursor dnd-ask",
    "pointer": "hand hand1 hand2 pointing_hand 9d800788f1b08800ae810202380a0822 "
               "e29285e634086352946a0e7090d73106",
    "text": "ibeam xterm",
    "wait": "watch",
    "progress": "half-busy left_ptr_watch 00000000000000020006000e7e9ffc3f "
                "08e8e1c95fe2fc01f976f1e063a24ccd 3ecb610c1bf2410f44200f48c40d3599",
    "help": "left_ptr_help question_arrow whats_this 5c6cd98b3f3ebcb1f9c7f1c204630408 "
            "d9ce0ab605698f320427677b458ad60b",
    "copy": "dnd-copy 1081e37283d90000800003c07f3ef6bf 6407b0e94181790501fd1e167b474872 "
            "b66166c04f8c3109214a4fbd64a50fc8",
    "alias": "link dnd-link 3085a0e285430894940527032f8b26df 640fb0e74195791501fd1ed57b41487f "
             "a2a266d0498c3104214a47bd64ab0fc8",
    "not-allowed": "circle crossed_circle forbidden 03b6e0fcb3499374a867c041f52298f0",
    "no-drop": "dnd-no-drop",
    "crosshair": "cross tcross color-picker cross_reverse diamond_cross",
    "cell": "plus",
    "X_cursor": "x-cursor pirate",
    "move": "fleur all-scroll all-resize size_all",
    "grab": "openhand",
    "grabbing": "closedhand dnd-move dnd-none 4498f0e0c1937ffe01fd06f973665830 "
                "9081237383d90e509aa00f00170e968f fcf21c00b30f7e3f83fe0dfd12e71cff",
    "pencil": "draft",
    "ew-resize": "h_double_arrow sb_h_double_arrow size_hor size-hor "
                 "028006030e0e7ebffc7f7070c0600140",
    "ns-resize": "v_double_arrow sb_v_double_arrow size_ver size-ver "
                 "00008160000006810000408080010102",
    "nwse-resize": "size_fdiag size-fdiag bd_double_arrow c7088f0f3e6c8088236ef8e1e3e70000",
    "nesw-resize": "size_bdiag size-bdiag fd_double_arrow fcf1c3c7cd4491d801f1e1c78f100000",
    "col-resize": "split_h 14fef782d02440884392942c11205230",
    "row-resize": "split_v 2870a09082c103050810ffdffffe0204",
    "n-resize": "top_side",
    "s-resize": "bottom_side",
    "e-resize": "right_side",
    "w-resize": "left_side",
    "nw-resize": "top_left_corner ul_angle",
    "ne-resize": "top_right_corner ur_angle",
    "se-resize": "bottom_right_corner lr_angle",
    "sw-resize": "bottom_left_corner ll_angle",
}

INDEX = """[Icon Theme]
Name=Cremisi-Obsidian-Cursors
Comment=Cremisi Obsidian: gothic cursors of spearheads, lances and a rose window
Inherits=Adwaita
"""


def main(theme_dir):
    cur = build()
    out = os.path.join(theme_dir, "cursors")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    with open(os.path.join(theme_dir, "index.theme"), "w") as fh:
        fh.write(INDEX)
    with tempfile.TemporaryDirectory() as tmp:
        for name, (frames, (hx, hy), delay) in cur.items():
            cfg = []
            for i, svg in enumerate(frames):
                src = os.path.join(tmp, f"{name}-{i}.svg")
                with open(src, "w") as fh:
                    fh.write(svg)
                for size in SIZES:
                    png = os.path.join(tmp, f"{name}-{i}-{size}.png")
                    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size),
                                    src, "-o", png], check=True)
                    k = size / BOX
                    x, y = min(size - 1, round(hx * k)), min(size - 1, round(hy * k))
                    cfg.append(f"{size} {x} {y} {png}" + (f" {delay}" if delay else ""))
            conf = os.path.join(tmp, f"{name}.cfg")
            with open(conf, "w") as fh:
                fh.write("\n".join(cfg) + "\n")
            subprocess.run(["xcursorgen", conf, os.path.join(out, name)], check=True)
        if os.environ.get("CURSOR_PREVIEW"):
            for name, (frames, _, _) in cur.items():
                with open(os.path.join(os.environ["CURSOR_PREVIEW"], f"{name}.svg"), "w") as fh:
                    fh.write(frames[0])
    for target, names in ALIASES.items():
        for alias in names.split():
            os.symlink(target, os.path.join(out, alias))
    print(f"{len(cur)} cursors, {sum(len(v.split()) for v in ALIASES.values())} aliases -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
