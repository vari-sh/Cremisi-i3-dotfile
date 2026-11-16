"""The reliquary: every cursor, drawn from Cremisi's own motifs.

Obsidian plates rimmed in crimson for whatever points and grips (the arrow,
the gauntlets), polished bone for the tools of precision (beam, crosshair,
resize lances), cut stones for the states, and the rose window for waiting.
"""
import math

from forge import (BLOOD, BONE, BONES, CRIMSON, GEMS, INK, OBSIDIAN, RIM,
                   STONE, Glyph, P, circle, dart, diamond, line, mix, ngon, num, poly, ramp, rect)

# ------------------------------------------------------------------ the arrow
A_LEN = 24.0
A_HW, A_SH = 0.305, 0.583       # half-width and shoulder height, as fractions of the length
A_TILT = -math.degrees(math.atan(A_HW / A_SH))      # the left edge stands vertical
HEART = [(0, BLOOD[100]), (0.45, BLOOD[400]), (1, BLOOD[600])]


def blade(G, tip, ang=A_TILT, length=A_LEN, flip=False):
    """An obsidian lozenge cut in four facets and edged in crimson, with a
    blood stone set where the ridges cross."""
    g = G.g
    w, sh = length * A_HW, length * A_SH

    def place(p):
        p = p.rot(ang, 0, 0).move(*tip)
        return p.flipx() if flip else p

    corners = [(0, 0), (w, sh), (0, length), (-w, sh)]
    inner = []
    for a, b in zip(corners, corners[1:] + corners[:1]):
        f = place(poly([a, b, (0, sh)]))
        (x0, y0), (x1, y1), (cx, cy) = (pts[0] for _, pts in f.c[:3])
        dx, dy = (x0 + x1) / 2 - cx, (y0 + y1) / 2 - cy
        lit = 0.5 - 0.5 * (dx + dy) / (math.hypot(dx, dy) * 1.4142)     # light from the top left
        inner.append(f'<path d="{f.d()}" fill="{mix("#101014", "#5d5963", lit)}"/>')
    if g.lod == 2:      # glints along the ridges
        for q in (line(0, length * 0.1, 0, length * 0.92), line(-w * 0.8, sh, w * 0.8, sh)):
            inner.append(f'<path d="{place(q).d()}" fill="none" stroke="{BONE}" stroke-opacity="0.16" '
                         f'stroke-width="{num(g.px(1))}"/>')
    G.plate(place(poly(corners)), inner)
    s = length / A_LEN
    rx, ry = (2.4, 3.3) if g.lod == 0 else (2.2, 3.2)
    heart = place(diamond(0, sh, rx * s, ry * s))
    return G.fill(heart, G.grad(heart, HEART), outline=False)


def base(g):
    G = Glyph(g)
    G.hot = (g.snap(4.5), g.snap(3.0))
    return blade(G, G.hot)


def right_ptr(g):
    G = Glyph(g)
    tip = (g.snap(4.5), g.snap(3.0))
    G.hot = (32 - tip[0] - g.px(0.5), tip[1])
    return blade(G, tip, flip=True)


def center_ptr(g):
    G = Glyph(g)
    G.hot = (g.snap(16), g.snap(3.5))
    return blade(G, G.hot, ang=0, length=22)


def lance(g, ang):
    """up-arrow and its turns: spearhead, bone shaft, crimson pommel."""
    G = Glyph(g)
    t = g.w(1.7)
    c = g.axis(16, t)
    tf = lambda p: p.rot(ang, c, c)
    G.bone(tf(rect(c - t / 2, 12, c + t / 2, 25.4)))
    G.crimson(tf(diamond(c, 26.6, 2.3, 2.6)))
    G.layer()
    blade(G, tf(P().M(c, 3.4)).c[0][1][0], ang=ang, length=15)
    G.hot = tf(P().M(c, 3.4 + g.px(0.5))).c[0][1][0]
    return G


# ------------------------------------------------------------- cut stones
def gem(G, kind, w=0.0):
    """An octagonal cut stone at the lower right; returns its centre."""
    g = G.g
    cx, cy, r = (g.axis(23.0, w), g.axis(23.2, w), 6.2) if w else (23.0, 23.2, 6.2)
    light, table, deep = GEMS[kind]
    G.layer()
    o = ngon(cx, cy, r, 8, 22.5)
    G.fill(o, G.grad(o, [(0, light), (0.5, mix(light, table, 0.55)), (1, deep)]))
    t = ngon(cx, cy, r - max(1.25, g.px(1.0)), 8, 22.5)
    G.fill(t, G.grad(t, [(0, mix(table, deep, 0.4)), (1, mix(table, light, 0.15))]), outline=False)
    return cx, cy


def copy(g):
    G = base(g)
    w = g.w(2.0)
    cx, cy = gem(G, "malachite", w)
    G.fill(rect(cx - 3.4, cy - w / 2, cx + 3.4, cy + w / 2), STONE[50], outline=False)
    return G.fill(rect(cx - w / 2, cy - 3.4, cx + w / 2, cy + 3.4), STONE[50], outline=False)


def alias(g):
    G = base(g)
    cx, cy = gem(G, "lapis")
    G.fill(poly([(cx + 3.1, cy - 3.1), (cx - 1.3, cy - 3.1), (cx + 3.1, cy + 1.3)]), STONE[50], outline=False)
    return G.stroke(line(cx - 2.6, cy + 2.6, cx + 1.0, cy - 1.0), STONE[50], g.thick(1.6, 1.4),
                    outline=False, cap="round")


def help_(g):
    G = base(g)
    cx, cy = gem(G, "amethyst")
    hook = (P().M(cx - 1.9, cy - 1.7).C(cx - 1.9, cy - 4.3, cx + 2.1, cy - 4.3, cx + 2.1, cy - 1.9)
            .C(cx + 2.1, cy - 0.4, cx, cy - 0.3, cx, cy + 1.2))
    G.stroke(hook, STONE[50], g.thick(1.5, 1.3), outline=False, cap="round")
    return G.fill(diamond(cx, cy + 3.3, 1.1), STONE[50], outline=False)


def context_menu(g):
    """A folio with a rubricated first line."""
    G = base(g)
    G.layer()
    x0, y0, x1, y1 = g.snap(18.2), g.snap(16.8), g.snap(27.8), g.snap(28.6)
    G.bone(rect(x0, y0, x1, y1))
    w = g.w(1.0)
    for i, yy in enumerate((19.5, 22.6, 25.7)):
        y = g.axis(yy, w)
        G.fill(rect(x0 + g.w(1.6), y - w / 2, x1 - g.w(1.6 if i < 2 else 3.6), y + w / 2),
               BLOOD[600] if i == 0 else STONE[600], outline=False)
    return G


def forbid(G, cx, cy, r, band, solid):
    ring = circle(cx, cy, r - band / 2)
    disc = circle(cx, cy, r - band / 2)
    if solid:
        G.fill(disc, G.grad(disc, OBSIDIAN), outline=False)
    else:
        G.fill(disc, INK, outline=False, fill_opacity="0.3")
    paint = G.grad(circle(cx, cy, r), RIM)
    s = (r - band * 0.6) * 0.7071
    G.stroke(line(cx - s, cy - s, cx + s, cy + s), paint, band * 0.92)
    return G.stroke(ring, paint, band)


def not_allowed(g):
    return forbid(Glyph(g), 16, 16, 12.4, g.thick(2.7, 2.0), False)


def no_drop(g):
    G = base(g)
    G.layer()
    return forbid(G, 23.0, 23.2, 6.3, g.thick(1.9, 1.5), True)


# -------------------------------------------------------------- gauntlets
CUFF = poly([(11.2, 25.2), (25.4, 25.2), (26.4, 27), (25.4, 28.8), (11.2, 28.8), (10.2, 27)])
HANDS = {
    "point": (P().M(13.4, 2.5).Q(16.2, 4.2, 16.2, 7.2).L(16.2, 12.3).Q(16.2, 10.7, 18.3, 10.2)
              .Q(20.4, 10.7, 20.4, 12.8).Q(20.4, 11.7, 22.4, 11.3).Q(24.4, 11.8, 24.4, 13.9)
              .Q(24.4, 13.0, 26.2, 12.7).Q(27.9, 13.2, 27.9, 15.4).L(27.9, 19.5).Q(27.9, 23.6, 24.6, 26)
              .L(13, 26).Q(11.2, 23.2, 9.2, 21.4).Q(5.4, 18.3, 4.4, 13.0).Q(7.6, 14.0, 10.6, 17.2)
              .L(10.6, 7.2).Q(10.6, 4.2, 13.4, 2.5).Z(),
              [(16.2, 12.3, 17.4), (20.4, 12.8, 17.4), (24.4, 13.9, 17.8)], (13.4, 2.5)),
    "open": (P().M(12.3, 5.0).Q(14.4, 6.4, 14.4, 8.2).Q(14.4, 4.8, 16.5, 3.4).Q(18.6, 4.8, 18.6, 7.6)
             .Q(18.6, 6.0, 20.7, 4.7).Q(22.8, 6.0, 22.8, 10.4).Q(22.8, 9.2, 24.7, 8.1)
             .Q(26.6, 9.4, 26.6, 12.5).L(26.6, 19.5).Q(26.6, 24, 23.6, 26).L(13.2, 26)
             .Q(11.2, 23.6, 9, 21.6).Q(5.2, 19.0, 4.0, 14.0).Q(7.4, 14.6, 10.2, 17.6).L(10.2, 8.6)
             .Q(10.2, 6.2, 12.3, 5.0).Z(),
             [(14.4, 8.2, 15.6), (18.6, 7.6, 15.6), (22.8, 10.4, 16.0)], (16.0, 15.0)),
    "fist": (P().M(10.4, 13.2).Q(10.4, 10.3, 12.5, 9.8).Q(14.6, 10.2, 14.6, 12.2).Q(14.6, 9.7, 16.7, 9.2)
             .Q(18.8, 9.6, 18.8, 11.9).Q(18.8, 10.0, 20.9, 9.6).Q(23, 10.0, 23, 12.5)
             .Q(23, 11.1, 24.9, 10.8).Q(26.6, 11.2, 26.6, 13.8).L(26.6, 19.5).Q(26.6, 24, 23.6, 26)
             .L(13.2, 26).Q(11, 23.8, 9, 22).Q(5.8, 20, 5.8, 16.0).Q(8.2, 15.4, 10.4, 17.2).Z(),
             [(14.6, 12.2, 16.8), (18.8, 11.9, 16.8), (23, 12.5, 17.0)], (16.0, 15.0)),
}


def hand(g, kind):
    """A plate gauntlet with lancet fingertips and a crimson cuff."""
    G = Glyph(g)
    body, seps, hot = HANDS[kind]
    G.hot = (hot[0], hot[1] + g.px(0.5))
    paint = G.grad(body, RIM)
    w = g.thick(0.9, 0.95)
    inner = [f'<path d="{line(x, y0 - 0.6, x, y1).d()}" fill="none" stroke="{paint}" stroke-width="{num(w)}"/>'
             for x, y0, y1 in seps]
    G.plate(body, inner)
    G.layer()
    G.crimson(CUFF)
    if g.lod:
        G.fill(diamond(18.3, 27, 1.5, 1.15), STONE[50], outline=False)
    return G


# ------------------------------------------------------- bone instruments
def text(g, vertical=False):
    """The I-beam as a blackletter minim: bladed serifs, a crimson waist."""
    G = Glyph(g)
    sw = st = g.w(1.4)
    cx, y0, y1, arm = g.axis(16, sw), g.snap(4.6), g.snap(27.4), 4.3
    tf = (lambda p: p.rot(90, 16, 16)) if vertical else (lambda p: p)
    G.bone(tf(rect(cx - sw / 2, y0, cx + sw / 2, y1)))
    for y in (y0, y1 - st):
        G.bone(tf(poly([(cx - arm - st * 0.8, y + st / 2), (cx - arm, y), (cx + arm, y),
                        (cx + arm + st * 0.8, y + st / 2), (cx + arm, y + st), (cx - arm, y + st)])))
    waist = tf(diamond(cx, 16, sw / 2 + g.thick(0.9, 1.0), sw / 2 + g.thick(1.9, 2.0)))
    G.fill(waist, G.grad(waist, HEART), outline=False)
    G.hot = (16, cx) if vertical else (cx, 16)
    return G


def crosshair(g):
    G = Glyph(g)
    t = g.w(1.3)
    c = g.axis(16, t)
    far, near = c - g.snap(3.4), c - g.snap(12.6)
    for q in range(4):
        G.bone(rect(c - t / 2, far, c + t / 2, near).rot(90 * q, c, c))
        if g.lod:
            G.bone(diamond(c, far + 1.3, t / 2 + g.thick(0.8, 1.0), 2.2).rot(90 * q, c, c))
    dot = rect(c - t / 2, c - t / 2, c + t / 2, c + t / 2) if g.lod == 0 else diamond(c, c, t * 1.05)
    G.fill(dot, BLOOD[500])
    G.hot = (c, c)
    return G


def cell(g):
    """A blood cross pattee with a bone boss."""
    G = Glyph(g)
    a, b, r, pts = 1.7, 3.9, 11.4, []
    for q in range(4):
        co, si = round(math.cos(q * math.pi / 2)), round(math.sin(q * math.pi / 2))
        pts += [(16 + x * co - y * si, 16 + x * si + y * co) for x, y in ((-a, -a), (-b, -r), (b, -r), (a, -a))]
    G.crimson(poly(pts))
    return G.fill(diamond(16, 16, 2.0), STONE[50], outline=False)


def move(g, shafts=True):
    """Four lance heads round a blood stone (with shafts: move; without: all-scroll)."""
    G = Glyph(g)
    t = g.w(1.7)
    c = g.axis(16, t)
    for q in range(4):
        if shafts:
            G.bone(rect(c - t / 2, c - 9, c + t / 2, c - 2).rot(90 * q, c, c))
            G.bone(dart((c, c - 13), 0, 5.6, 4.4, 1.7).rot(90 * q, c, c))
        else:
            G.bone(dart((c, c - 13), 0, 6.4, 5.0, 2.2).rot(90 * q, c, c))
    G.layer()
    G.crimson(diamond(c, c, 2.8 if shafts else 3.4))
    if not shafts and g.lod:
        G.fill(diamond(c, c, 1.2), STONE[50], outline=False)
    G.hot = (c, c)
    return G


def double(g, ang, kind="plain"):
    """Resize lances. Canonical form is vertical; kind 'edge' adds the wall it
    pushes against (above), 'corner' a bracket (canonical: top left)."""
    G = Glyph(g)
    t = g.w(1.7)
    c = g.axis(16, t)
    diag = kind == "corner" or ang % 90 != 0
    off, hl = (0.0, 14.4 if diag else 13.0) if kind == "plain" else (1.5, 12.8 if diag else 11.2)
    cy = c + off
    parts = [rect(c - t / 2, cy - hl + 4.4, c + t / 2, cy + hl - 4.4),
             dart((c, cy - hl), 0, 5.8, 4.4, 1.7), dart((c, cy + hl), 180, 5.8, 4.4, 1.7)]
    stone = diamond(c, cy, 2.4)
    wall = []
    if kind == "edge":
        y = g.snap(16 - 13.4)
        wall = [rect(c - 7, y, c + 7, y + g.w(1.6))]
    elif kind == "corner":
        parts = [p.rot(-45, c, c) for p in parts]
        stone = stone.rot(-45, c, c)
        p0, tw = g.snap(16 - 11.4), g.w(1.6)
        wall = [poly([(p0, p0), (p0 + 8.4, p0), (p0 + 8.4, p0 + tw), (p0 + tw, p0 + tw),
                      (p0 + tw, p0 + 8.4), (p0, p0 + 8.4)])]
    for p in parts + wall:
        G.bone(p.rot(ang, c, c))
    G.layer()
    G.crimson(stone.rot(ang, c, c))
    G.hot = (c, c)
    return G


def split(g, ang):
    """col-resize (canonical) and row-resize: a mullion with a lance head on each side."""
    G = Glyph(g)
    t = g.w(1.7)
    c = g.axis(16, t)
    parts = [poly([(c, c - 12.4), (c + t / 2, c - 10.8), (c + t / 2, c + 10.8), (c, c + 12.4),
                   (c - t / 2, c + 10.8), (c - t / 2, c - 10.8)])]
    for a in (90, 270):
        parts += [dart((c, c - 13.4), 0, 5.4, 4.3, 1.6).rot(a, c, c),
                  rect(c - t / 2, c - 8.8, c + t / 2, c - 4.6).rot(a, c, c)]
    for p in parts:
        G.bone(p.rot(ang, c, c))
    G.fill(diamond(c, c, t / 2 + g.thick(0.7, 1.0), t / 2 + g.thick(1.7, 2.0)).rot(ang, c, c), BLOOD[500], outline=False)
    G.hot = (c, c)
    return G


# ---------------------------------------------------------------- relics
def zoom(g, sign):
    """A scrying glass."""
    G = Glyph(g)
    w = g.w(1.7)
    cx = cy = g.axis(13, w)
    r, band = 9.4, g.thick(2.2, 1.7)
    G.bone(poly([(20.6, 18.4), (28.2, 26), (26, 28.2), (18.4, 20.6)]))
    G.layer()
    glass = circle(cx, cy, r - band / 2)
    G.fill(glass, "#15151a", outline=False, fill_opacity="0.62")
    if g.lod:
        G.stroke(P().M(cx - 5.2, cy - 1.4).Q(cx - 4.6, cy - 4.6, cx - 1.4, cy - 5.2), BONE, g.thick(0.8, 0.9),
                 outline=False, cap="round", stroke_opacity="0.4")
    G.stroke(glass, G.grad(circle(cx, cy, r), RIM), band)
    G.fill(rect(cx - 4.2, cy - w / 2, cx + 4.2, cy + w / 2), STONE[50], outline=False)
    if sign == "+":
        G.fill(rect(cx - w / 2, cy - 4.2, cx + w / 2, cy + 4.2), STONE[50], outline=False)
    G.hot = (cx, cy)
    return G


def along(origin, to):
    """Local frame: x runs from origin towards `to`."""
    ang = math.degrees(math.atan2(to[1] - origin[1], to[0] - origin[0]))
    return lambda p: p.rot(ang, 0, 0).move(*origin)


def quill(g):
    """pencil: a bone quill, its nib dipped in blood."""
    G = Glyph(g)
    nib = (4.5, 26.8)
    tf = along(nib, (26.6, 4.0))
    vane = (P().M(0, 0).L(2.6, -1.0).L(9, -1.2).C(12.5, -5.0, 23, -5.6, 31.6, 0)
            .C(24, 5.8, 13.5, 5.6, 9, 1.2).L(2.6, 1.0).Z())
    G.bone(tf(vane))
    if g.lod:
        G.stroke(tf(line(8.5, 0, 29.5, 0)), STONE[400], g.thick(0.7, 0.9), outline=False, cap="round")
        for u in (14.5, 19.5, 24.5):
            G.stroke(tf(P().M(u, 0).L(u - 2.6, -3.4)), STONE[400], g.thick(0.5, 0.7), outline=False,
                     cap="round", stroke_opacity="0.75")
    tip = tf(poly([(0, 0), (2.6, -1.0), (4.6, -1.1), (4.6, 1.1), (2.6, 1.0)]))
    G.fill(tip, G.grad(tip, CRIMSON), outline=False)
    G.hot = (nib[0], nib[1] - g.px(0.5))
    return G


def dropper(g):
    """color-picker: a phial drawing blood."""
    G = Glyph(g)
    tipp = (4.5, 26.8)
    tf = along(tipp, (26.0, 5.3))
    tube = poly([(0, 0), (5.5, -2.1), (17.4, -2.1), (17.4, 2.1), (5.5, 2.1)])
    G.bone(tf(tube))
    G.fill(tf(poly([(1.6, 0), (6.0, -1.0), (12.5, -1.0), (12.5, 1.0), (6.0, 1.0)])), BLOOD[600], outline=False)
    G.layer()
    bulb = (P().M(19.2, -3.7).C(24, -4.6, 29.4, -3.4, 29.4, 0).C(29.4, 3.4, 24, 4.6, 19.2, 3.7).Z())
    G.plate(tf(bulb), rw=G.rw * 0.9)
    G.crimson(tf(rect(16.6, -3.9, 19.6, 3.9)))
    G.hot = (tipp[0], tipp[1] - g.px(0.5))
    return G


def skull(g):
    """pirate (xkill): memento mori."""
    G = Glyph(g)
    head = (P().M(6.4, 14.2).C(6.4, 2.6, 25.6, 2.6, 25.6, 14.2).C(25.6, 17.6, 24.2, 19.2, 22.4, 20.2)
            .L(22.4, 25.2).L(9.6, 25.2).L(9.6, 20.2).C(7.8, 19.2, 6.4, 17.6, 6.4, 14.2).Z())
    G.bone(head)
    for x in (11.9, 20.1):
        G.fill(circle(x, 14.6, 2.75), INK, outline=False)
        G.fill(diamond(x, 14.8, 1.05, 1.3), BLOOD[500], outline=False)
    G.fill(poly([(16, 17.0), (17.4, 19.9), (14.6, 19.9)]), INK, outline=False)
    w = g.thick(0.8, 1.0)
    for x in (12.8, 16, 19.2):
        G.stroke(line(x, 22.0, x, 25.2), INK, w, outline=False)
    return G


def x_cursor(g):
    """Two crossed blades."""
    G = Glyph(g)
    b = poly([(16, 2.6), (18.3, 6.4), (18.3, 25.6), (16, 29.4), (13.7, 25.6), (13.7, 6.4)])
    for a in (45, -45):
        G.crimson(b.rot(a))
    return G.fill(diamond(16, 16, 2.3), STONE[50], outline=False)


# ---------------------------------------------------------- the rose window
PANE = [(0, "#4a141d"), (0.3, BLOOD[800]), (0.55, BLOOD[600]), (0.8, BLOOD[400]), (1, "#ffe3e5")]


def lit(d):
    """How brightly a pane burns when the light passed it d panes ago."""
    return d if d < 1 else math.exp(-(d - 1) / 1.5)


def rose(G, cx, cy, R, t, mini=False):
    g, n = G.g, 8
    head = t * n
    disc = circle(cx, cy, R)
    G.fill(disc, G.grad(disc, [(0, "#2d2c33"), (1, "#0f0f13")]))
    band = g.thick(R * (0.16 if mini else 0.12), 1.15)
    ri = R - band
    ra, rs, r0 = ri - g.thick(0.05 * R, 0.5), 0.56 * ri + 0.9, 0.26 * R
    hw = rs * 0.414 * (0.86 if mini else 0.76)
    k = rs + (ra - rs) * 0.62
    petal = P().M(cx, cy - r0).L(cx + hw, cy - rs).Q(cx + hw, cy - k, cx, cy - ra).Q(cx - hw, cy - k, cx - hw, cy - rs).Z()
    panes, glow = [], []
    for i in range(n):
        v = lit((head - i) % n)
        p = petal.rot(i * 360 / n, cx, cy)
        panes.append(f'<path d="{p.d()}" fill="{ramp(PANE, v)}"/>')
        if v > 0.4:
            glow.append(f'<path d="{p.d()}" fill="{BLOOD[400]}" fill-opacity="{num(min(1, (v - 0.4) * 1.5))}"/>')
    if g.lod == 2 and not mini:     # oculi between the lancets
        for i in range(n):
            v = lit((head - i - 0.5) % n)
            panes.append(f'<path d="{circle(cx, cy - ri + 0.115 * R, 0.062 * R).rot((i + 0.5) * 360 / n, cx, cy).d()}" '
                         f'fill="{ramp(PANE, v * 0.9)}"/>')
    if glow and not mini:
        cid, fid = G.uid(), G.uid()
        G.defs.append(f'<clipPath id="{cid}"><path d="{disc.d()}"/></clipPath><filter id="{fid}" '
                      f'filterUnits="userSpaceOnUse" x="-8" y="-8" width="48" height="48">'
                      f'<feGaussianBlur stdDeviation="{num(R * 0.09)}"/></filter>')
        G.put(f'<g clip-path="url(#{cid})"><g filter="url(#{fid})" opacity="0.75">{"".join(glow)}</g></g>')
    G.put("".join(panes))
    G.stroke(circle(cx, cy, R - band / 2), G.grad(disc, RIM), band, outline=False)
    G.fill(circle(cx, cy, 0.2 * R), INK, outline=False)
    return G.fill(diamond(cx, cy, (0.17 if mini else 0.13) * R).rot(0 if mini else t * 90, cx, cy), STONE[50], outline=False)


def wait(g, t):
    return rose(Glyph(g), 16, 16, 12.8, t)


def progress(g, t):
    G = base(g)
    G.layer()
    return rose(G, 23.2, 23.2, 6.1, t, mini=True)


# -------------------------------------------------------------- the index
def still(fn, *a, **kw):
    return (lambda g, t: fn(g, *a, **kw)), 1, 0


FRAMES, DELAY = 24, 50
CURSORS = {
    "default": still(base), "right_ptr": still(right_ptr), "center_ptr": still(center_ptr),
    "pointer": still(hand, "point"), "grab": still(hand, "open"), "grabbing": still(hand, "fist"),
    "text": still(text), "vertical-text": still(text, True),
    "wait": (wait, FRAMES, DELAY), "progress": (progress, FRAMES, DELAY),
    "help": still(help_), "copy": still(copy), "alias": still(alias), "context-menu": still(context_menu),
    "not-allowed": still(not_allowed), "no-drop": still(no_drop),
    "crosshair": still(crosshair), "cell": still(cell), "move": still(move), "all-scroll": still(move, False),
    "zoom-in": still(zoom, "+"), "zoom-out": still(zoom, "-"),
    "pencil": still(quill), "color-picker": still(dropper), "pirate": still(skull), "X_cursor": still(x_cursor),
    "up-arrow": still(lance, 0), "right-arrow": still(lance, 90), "down-arrow": still(lance, 180),
    "left-arrow": still(lance, 270),
    "ns-resize": still(double, 0), "ew-resize": still(double, 90),
    "nwse-resize": still(double, -45), "nesw-resize": still(double, 45),
    "n-resize": still(double, 0, "edge"), "e-resize": still(double, 90, "edge"),
    "s-resize": still(double, 180, "edge"), "w-resize": still(double, 270, "edge"),
    "nw-resize": still(double, 0, "corner"), "ne-resize": still(double, 90, "corner"),
    "se-resize": still(double, 180, "corner"), "sw-resize": still(double, 270, "corner"),
    "col-resize": still(split, 0), "row-resize": still(split, 90),
}

ALIASES = {
    "default": "arrow left_ptr top_left_arrow wayland-cursor",
    "right_ptr": "draft_large draft_small",
    "pointer": "hand hand1 hand2 pointing_hand 9d800788f1b08800ae810202380a0822 "
               "e29285e634086352946a0e7090d73106",
    "text": "ibeam xterm",
    "vertical-text": "048008013003cff3c00c801001200000",
    "wait": "watch clock 0426c94ea35c87780ff01dc239897213",
    "progress": "half-busy left_ptr_watch 00000000000000020006000e7e9ffc3f "
                "08e8e1c95fe2fc01f976f1e063a24ccd 3ecb610c1bf2410f44200f48c40d3599 "
                "9116a3ea924ed2162ecab71ba103b17f",
    "help": "left_ptr_help question_arrow whats_this 5c6cd98b3f3ebcb1f9c7f1c204630408 "
            "d9ce0ab605698f320427677b458ad60b",
    "copy": "dnd-copy 1081e37283d90000800003c07f3ef6bf 6407b0e94181790501fd1e167b474872 "
            "b66166c04f8c3109214a4fbd64a50fc8",
    "alias": "link dnd-link 3085a0e285430894940527032f8b26df 640fb0e74195791501fd1ed57b41487f "
             "a2a266d0498c3104214a47bd64ab0fc8",
    "context-menu": "dnd-ask",
    "not-allowed": "circle crossed_circle forbidden 03b6e0fcb3499374a867c041f52298f0",
    "no-drop": "dnd-no-drop",
    "crosshair": "cross tcross cross_reverse diamond_cross target dotbox dot_box_mask draped_box icon",
    "cell": "plus",
    "X_cursor": "x-cursor X-cursor",
    "pirate": "kill",
    "move": "fleur size_all all-resize pointer-move",
    "grab": "openhand 5aca4d189052212118709018842178c0 9141b49c8149039304290b508d208c40",
    "grabbing": "closedhand dnd-move dnd-none 208530c400c041818281048008011002 "
                "4498f0e0c1937ffe01fd06f973665830 9081237383d90e509aa00f00170e968f "
                "fcf21c00b30f7e3f83fe0dfd12e71cff",
    "zoom-in": "zoom_in f41c0e382c94c0958e07017e42b00462",
    "zoom-out": "zoom_out f41c0e382c97c0938e07017e42800402",
    "pencil": "draft",
    "up-arrow": "up_arrow sb_up_arrow based_arrow_up",
    "down-arrow": "down_arrow sb_down_arrow based_arrow_down",
    "left-arrow": "left_arrow sb_left_arrow",
    "right-arrow": "right_arrow sb_right_arrow",
    "ew-resize": "h_double_arrow sb_h_double_arrow size_hor size-hor "
                 "028006030e0e7ebffc7f7070c0600140",
    "ns-resize": "v_double_arrow sb_v_double_arrow double_arrow size_ver size-ver "
                 "00008160000006810000408080010102",
    "nwse-resize": "size_fdiag size-fdiag bd_double_arrow c7088f0f3e6c8088236ef8e1e3e70000",
    "nesw-resize": "size_bdiag size-bdiag fd_double_arrow fcf1c3c7cd4491d801f1e1c78f100000",
    "col-resize": "split_h 14fef782d02440884392942c11205230 043a9f68147c53184671403ffa811cc5",
    "row-resize": "split_v 2870a09082c103050810ffdffffe0204 c07385c7190e701020ff7ffffd08103c",
    "n-resize": "top_side", "s-resize": "bottom_side", "e-resize": "right_side", "w-resize": "left_side",
    "nw-resize": "top_left_corner ul_angle", "ne-resize": "top_right_corner ur_angle",
    "se-resize": "bottom_right_corner lr_angle", "sw-resize": "bottom_left_corner ll_angle",
}
