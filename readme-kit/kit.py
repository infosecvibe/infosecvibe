"""README art kit: small helpers for building animated SVG panels for a README.

Python standard library only. Text is drawn from glyph outlines stored in
glyphs.json (next to this file), so panels look identical on every machine and
inside GitHub, where web fonts cannot load.

Fonts in glyphs.json (all SIL Open Font License):
  ui5 ui6 ui7     Chakra Petch 500 / 600 / 700   technical UI lettering
  out4 out5 out6  Outfit 400 / 500 / 600         clean geometric sans
  sign            Audiowide (letters, digits, hyphen only)   neon tubing
  signb           Monoton   (letters, digits, hyphen only)   retro marquee

Rules that keep panels working on GitHub:
  - one self-contained .svg per panel, referenced from the README by relative path
  - CSS animations inside <style> only; no scripts, no external files, no web fonts
  - draw the finished state as the base attributes and animate *from* hidden,
    so a viewer with reduced motion (or a static renderer) still sees everything
  - blur filters go on a wrapper group that has no transform
  - animate opacity, transform and stroke-dashoffset only; never animate a blur
"""
import json
import pathlib

GLYPHS = json.loads((pathlib.Path(__file__).resolve().parent / "glyphs.json").read_text())


def f2(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


class Type:
    """Sets text as glyph outlines shared through <defs>. One instance per panel."""

    def __init__(self):
        self.used = {}

    def width(self, s, font, size, track=0):
        f = GLYPHS[font]
        k = size / f["upm"]
        kern = sum(f.get("k", {}).get(a + c, 0) for a, c in zip(s, s[1:]))
        return (sum(f["g"].get(c, f["g"]["?"])["a"] for c in s) + kern) * k + track * max(len(s) - 1, 0)

    def text(self, s, x, y, font, size, fill, anchor="start", track=0, attrs="", cls=None):
        """anchor: start | middle | end. cls: {letter index: css class} for per-letter effects."""
        f = GLYPHS[font]
        k = size / f["upm"]
        w = self.width(s, font, size, track)
        x0 = x - (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
        cx, uses = 0.0, []
        for i, c in enumerate(s):
            g = f["g"].get(c, f["g"]["?"])
            if g["d"]:
                gid = f"{font}-{ord(c):x}"
                self.used[gid] = g["d"]
                c_attr = f' class="{cls[i]}"' if cls and i in cls else ""
                uses.append(f'<use href="#{gid}" x="{f2(cx)}"{c_attr}/>')
            cx += g["a"] + track / k + (f.get("k", {}).get(s[i:i + 2], 0) if i + 1 < len(s) else 0)
        return (f'<g transform="translate({f2(x0)} {f2(y)}) scale({k:.5f} {-k:.5f})" fill="{fill}" {attrs}>'
                + "".join(uses) + "</g>")

    def defs(self):
        return "".join(f'<path id="{gid}" d="{d}"/>' for gid, d in sorted(self.used.items()))


def panel(w, h, label, style, defs, body):
    """Wraps a panel. label becomes the accessible name; reduced motion is respected."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{label}">\n<title>{label}</title>\n'
            f'<style>{style}@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>\n'
            f'<defs>{defs}</defs>\n{body}\n</svg>\n')


def blur(fid, std, pad=40):
    """A blur filter with room around it. Put it on an untransformed wrapper <g>."""
    return (f'<filter id="{fid}" x="-{pad}%" y="-{pad}%" width="{100 + 2 * pad}%" height="{100 + 2 * pad}%">'
            f'<feGaussianBlur stdDeviation="{std}"/></filter>')


def surface(w, h, fill, stroke, rx=16, extra=""):
    """Panel background and hairline frame. extra is drawn between the two, clipped to the panel."""
    return (f'<clipPath id="clip"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>',
            f'<g clip-path="url(#clip)"><rect width="{w}" height="{h}" fill="{fill}"/>{extra}</g>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="none" stroke="{stroke}"/>')


def glow_text(t, s, x, y, font, size, fill, glow, fid, opacity=0.5, **kw):
    """Text with a soft halo behind it. fid names a blur() filter already in <defs>."""
    return (f'<g filter="url(#{fid})" opacity="{opacity}">{t.text(s, x, y, font, size, glow, **kw)}</g>'
            + t.text(s, x, y, font, size, fill, **kw))


def neon_outline(t, s, x, y, font, size, core="#fff0fc", rim="#ff62dd", halo="#ff2fcb",
                 wide="wide", tight="tight", track=3, cls=None):
    """Neon tubing bent around each letter's outline (best with font 'sign')."""
    k = size / GLYPHS[font]["upm"]

    def tube(colour, px, fill="none"):
        return t.text(s, x, y, font, size, fill, anchor="middle", track=track, cls=cls,
                      attrs=f'stroke="{colour}" stroke-width="{px / k:.1f}" stroke-linejoin="round"')
    return (f'<g filter="url(#{wide})" opacity=".9">{tube(halo, 8)}</g>'
            f'<g filter="url(#{tight})">{tube(rim, 6.5, rim + "22")}</g>' + tube(rim, 4.8) + tube(core, 2))


def flow(d, colour, width=1.6, speed=1.2, dash="3 7", opacity=0.9):
    """A connector whose dashes travel along it, start to end. Needs FLOW_CSS in the panel style."""
    return (f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="{width}" stroke-linecap="round" '
            f'stroke-dasharray="{dash}" opacity="{opacity}" class="flow" style="animation-duration:{speed}s"/>')


FLOW_CSS = ".flow{animation:flow 1.2s linear infinite}@keyframes flow{to{stroke-dashoffset:-20}}"


def arrow(x, y, direction, colour, size=5):
    """A small arrowhead with its tip at x,y. direction: right | left | down | up."""
    s = size
    pts = {"right": f"{x},{y} {x - s * 1.5},{y - s} {x - s * 1.5},{y + s}",
           "left": f"{x},{y} {x + s * 1.5},{y - s} {x + s * 1.5},{y + s}",
           "down": f"{x},{y} {x - s},{y - s * 1.5} {x + s},{y - s * 1.5}",
           "up": f"{x},{y} {x - s},{y + s * 1.5} {x + s},{y + s * 1.5}"}[direction]
    return f'<polygon points="{pts}" fill="{colour}"/>'


def node(t, x, y, w, h, title, lines, accent, fill, stroke, ink, ink2, fonts=("ui6", "ui5")):
    """A labelled box for diagrams: accent bar, title, and up to three short lines."""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}"/>',
           f'<rect x="{x}" y="{y + 12}" width="3" height="{h - 24}" rx="1.5" fill="{accent}"/>',
           t.text(title, x + 16, y + 25, fonts[0], 14, ink)]
    for i, line in enumerate(lines):
        out.append(t.text(line, x + 16, y + 44 + i * 16, fonts[1], 11.5, ink2))
    return "".join(out)
