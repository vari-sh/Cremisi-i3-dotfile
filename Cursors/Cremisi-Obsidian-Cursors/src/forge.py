"""The forge: grid hinting, paths and Cremisi materials for the cursor glyphs.

Every glyph is drawn in a 32-unit box and re-drawn (not rescaled) for each
pixel size, so outlines keep a whole number of pixels and thin strokes sit on
the pixel grid.
"""
import math

# Cremisi tonal scales (cremisi-scales.css)
STONE = {50: "#f4eee2", 100: "#e9e1d1", 200: "#cfc6b8", 300: "#b3aa9a", 400: "#9a948c",
         500: "#827a76", 600: "#696164", 700: "#4e4a50", 800: "#302f35", 900: "#17171c",
         950: "#0c0c10"}
BLOOD = {50: "#feeff0", 100: "#ffddde", 200: "#febec1", 300: "#fa969f", 400: "#ef6f80",
         500: "#e2586a", 600: "#c42740", 700: "#a11730", 800: "#7e1023", 900: "#52151f",
         950: "#301419"}
INK = "#0b0b0f"
BONE = STONE[100]

# material ramps, lit from the top left
RIM = [(0, BLOOD[400]), (0.4, "#d63f58"), (1, BLOOD[700])]
CRIMSON = [(0, BLOOD[400]), (0.5, BLOOD[600]), (1, BLOOD[700])]
BONES = [(0, "#fbf7ef"), (0.5, BONE), (1, STONE[200])]
OBSIDIAN = [(0, "#3b3940"), (1, "#141418")]
FACET_LIT = [(0, "#625e67"), (1, "#33323a")]
FACET_DARK = [(0, "#25242b"), (1, "#0f0f13")]
GEMS = {  # light bevel, table, deep bevel
    "malachite": ("#93d6b4", "#2f7a4e", "#1b4f33"),
    "lapis": ("#a3bbe3", "#2d5c9c", "#1a3a66"),
    "amethyst": ("#cdaede", "#7e3a9e", "#532469"),
    "blood": ("#f9919e", BLOOD[600], BLOOD[800]),
}

BOX = 32


def num(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def mix(a, b, t):
    pa, pb = (int(a[i:i + 2], 16) for i in (1, 3, 5)), (int(b[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


def ramp(stops, t):
    t = min(1.0, max(0.0, t))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            return mix(c0, c1, (t - t0) / (t1 - t0))
    return stops[-1][1]


class Grid:
    """Pixel grid of one cursor size; lengths are in box units."""

    def __init__(self, size):
        self.size, self.k = size, size / BOX
        self.lod = 0 if size < 32 else 1 if size < 48 else 2

    def px(self, n=1.0):
        return n / self.k

    def snap(self, v):
        return math.floor(v * self.k + 0.5) / self.k

    def w(self, u, lo=1):
        """A width rounded to whole pixels (at least lo of them)."""
        return max(lo, math.floor(u * self.k + 0.5)) / self.k

    def thick(self, u, lo=1.0):
        """A width that never gets thinner than lo pixels."""
        return max(u, lo / self.k)

    def axis(self, c, w):
        """Centre for a stroke of width w so that both its edges hit pixel edges."""
        odd = round(w * self.k) % 2
        return (math.floor(c * self.k) + 0.5) / self.k if odd else self.snap(c)


class P:
    """A path of M/L/Q/C/Z commands that can be transformed point by point."""

    def __init__(self, c=None):
        self.c = c or []

    def M(self, x, y):
        self.c.append(("M", [(x, y)]))
        return self

    def L(self, *a):
        for i in range(0, len(a), 2):
            self.c.append(("L", [(a[i], a[i + 1])]))
        return self

    def Q(self, x1, y1, x, y):
        self.c.append(("Q", [(x1, y1), (x, y)]))
        return self

    def C(self, x1, y1, x2, y2, x, y):
        self.c.append(("C", [(x1, y1), (x2, y2), (x, y)]))
        return self

    def Z(self):
        self.c.append(("Z", []))
        return self

    def __add__(self, o):
        return P(self.c + o.c)

    def map(self, fn):
        return P([(k, [fn(x, y) for x, y in pts]) for k, pts in self.c])

    def rot(self, deg, cx=16.0, cy=16.0):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        return self.map(lambda x, y: (cx + (x - cx) * c - (y - cy) * s,
                                      cy + (x - cx) * s + (y - cy) * c))

    def move(self, dx, dy):
        return self.map(lambda x, y: (x + dx, y + dy))

    def flipx(self, ax=16.0):
        return self.map(lambda x, y: (2 * ax - x, y))

    def bbox(self):
        pts = [p for _, ps in self.c for p in ps]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)

    def d(self):
        return "".join(k + " ".join(f"{num(x)} {num(y)}" for x, y in pts) for k, pts in self.c)


def poly(pts):
    p = P().M(*pts[0])
    for q in pts[1:]:
        p.L(*q)
    return p.Z()


def rect(x0, y0, x1, y1):
    return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def diamond(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    return poly([(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)])


def circle(cx, cy, r):
    k = r * 0.5522848
    return (P().M(cx, cy - r).C(cx + k, cy - r, cx + r, cy - k, cx + r, cy)
            .C(cx + r, cy + k, cx + k, cy + r, cx, cy + r)
            .C(cx - k, cy + r, cx - r, cy + k, cx - r, cy)
            .C(cx - r, cy - k, cx - k, cy - r, cx, cy - r).Z())


def ngon(cx, cy, r, n, turn=0.0):
    return poly([(cx + r * math.sin(math.radians(turn + i * 360 / n)),
                  cy - r * math.cos(math.radians(turn + i * 360 / n))) for i in range(n)])


def line(x0, y0, x1, y1):
    return P().M(x0, y0).L(x1, y1)


def dart(tip, ang, length, hw, notch):
    """Swallow-tailed arrowhead; ang 0 points up, 90 right."""
    p = poly([(0, 0), (hw, length), (0, length - notch), (-hw, length)])
    return p.rot(ang, 0, 0).move(*tip)


class Glyph:
    """One cursor image: layers of ink silhouettes with material fills on top,
    and a soft shadow cast by all the silhouettes together."""

    def __init__(self, g):
        self.g, self.defs, self.layers, self.n = g, [], [([], [])], 0
        self.hot = (16.0, 16.0)
        self.ow = g.w(1.0)             # ink outline, whole pixels
        self.rw = g.thick(1.5, 1.3)    # crimson rim of the obsidian plates

    def uid(self):
        self.n += 1
        return f"d{self.n}"

    def layer(self):
        self.layers.append(([], []))
        return self

    def grad(self, p, stops, box=None):
        x0, y0, x1, y1 = box or p.bbox()
        i = self.uid()
        st = "".join(f'<stop offset="{num(o)}" stop-color="{c}"/>' for o, c in stops)
        self.defs.append(f'<linearGradient id="{i}" gradientUnits="userSpaceOnUse" x1="{num(x0)}" '
                         f'y1="{num(y0)}" x2="{num(x1)}" y2="{num(y1)}">{st}</linearGradient>')
        return f"url(#{i})"

    def put(self, svg):
        self.layers[-1][1].append(svg)
        return self

    def sil(self, p, width=0.0, cap="butt"):
        """Ink silhouette: the shape (or a stroke of the given width) grown by the outline."""
        if width:
            self.layers[-1][0].append(
                f'<path d="{p.d()}" fill="none" stroke="{INK}" stroke-width="{num(width + 2 * self.ow)}" '
                f'stroke-linejoin="round" stroke-linecap="{"round" if cap == "round" else "square" if cap == "square" else "butt"}"/>')
        else:
            self.layers[-1][0].append(
                f'<path d="{p.d()}" fill="{INK}" stroke="{INK}" stroke-width="{num(2 * self.ow)}" '
                f'stroke-linejoin="round"/>')
        return self

    def fill(self, p, paint, outline=True, **at):
        if outline:
            self.sil(p)
        a = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in at.items())
        return self.put(f'<path d="{p.d()}" fill="{paint}"{a}/>')

    def stroke(self, p, paint, width, outline=True, cap="butt", **at):
        if outline:
            self.sil(p, width, cap)
        a = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in at.items())
        return self.put(f'<path d="{p.d()}" fill="none" stroke="{paint}" stroke-width="{num(width)}" '
                        f'stroke-linecap="{cap}" stroke-linejoin="round"{a}/>')

    def bone(self, p, outline=True):
        return self.fill(p, self.grad(p, BONES), outline)

    def crimson(self, p, outline=True):
        return self.fill(p, self.grad(p, CRIMSON), outline)

    def plate(self, p, inner=(), rw=None, body=None):
        """Obsidian with a crimson rim: the rim is a stroke clipped to the shape,
        so it is an exact inset whatever the outline of the shape."""
        rw = rw or self.rw
        d, cid = p.d(), self.uid()
        self.defs.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        self.sil(p)
        body = body or self.grad(p, OBSIDIAN)
        return self.put(
            f'<g clip-path="url(#{cid})"><path d="{d}" fill="{body}"/>{"".join(inner)}'
            f'<path d="{d}" fill="none" stroke="{self.grad(p, RIM)}" stroke-width="{num(2 * rw)}" '
            f'stroke-linejoin="miter" stroke-miterlimit="20"/></g>')

    def svg(self):
        g, size = self.g, self.g.size
        sd = max(0.85, g.px(0.9))
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
               f'viewBox="0 0 {BOX} {BOX}"><defs>'
               f'<filter id="sh" filterUnits="userSpaceOnUse" x="-8" y="-8" width="48" height="48">'
               f'<feGaussianBlur in="SourceAlpha" stdDeviation="{num(sd)}"/>'
               f'<feOffset dx="{num(g.px(0.5) if g.lod == 0 else 0.5)}" dy="{num(max(1.0, g.px(1)))}"/></filter>',
               *self.defs, "</defs>",
               '<g filter="url(#sh)" opacity="0.5">', *(s for sils, _ in self.layers for s in sils), "</g>"]
        for sils, fills in self.layers:
            out += sils
            out += fills
        out.append("</svg>")
        return "".join(out)
