#!/usr/bin/env python3
"""Patch a compiled Cremisi GTK css so radios and scale sliders become
diamonds (drawn by the radio-plate / scale-slider SVG assets) and checkboxes
lose their round shape.

Usage: patch_css.py <3|4> <gtk.css> [<gtk-dark.css> ...]
"""
import re
import sys

MARK = "/* Cremisi gothic: diamond radios */"


def scaled(name):
    return f'-gtk-scaled(url("assets/{name}.svg"), url("assets/{name}@2.svg"))'


def plate_rule(selectors, asset):
    return (f"{selectors} {{\n"
            f"  border-radius: 0;\n"
            f"  box-shadow: none;\n"
            f"  background-color: transparent;\n"
            f"  background-image: {scaled(asset)};\n"
            f"}}\n")


RULE = re.compile(r"(?P<sel>[^{}]+)\{(?P<body>[^{}]*)\}\n?")
RADIO = re.compile(r"(?<![.\w-])radio\b")
CONTEXTS = ("treeview.view", "columnview.view", "popover modelbutton.flat")


def split_radio_backgrounds(css):
    """In treeview/columnview/popover rules shared by check and radio, keep
    background declarations away from radios (they would paint a square
    behind the diamond plate, or remove the plate altogether)."""
    def repl(m):
        sel, body = m.group("sel"), m.group("body")
        lead = re.match(r"\s*(?:/\*.*?\*/\s*)*", sel, re.S).group(0)
        parts = [p.strip() for p in sel[len(lead):].split(",")]
        radios = [p for p in parts if RADIO.search(p) and any(c in p for c in CONTEXTS)]
        if not radios:
            return m.group(0)
        decls = [d for d in body.split(";") if d.strip()]
        bg = [d for d in decls if d.strip().startswith("background")]
        if not bg:
            return m.group(0)
        others = [p for p in parts if p not in radios]
        out = lead
        if others:
            out += ", ".join(others) + " {" + body + "}\n"
        rest = [d for d in decls if d not in bg]
        if rest:
            out += "\n" + ", ".join(radios) + " {" + ";".join(rest) + ";\n}\n"
        return out
    return RULE.sub(repl, css)


def replace_once(css, old, new):
    assert css.count(old) == 1, f"expected one match for: {old[:70]!r}"
    return css.replace(old, new)


def patch(css, gtk):
    if MARK not in css:
        css = patch_controls(css, gtk)
    if TB_MARK not in css:
        css = patch_titlebuttons(css, gtk)
    return css


def patch_controls(css, gtk):
    # checkboxes: sharp stone corners instead of circles
    css = replace_once(css, "check,\nradio {\n  min-height: 20px;\n  min-width: 20px;\n"
                       "  margin: 3px;\n  padding: 0;\n  border-radius: 9999px;",
                       "check,\nradio {\n  min-height: 20px;\n  min-width: 20px;\n"
                       "  margin: 3px;\n  padding: 0;\n  border-radius: 2px;")

    css = split_radio_backgrounds(css)

    # radios: diamond plates, inserted right after the radio icon rules so
    # they win over the shared check/radio state rules but still lose to the
    # more specific widget rules (theme switchers, etc.)
    anchor = re.search(r'radio:indeterminate \{\n  -gtk-icon-source: [^}]*\}\n', css)
    rules = (f"\n{MARK}\nradio {{\n"
             f"  background-repeat: no-repeat;\n"
             f"  background-position: center;\n"
             f"  background-size: contain;\n"
             f"}}\n\n"
             + plate_rule("radio", "radio-plate") + "\n"
             + plate_rule("radio:hover", "radio-plate-hover") + "\n"
             + plate_rule("radio:active", "radio-plate-active") + "\n"
             + plate_rule("radio:disabled", "radio-plate-disabled") + "\n"
             + plate_rule("radio:checked, radio:indeterminate, radio:checked:active, "
                          "radio:indeterminate:active", "radio-plate-checked") + "\n"
             + plate_rule("radio:checked:hover, radio:indeterminate:hover",
                          "radio-plate-checked-hover") + "\n"
             + plate_rule("radio:checked:disabled, radio:indeterminate:disabled",
                          "radio-plate-checked-disabled"))
    css = css[:anchor.end()] + rules + css[anchor.end():]

    # scale slider (no marks): diamond knob
    slider = "scale slider" if gtk == 3 else "scale > trough > slider"
    anchor = re.search(re.escape(slider) + r':disabled \{\n  box-shadow: [^}]*\}\n', css)
    rules = (f"\n/* Cremisi gothic: diamond slider */\n{slider} {{\n"
             f"  border-radius: 0;\n"
             f"  box-shadow: none;\n"
             f"  background-color: transparent;\n"
             f"  background-image: {scaled('scale-slider')};\n"
             f"  background-repeat: no-repeat;\n"
             f"  background-position: center;\n"
             f"  background-size: contain;\n"
             f"}}\n")
    for state in ("hover", "active", "disabled"):
        rules += (f"\n{slider}:{state} {{\n  box-shadow: none;\n"
                  f"  background-image: {scaled('scale-slider-' + state)};\n}}\n")
    css = css[:anchor.end()] + rules + css[anchor.end():]
    return css


TB_MARK = "/* Cremisi gothic: diamond titlebuttons */"
NOT = ":not(.suggested-action):not(.destructive-action)"
BUTTONS = ("minimize", "maximize", "close")


def recolor(name):
    return (f'-gtk-scaled(-gtk-recolor(url("assets/{name}.svg")), '
            f'-gtk-recolor(url("assets/{name}@2.svg")))')


def rule(selectors, *decls):
    return ", ".join(selectors) + " {\n" + "".join(f"  {d};\n" for d in decls) + "}\n\n"


def patch_titlebuttons(css, gtk):
    """Titlebuttons become coloured diamonds; the glyph is drawn by the theme
    (symbolic assets recoloured through `color`) instead of the icon theme."""
    if gtk == 3:
        # the default-decoration rules forced `color: transparent` and drew
        # white glyph images on hover: drop them, the rules below replace them
        css = re.sub(r'(#MozillaGtkWidget[^{}]*\{\n  box-shadow: none;\n)  color: transparent;\n'
                     r'(  animation: none;)', r"\1\2", css, count=1)
        css, n = re.subn(r'[^{}]*default-decoration[^{}]*\{\n  background-image: -gtk-scaled'
                         r'\(url\("assets/(?:minimize|maximize|close|unmaximize)-symbolic\.svg"\)'
                         r'[^{}]*\}\n\n', "", css)
        assert n == 4, n
        css = replace_once(css, ".background:not(.csd) .titlebar.default-decoration "
                           "button.titlebutton:active {\n  background-size: 1000% 1000%;\n}\n\n", "")

        def sel(btn, state="", pre=""):
            return [f"{pre}button.{btn}.titlebutton{state}{NOT}"]

        out = f"{TB_MARK}\n"
        for b in BUTTONS:
            out += rule(sel(b), "border-radius: 0", "box-shadow: none",
                        "background-color: transparent",
                        f"background-image: {scaled(f'titlebutton-{b}')}",
                        "background-repeat: no-repeat", "background-position: center",
                        "background-size: 16px 16px")
            out += rule([s + " image" for s in sel(b)], "opacity: 0")
        for b, pre, btn in [(b, "", b) for b in BUTTONS] + [("unmaximize", ".maximized ", "maximize")]:
            out += rule(sel(btn, ":hover", pre),
                        f"background-image: {scaled(f'titlebutton-{b}-hover')}")
            out += rule(sel(btn, ":active", pre), "box-shadow: none",
                        "background-color: transparent",
                        f"background-image: {scaled(f'titlebutton-{b}-pressed')}")
            if not pre:
                out += rule(sel(btn, ":backdrop"), "background-color: transparent",
                            f"background-image: {scaled('titlebutton-backdrop')}")
            out += rule(sel(btn, ":backdrop:hover", pre) + sel(btn, ":backdrop:active", pre),
                        "background-color: transparent",
                        f"background-image: {scaled(f'titlebutton-{b}-backdrop-hover')}")
        # the removed glyph rules sat right before .monospace
        anchor = re.search(r'\.monospace \{', css)
        return css[:anchor.start()] + "\n\n" + out + css[anchor.start():]

    def img(btn, state="", pre=""):
        return [f"{pre}windowcontrols > button.{btn}{state}{NOT} > image"]

    # the icon-theme glyph is hidden (it is symbolic, so `color` hides it) and
    # the pre-composed diamond + glyph is drawn as the image background
    out = f"\n{TB_MARK}\n"
    for b in BUTTONS:
        out += rule(img(b), "color: transparent", "border-radius: 0", "box-shadow: none",
                    "background-color: transparent",
                    f"background-image: {scaled(f'titlebutton-{b}')}",
                    "background-repeat: no-repeat", "background-position: center",
                    "background-size: contain")
    for b, pre, btn in [(b, "", b) for b in BUTTONS] + [("unmaximize", "window.maximized ", "maximize")]:
        out += rule(img(btn, ":hover", pre),
                    f"background-image: {scaled(f'titlebutton-{b}-hover')}")
        if not pre:
            out += rule(img(btn, ":backdrop"), "background-color: transparent",
                        f"background-image: {scaled('titlebutton-backdrop')}")
        out += rule(img(btn, ":backdrop:hover", pre),
                    f"background-image: {scaled(f'titlebutton-{b}-backdrop-hover')}")
        out += rule(img(btn, ":active", pre), "box-shadow: none",
                    "background-color: transparent",
                    f"background-image: {scaled(f'titlebutton-{b}-pressed')}")
    anchor = re.search(r'windowcontrols > button' + re.escape(NOT) +
                       r' > image \{\n  border-radius: 100%;\n  padding: 0;\n\}\n', css)
    return css[:anchor.end()] + out + css[anchor.end():]


def main():
    gtk = int(sys.argv[1])
    for p in sys.argv[2:]:
        with open(p) as fh:
            css = fh.read()
        with open(p, "w") as fh:
            fh.write(patch(css, gtk))
        print("patched", p)


if __name__ == "__main__":
    main()
