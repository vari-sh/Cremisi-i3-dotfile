#!/usr/bin/env python3
"""Build the Cremisi Obsidian cursor theme.

    src/build.py [THEME_DIR]            write cursors/, index.theme, preview.png
    src/build.py --sheet OUT.png [--size N ...] [--only NAME ...] [--zoom Z]
                                        only draw a contact sheet (for design work)

Needs python-cairo and librsvg through python-gobject. Each cursor is drawn
again for every size and written straight into the Xcursor container.
"""
import argparse
import math
import os
import shutil
import struct
import sys

import cairo
import gi

gi.require_version("Rsvg", "2.0")
gi.require_foreign("cairo")
from gi.repository import Rsvg  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cursors import ALIASES, CURSORS  # noqa: E402
from forge import Grid  # noqa: E402

SIZES = (24, 28, 32, 36, 40, 48, 56, 64, 72, 96)
NAME = "Cremisi-Obsidian-Cursors"
INDEX = f"""[Icon Theme]
Name={NAME}
Comment=Cremisi Obsidian: gothic, arcane cursors of obsidian, bone and blood
Inherits=Adwaita
"""
IMAGE = 0xFFFD0002


def render(name, size, frame=0):
    """-> (cairo surface, hotspot x, hotspot y, delay)"""
    name, _, at = name.partition("@")      # "wait@6" picks a frame on a contact sheet
    fn, frames, delay = CURSORS[name]
    frame = int(at) if at else frame
    grid = Grid(size)
    glyph = fn(grid, frame / frames)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    box = Rsvg.Rectangle()
    box.x = box.y = 0
    box.width = box.height = size
    Rsvg.Handle.new_from_data(glyph.svg().encode()).render_document(cairo.Context(surf), box)
    surf.flush()
    hot = [min(size - 1, max(0, math.floor(v * grid.k + 1e-6))) for v in glyph.hot]
    return surf, hot[0], hot[1], delay


def write_xcursor(path, images):
    """images: (nominal size, surface, xhot, yhot, delay), frames of one size together."""
    pos = 16 + 12 * len(images)
    toc, body = [], []
    for size, surf, xh, yh, delay in images:
        w, h = surf.get_width(), surf.get_height()
        chunk = struct.pack("<9I", 36, IMAGE, size, 1, w, h, xh, yh, delay) + bytes(surf.get_data())
        toc.append(struct.pack("<3I", IMAGE, size, pos))
        body.append(chunk)
        pos += len(chunk)
    with open(path, "wb") as fh:
        fh.write(b"Xcur" + struct.pack("<3I", 16, 0x10000, len(images)) + b"".join(toc) + b"".join(body))


def sheet(path, names, sizes, zoom=None, labels=False, cols=None, grounds=("#17171c", "#f4eee2")):
    """Contact sheet: for each size, the cursors on a dark and a light ground."""
    rows, pad = [], 10
    cols = cols or len(names)
    lines = math.ceil(len(names) / cols)
    for size in sizes:
        z = zoom or max(1, round(96 / size))
        rows.append((size, z, size * z + 2 * pad + (16 if labels else 0)))
    cw = max(s * z for s, z, _ in rows) + 2 * pad
    W = cw * cols
    H = sum(h * lines * len(grounds) for _, _, h in rows)
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(out)
    y = 0
    for size, z, h in rows:
        for ground in grounds:
            rgb = [int(ground[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            ctx.set_source_rgb(*rgb)
            ctx.rectangle(0, y, W, h * lines)
            ctx.fill()
            for i, name in enumerate(names):
                surf = render(name, size)[0]
                x0 = (i % cols) * cw + (cw - size * z) / 2
                y0 = y + (i // cols) * h + pad
                ctx.save()
                ctx.translate(x0, y0)
                ctx.scale(z, z)
                ctx.set_source_surface(surf, 0, 0)
                ctx.get_source().set_filter(cairo.FILTER_NEAREST)
                ctx.paint()
                ctx.restore()
                if labels:
                    ctx.set_source_rgba(*([0.6, 0.58, 0.55] if sum(rgb) < 1.5 else [0.39, 0.38, 0.42]), 1)
                    ctx.select_font_face("serif", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_NORMAL)
                    ctx.set_font_size(11)
                    ext = ctx.text_extents(name)
                    ctx.move_to((i % cols) * cw + (cw - ext.width) / 2, y0 + size * z + 14)
                    ctx.show_text(name)
            y += h * lines
    out.write_to_png(path)


def build(theme):
    out = os.path.join(theme, "cursors")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    for name, (_, frames, _) in CURSORS.items():
        images = []
        for size in SIZES:
            for f in range(frames):
                surf, xh, yh, delay = render(name, size, f)
                images.append((size, surf, xh, yh, delay))
        write_xcursor(os.path.join(out, name), images)
    links = 0
    for target, names in ALIASES.items():
        assert target in CURSORS, target
        for alias in names.split():
            assert alias not in CURSORS, alias
            os.symlink(target, os.path.join(out, alias))
            links += 1
    for fname in ("index.theme", "cursor.theme"):
        with open(os.path.join(theme, fname), "w") as fh:
            fh.write(INDEX)
    sheet(os.path.join(theme, "preview.png"), list(CURSORS), (48,), zoom=1, labels=True, cols=11)
    print(f"{len(CURSORS)} cursors, {links} aliases, sizes {SIZES} -> {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("theme", nargs="?", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--sheet")
    ap.add_argument("--size", type=int, nargs="+", default=[24, 48])
    ap.add_argument("--only", nargs="+")
    ap.add_argument("--zoom", type=int)
    ap.add_argument("--cols", type=int)
    a = ap.parse_args()
    if a.sheet:
        sheet(a.sheet, a.only or list(CURSORS), a.size, a.zoom, cols=a.cols)
    else:
        build(a.theme)


if __name__ == "__main__":
    main()
