#!/usr/bin/env python3
"""Generate the Cremisi gothic SVG assets (diamonds, blades, lancet arches).

Usage: gen_assets.py <assets-dir> [<assets-dir> ...]
"""
import math
import os
import sys

# Cremisi Obsidian palette (taken from the existing compiled CSS/assets)
BLOOD = "#e2586a"        # accent
BLOOD_LIGHT = "#f0acb4"  # accent hover
CRYPT = "#17171c"        # surface
ABYSS = "#131317"        # view base
BONE = "#e9e1d1"         # foreground
INK = "#0f0f13"          # mark on accent


# ---------------------------------------------------------------- geometry

def f(n):
    s = f"{n:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def poly(pts):
    return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"


def diamond(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    return [(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)]


def blade(points, hw, tip=None):
    """Outline of a polyline stroked with half-width hw, miter joins and
    pointed (lozenge) caps: the stroke tapers to a point at both ends."""
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
            if i == 0:
                tx, ty = dirs[0]
                out.append((x - ty * hw * side, y + tx * hw * side))
            elif i == n - 1:
                tx, ty = dirs[-1]
                out.append((x - ty * hw * side, y + tx * hw * side))
            else:
                (ax, ay), (bx, by) = dirs[i - 1], dirs[i]
                mx, my = -(ay + by), ax + bx  # bisector normal (unnormalised)
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


def scale_pts(pts, k, c=0.0):
    return [((x - c) * k + c, (y - c) * k + c) for x, y in pts]


def lancet(x0, x1, spring, bottom):
    """Equilateral pointed (gothic) arch, as a closed path."""
    w = x1 - x0
    apex = spring - w * math.sqrt(3) / 2
    xm = (x0 + x1) / 2
    return (f"M{f(x0)} {f(bottom)} V{f(spring)} "
            f"A{f(w)} {f(w)} 0 0 1 {f(xm)} {f(apex)} "
            f"A{f(w)} {f(w)} 0 0 1 {f(x1)} {f(spring)} V{f(bottom)} Z")


def lancet_frame(x0, x1, spring, bottom, t):
    return lancet(x0, x1, spring, bottom) + " " + lancet(x0 + t, x1 - t, spring, bottom - t)


def chamfer_rect(x, y, w, h, c):
    return [(x + c, y), (x + w - c, y), (x + w, y + c), (x + w, y + h - c),
            (x + w - c, y + h), (x + c, y + h), (x, y + h - c), (x, y + c)]


# ------------------------------------------------------------------ output

def svg(size, body, scale=1):
    s = size * scale
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" '
            f'viewBox="0 0 {size} {size}" version="1.1">\n{body}</svg>\n')


def emit(dirs, name, size, body, hidpi=True):
    for d in dirs:
        with open(os.path.join(d, f"{name}.svg"), "w") as fh:
            fh.write(svg(size, body))
        if hidpi:
            with open(os.path.join(d, f"{name}@2.svg"), "w") as fh:
                fh.write(svg(size, body, 2))


def path(d, **attrs):
    a = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f' <path d="{d}"{a}/>\n'


def main(dirs):
    # ---- symbolic marks (recoloured by GTK: plain filled <path>s only) ----
    check = [(5.2, 10.2), (8.6, 13.6), (15.2, 6.6)]
    mixed = [(5.6, 10), (14.4, 10)]
    emit(dirs, "checkbox-checked-symbolic", 20, path(poly(blade(check, 0.95, 1.6))))
    emit(dirs, "checkbox-mixed-symbolic", 20, path(poly(blade(mixed, 0.95, 2.2))))
    emit(dirs, "radio-checked-symbolic", 20, path(poly(diamond(10, 10, 3.2, 4.2))))
    emit(dirs, "radio-mixed-symbolic", 20, path(poly(blade(mixed, 0.95, 2.2))))

    k = 0.8  # small (16px) variants share the 20px geometry
    emit(dirs, "small-checkbox-checked-symbolic", 16,
         path(poly(blade(scale_pts(check, k), 0.8, 1.4))))
    emit(dirs, "small-checkbox-mixed-symbolic", 16,
         path(poly(blade(scale_pts(mixed, k), 0.8, 1.8))))
    emit(dirs, "small-radio-checked-symbolic", 16, path(poly(diamond(8, 8, 2.6, 3.4))))
    emit(dirs, "small-radio-mixed-symbolic", 16,
         path(poly(blade(scale_pts(mixed, k), 0.8, 1.8))))
    emit(dirs, "menu-radio-symbolic", 14, path(poly(diamond(7, 7, 2.3, 3))))

    # touch-selection handle: a kite pointing at its corner
    emit(dirs, "cursor-handle-symbolic", 24,
         path(poly([(0, 0), (15, 4.5), (21, 21), (4.5, 15)])), hidpi=False)

    # ---- radio plates: the diamond body of radio buttons ----
    body = poly(diamond(10, 10, 9, 9))
    inner = poly(diamond(10, 10, 6, 6))
    plates = {
        "": (BONE, 0.12, BONE, 0.30, None),
        "-hover": (BONE, 0.15, BONE, 0.50, None),
        "-active": (BONE, 0.20, BONE, 0.60, None),
        "-disabled": (BONE, 0.04, BONE, 0.10, None),
        "-checked": (BLOOD, 1, BLOOD, 1, 0.30),
        "-checked-hover": (BLOOD_LIGHT, 1, BLOOD_LIGHT, 1, 0.30),
        "-checked-disabled": (BLOOD, 0.35, BLOOD, 0.35, 0.15),
    }
    for suffix, (fill, fo, stroke, so, ink) in plates.items():
        b = path(body, fill=fill, fill_opacity=fo, stroke=stroke, stroke_opacity=so,
                 stroke_width=1, stroke_linejoin="miter")
        if ink is not None:  # engraved inner diamond, like the site ornament
            b += path(inner, fill="none", stroke=INK, stroke_opacity=ink,
                      stroke_width=0.75, stroke_linejoin="miter")
        emit(dirs, f"radio-plate{suffix}", 20, b)

    # ---- scale slider (no marks): 18px diamond ----
    knob = poly(diamond(9, 9, 7, 7))
    pip = poly(diamond(9, 9, 2, 2.6))
    sliders = {
        "": (BLOOD, 1, 1.5, False),
        "-hover": (BLOOD, 1, 1.5, True),
        "-active": (BLOOD, 1, 2.25, True),
        "-disabled": (BONE, 0.32, 1.5, False),
    }
    for suffix, (stroke, so, sw, show_pip) in sliders.items():
        b = path(knob, fill=CRYPT, stroke=stroke, stroke_opacity=so,
                 stroke_width=sw, stroke_linejoin="miter")
        if show_pip:
            b += path(pip, fill=BLOOD)
        emit(dirs, f"scale-slider{suffix}", 18, b)

    # ---- scale slider with marks: a spearhead pointing at the marks ----
    spear = poly([(12, 2.5), (17.5, 13), (12, 20.5), (6.5, 13)])
    spear_pip = poly(diamond(12, 13, 1.8, 2.4))
    orient = {
        ("horz", "before"): "",
        ("horz", "after"): "rotate(180 12 12)",
        ("vert", "before"): "rotate(-90 12 12)",
        ("vert", "after"): "rotate(90 12 12)",
    }
    for (axis, side), tr in orient.items():
        for disabled in (False, True):
            stroke, so = (BONE, 0.32) if disabled else (BLOOD, 1)
            g = path(spear, fill=CRYPT, stroke=stroke, stroke_opacity=so,
                     stroke_width=2, stroke_linejoin="miter")
            g += path(spear_pip, fill=stroke, fill_opacity=so)
            body_ = f' <g transform="{tr}">\n{g} </g>\n' if tr else g
            for variant in ("", "-dark"):
                dis = "-disabled" if disabled else ""
                emit(dirs, f"scale-{axis}-marks-{side}-slider{dis}{variant}", 24, body_)

    # ---- selection-mode checkboxes (content-view tiles): chamfered stone ----
    tile = poly(chamfer_rect(3, 3, 34, 34, 7))
    tile_check = poly(blade([(11, 20.5), (17, 26.5), (29.5, 13.5)], 2, 3.2))
    for variant in ("", "-dark"):
        emit(dirs, f"selectionmode-checkbox-unchecked{variant}", 40,
             path(tile, fill=ABYSS, stroke=BONE, stroke_opacity=0.35, stroke_width=2,
                  stroke_linejoin="miter"))
        emit(dirs, f"selectionmode-checkbox-checked{variant}", 40,
             path(tile, fill=BLOOD) + path(tile_check, fill=CRYPT))

    # ---- titlebuttons: coloured diamond plates + glyphs that fit inside ----
    front = (4.75, 9.25, 9, 11.25)
    back = (6.75, 11.25, 7.25, 9.5)

    def glyph(name, **a):
        if name == "close":
            return (path(poly(blade([(5.4, 5.4), (10.6, 10.6)], 0.6, 1.1)), **a)
                    + path(poly(blade([(10.6, 5.4), (5.4, 10.6)], 0.6, 1.1)), **a))
        if name == "minimize":
            return (path(poly(blade([(4.6, 8), (11.4, 8)], 0.5, 1)), **a)
                    + path(poly(diamond(8, 8, 1.3, 1.8)), **a))
        if name == "maximize":
            return path(lancet_frame(5.5, 10.5, 8.5, 11, 1), fill_rule="evenodd", **a)
        # unmaximize: the back arch is clipped (geometry only, so it also
        # survives symbolic recolouring)
        return (' <defs><clipPath id="c"><path clip-rule="evenodd" d="M0 0 H16 V16 H0 Z '
                f'{lancet(front[0] - 1, front[1] + 1, front[2], front[3] + 1)}"/></clipPath></defs>\n'
                + path(lancet_frame(*back, 1), fill_rule="evenodd", opacity=0.4,
                       clip_path="url(#c)", **a)
                + path(lancet_frame(*front, 1), fill_rule="evenodd", **a))

    # symbolic glyphs (GTK4 recolours them through `color`), so no fills
    for name in ("close", "minimize", "maximize", "unmaximize"):
        emit(dirs, f"{name}-symbolic", 16, glyph(name))

    # pre-composed plates for every state (GTK3 cannot recolour backgrounds)
    tb = poly(diamond(8, 8, 7.5, 7.5))
    backdrop = path(tb, fill=BONE, fill_opacity=0.3)
    for name, color, active in (("close", BLOOD, "#ec929e"),
                                ("minimize", "#cf9142", "#f7e6c1"),
                                ("maximize", "#44a078", "#b8e7b6")):
        plate, plate_active = path(tb, fill=color), path(tb, fill=active)
        emit(dirs, f"titlebutton-{name}", 16, plate)
        for g in ((name, "unmaximize") if name == "maximize" else (name,)):
            emit(dirs, f"titlebutton-{g}-hover", 16, plate + glyph(g, fill="#fff"))
            emit(dirs, f"titlebutton-{g}-pressed", 16, plate_active + glyph(g, fill=INK))
            emit(dirs, f"titlebutton-{g}-backdrop-hover", 16,
                 backdrop + glyph(g, fill=BONE, fill_opacity=0.6))
    emit(dirs, "titlebutton-backdrop", 16, backdrop)


if __name__ == "__main__":
    main(sys.argv[1:])
