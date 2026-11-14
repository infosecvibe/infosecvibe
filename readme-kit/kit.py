"""README art kit: small helpers for building animated SVG panels for a README.

Python standard library only. Text is drawn from glyph outlines stored in
glyphs.json (next to this file), so panels look identical on every machine and
inside GitHub, where web fonts cannot load.

Fonts in glyphs.json (all SIL Open Font License):
  ui5 ui6 ui7     Chakra Petch 500 / 600 / 700   technical UI lettering
  out4 out5 out6  Outfit 400 / 500 / 600         clean geometric sans
  sign            Audiowide (letters, digits, hyphen only)   neon tubing
  signb           Monoton   (letters, digits, hyphen only)   retro marquee
  in4 in5 in6 in7 Inter 400 to 700               neutral UI lettering
  mono4 mono7     JetBrains Mono 400 / 700       terminals, code, command-line tools
  wd5 wd7 wt4 wt6 Wix Madefor Display 500 / 700, Text 400 / 600   calm editorial sans (no kerning data)

Rules that keep panels working on GitHub:
  - one self-contained .svg per panel, referenced from the README by relative path
  - CSS animations inside <style> only; no scripts, no external files, no web fonts
  - draw the finished state as the base attributes and animate *from* hidden,
    so a viewer with reduced motion (or a static renderer) still sees everything
  - blur filters go on a wrapper group that has no transform
  - animate opacity, transform and stroke-dashoffset only; never animate a blur

Frame rate: the owner requires 60 fps or more. Show panels in the README as
animated .svg files with a plain <img> tag; the browser then draws them at the
screen's refresh rate. Never ship GIFs as the README art: a GIF tops out around
20 fps and looks sluggish. Measure with perf.py before pushing.

Build panels on Loop, below: one timeline of a fixed length that plays the
entrance, runs the scene, fades out and starts again. Every repeating effect
inside such a panel should have a period that divides the loop length.
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
    label = label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
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


EASE = "cubic-bezier(.2,.8,.2,1)"


class Loop:
    """One looping timeline for a whole panel. Times are in seconds from the start of the loop.

    Build the content with enter / show / scene / typed / grow, pass it through wrap() so it
    fades out just before the loop restarts, and add "".join(loop.css) to the panel style.
    Everything is drawn in its finished state and animated from hidden, so reduced motion
    still shows the complete picture.
    """

    def __init__(self, t, seconds, out=0.5):
        self.t, self.L, self.out, self.css, self.n = t, seconds, out, [], 0

    def kf(self, stops, prefix="k"):
        """@keyframes from [(seconds, 'css declarations'), ...]; returns the name."""
        self.n += 1
        name, pts = f"{prefix}{self.n}", []
        for s, css in stops:
            p = round(max(0.0, min(100.0, 100 * s / self.L)), 2)
            if pts and p <= pts[-1][0]:
                if css == pts[-1][1]:
                    continue
                p = round(min(100.0, pts[-1][0] + 0.01), 2)
            pts.append((p, css))
        self.css.append(f"@keyframes {name}{{" + "".join(f"{f2(p)}%{{{c}}}" for p, c in pts) + "}")
        return name

    def anim(self, name, extra=""):
        return f'style="{extra}animation:{name} {self.L}s linear infinite"'

    def enter(self, content, at, dx=0, dy=12, scale=1, dur=0.6, origin=None):
        """Content that arrives at `at`: fades in while moving from (dx, dy) and growing from `scale`.
        origin=(x, y) is the point it scales about."""
        hid = f"opacity:0;transform:translate({dx}px,{dy}px) scale({scale})"
        vis = "opacity:1;transform:translate(0px,0px) scale(1)"
        name = self.kf([(0, hid), (at, hid + f";animation-timing-function:{EASE}"), (at + dur, vis), (self.L, vis)], "e")
        o = f"transform-origin:{origin[0]}px {origin[1]}px;" if origin else ""
        return f"<g {self.anim(name, o)}>{content}</g>"

    def show(self, a, b=None, hi=1, fade=0.25):
        """Style attribute: appear at a, and vanish at b if given."""
        stops = [(0, "opacity:0"), (a, "opacity:0"), (a + fade, f"opacity:{hi}")]
        stops += [(b, f"opacity:{hi}"), (b + fade, "opacity:0"), (self.L, "opacity:0")] if b is not None else [(self.L, f"opacity:{hi}")]
        return self.anim(self.kf(stops, "s"))

    def scene(self, a, b, content, still=False, dx=22):
        """A group on screen from a to b, sliding in and out. still: the one shown when motion is off."""
        hid = f"opacity:0;transform:translateX({dx}px)"
        vis = "opacity:1;transform:translateX(0px)"
        name = self.kf([(0, hid), (a, hid + f";animation-timing-function:{EASE}"), (a + 0.5, vis), (b - 0.35, vis),
                        (b, f"opacity:0;transform:translateX({-dx}px)"), (self.L, f"opacity:0;transform:translateX({-dx}px)")], "c")
        return f'<g opacity="{1 if still else 0}" {self.anim(name)}>{content}</g>'

    def typed(self, s, x, y, font, size, fill, back, a, b):
        """Text revealed left to right between a and b. back must be the solid colour behind it."""
        w = self.t.width(s, font, size) + 4
        name = self.kf([(0, "transform:scaleX(1)"), (a, f"transform:scaleX(1);animation-timing-function:steps({len(s)},end)"),
                        (b, "transform:scaleX(0)"), (self.L, "transform:scaleX(0)")], "t")
        return (self.t.text(s, x, y, font, size, fill)
                + f'<g transform="translate({x - 2 + w:.0f} {y - size:.0f})"><rect x="{-w:.0f}" width="{w:.0f}" height="{size * 1.45:.0f}" '
                  f'fill="{back}" transform="scale(0 1)" {self.anim(name)}/></g>')

    def grow(self, x, y, w, h, fill, a, b, rx=3):
        """A bar that grows from its left end between a and b."""
        name = self.kf([(0, "transform:scaleX(0)"), (a, f"transform:scaleX(0);animation-timing-function:{EASE}"),
                        (b, "transform:scaleX(1)"), (self.L, "transform:scaleX(1)")], "g")
        return f'<g transform="translate({x} {y})"><rect width="{w}" height="{h}" rx="{rx}" fill="{fill}" {self.anim(name)}/></g>'

    def travel(self, pts, a, b, content, hold=0.0):
        """Moves content (drawn around 0,0) through the points at constant speed between a and b, then fades it."""
        seg = [0] + [((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2) ** 0.5 for p, q in zip(pts, pts[1:])]
        total, acc = sum(seg) or 1, 0
        at = lambda p, o: f"transform:translate({f2(p[0])}px,{f2(p[1])}px);opacity:{o}"
        stops = [(0, at(pts[0], 0)), (max(a - 0.2, 0), at(pts[0], 0))]
        for p, d in zip(pts, seg):
            acc += d
            stops.append((a + (b - a) * acc / total, at(p, 1)))
        stops += [(b + hold, at(pts[-1], 1)), (b + hold + 0.25, at(pts[-1], 0)), (self.L, at(pts[-1], 0))]
        return f'<g opacity="0" {self.anim(self.kf(stops, "m"))}>{content}</g>'

    def wrap(self, body):
        """Fades everything out just before the loop restarts, so the entrance can play again."""
        name = self.kf([(0, "opacity:1"), (self.L - self.out - 0.1, "opacity:1"), (self.L - 0.1, "opacity:0"), (self.L, "opacity:0")], "w")
        return f"<g {self.anim(name)}>{body}</g>"
