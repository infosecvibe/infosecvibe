"""Themes: one look per kind of project, so READMEs feel like a family without being copies.

A Theme is a palette, a lettering choice and a backdrop. Pick the preset that matches what the
repository is for, then override colours with the project's own (its stylesheet, its icon):

    from themes import pick
    th = pick("hunt")                           # threat hunting, detection
    th = pick("study", a="#38BDF8", c="#8B5CF6")  # same family, the project's own accents

Presets
  study      learning and practice apps        blue light, floating dust            Outfit
  hunt       threat hunting, detection         crimson radar on graphite, steel     Chakra Petch
  intel      threat intel, OSINT, analysis     violet link graph with signals       Outfit
  forensics  DFIR, timelines, evidence         amber ruler with a scan line         Chakra Petch
  tool       command-line tools, utilities     graphite grid with lit cells         JetBrains Mono
  data       finance, calculators, reports     teal ledger grid                     Outfit
  lamp       anything that suits a warm, calm mood (study, reading, notes, writing)   lamp light, lit windows   Outfit

Rules: the preset decides the mood, the project decides the picture. The hero's moving picture
is always drawn for the project itself (panels.hero takes it as a function). Two repos that are
siblings may share a preset and differ in accents. Never give two unrelated repos the same
preset and the same picture.
"""
import math
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Theme:
    name: str
    bg0: str            # colour of the glow in the top-right corner
    bg: str             # main background
    bg1: str            # darkest edge
    panel: str          # flat panel background (demo, features, terminal)
    glass: str          # cards and tiles
    stage: str          # inside windows and screens
    line: str           # hairlines
    a: str              # primary accent
    b: str              # highlight (lighter, for small bright details)
    c: str              # secondary accent
    ink: str = "#FFFFFF"
    ink2: str = "#98A1BC"
    soft: str = "#D6DBEE"
    ok: str = "#30D158"
    warn: str = "#FF9F0A"
    bad: str = "#FF6961"
    display: str = "out6"   # the project name
    strong: str = "out6"    # titles
    medium: str = "out5"
    text: str = "out4"
    mono: str = "mono4"
    mono_bold: str = "mono7"
    track: float = 0        # extra letter spacing for the name
    backdrop: str = "dust"  # dust | radar | graph | scan | grid | lamp

    def fonts(self):
        return {self.display, self.strong, self.medium, self.text, self.mono, self.mono_bold}


PRESETS = {
    "study": Theme("study", "#0B2C66", "#070A14", "#03040A", "#0B0F1D", "#151B2E", "#0A0E1B", "#27304A",
                   "#0A84FF", "#64D2FF", "#5E5CE6"),
    "hunt": Theme("hunt", "#4A0E18", "#0B0A0C", "#040304", "#0E0D10", "#1A181D", "#0A090B", "#2A262E",
                  "#F43F5E", "#FDA4AF", "#94A3B8", ink2="#9A95A0", soft="#DDD9E0", ok="#E2E8F0", warn="#FDBA74", bad="#F43F5E",
                  display="ui7", strong="ui6", medium="ui6", text="ui5", track=1.5, backdrop="radar"),
    "intel": Theme("intel", "#2A1466", "#0A0714", "#040309", "#0E0A1C", "#1A1430", "#0B0818", "#2E2550",
                   "#A78BFA", "#22D3EE", "#F472B6", ink2="#A39CC2", soft="#DDD8F2", backdrop="graph"),
    "forensics": Theme("forensics", "#4A2A08", "#0C0906", "#050302", "#120E09", "#221A10", "#0E0A06", "#3D2F1C",
                       "#F59E0B", "#FDE68A", "#38BDF8", ink2="#B0A38E", soft="#EDE3D2",
                       display="ui7", strong="ui6", medium="ui6", text="ui5", track=1.5, backdrop="scan"),
    "tool": Theme("tool", "#2A2F3A", "#0A0B0E", "#030304", "#0E1014", "#1A1D24", "#0B0C10", "#2C313C",
                  "#F97316", "#FDBA74", "#94A3B8", ink2="#9AA1AE", soft="#DADDE4",
                  display="mono7", strong="mono7", medium="mono7", text="mono4", track=-2, backdrop="grid"),
    "data": Theme("data", "#064E48", "#060D0D", "#020505", "#091312", "#11221F", "#07100F", "#1D3B37",
                  "#2DD4BF", "#99F6E4", "#818CF8", ink2="#8FAAA6", soft="#D3E8E4", backdrop="grid"),
    "lamp": Theme("lamp", "#5A3A14", "#13100D", "#080604", "#15120E", "#241E17", "#1B1611", "#3A3026",
                  "#F2B66D", "#FFDCA8", "#E58E73", ink="#F6EEDF", ink2="#A89B88", soft="#DDD0BC", ok="#A8C69A", backdrop="lamp"),
}


def pick(kind, **overrides):
    """A preset by name, with any fields replaced (usually a, b, c from the project's own colours)."""
    return replace(PRESETS[kind], **overrides)


def base_defs(th):
    """Gradients every themed panel can use: appbg (hero background), gb / gi (colour glows), pg (progress)."""
    return (f'<radialGradient id="appbg" cx="100%" cy="0%" r="95%"><stop offset="0" stop-color="{th.bg0}"/>'
            f'<stop offset=".45" stop-color="{th.bg}"/><stop offset="1" stop-color="{th.bg1}"/></radialGradient>'
            f'<radialGradient id="gb"><stop offset="0" stop-color="{th.a}" stop-opacity=".2"/><stop offset="1" stop-color="{th.a}" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="gi"><stop offset="0" stop-color="{th.c}" stop-opacity=".18"/><stop offset="1" stop-color="{th.c}" stop-opacity="0"/></radialGradient>'
            f'<linearGradient id="pg"><stop offset="0" stop-color="{th.a}"/><stop offset="1" stop-color="{th.b}"/></linearGradient>')


def backdrop(th, W, H, rng, x0=0, density=1.0):
    """The theme's moving background, drawn behind everything. Returns (svg, css).

    Everything here moves with opacity or transform only, and stays faint so text stays readable.
    x0: keep detail to the right of this x (the hero's text sits on the left).
    """
    glows = (f'<g class="bdA"><circle cx="{W - 180}" cy="{H * 0.35:.0f}" r="260" fill="url(#gb)"/></g>'
             f'<g class="bdB"><circle cx="{W - 370}" cy="{H * 0.85:.0f}" r="220" fill="url(#gi)"/></g>')
    css = (".bdA{animation:bdA 14s ease-in-out infinite alternate}@keyframes bdA{to{transform:translate(-50px,34px)}}"
           ".bdB{animation:bdB 18s ease-in-out infinite alternate}@keyframes bdB{to{transform:translate(60px,-40px)}}"
           ".dust{animation:dust 8s ease-in-out infinite}@keyframes dust{0%,100%{opacity:.1;transform:translateY(5px)}50%{opacity:.7;transform:translateY(-5px)}}")

    def dust(n):
        out = ""
        for _ in range(round(n * density)):
            x, y, r = rng.randint(x0, W - 10), rng.randint(14, H - 14), rng.choice([0.8, 1, 1.3, 1.6])
            out += (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{rng.choice([th.a, th.b, th.c, th.ink])}" class="dust" '
                    f'style="animation-duration:{rng.choice([4, 6, 8])}s;animation-delay:-{rng.uniform(0, 8):.1f}s"/>')
        return out

    kind = th.backdrop
    if kind == "radar":
        cx, cy, T = round(W * 0.72), round(H * 0.5), 6
        out = glows + f'<g fill="none" stroke="{th.a}" stroke-opacity=".13">' + "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>' for r in (60, 120, 180, 240, 300))
        out += f'<path d="M{cx - 300} {cy}H{cx + 300}M{cx} {cy - 300}V{cy + 300}" stroke-opacity=".08"/></g>'
        wedge = ""
        for i in range(9):   # a fading fan behind the leading edge
            a0, a1 = math.radians(-i * 5), math.radians(-(i + 1) * 5)
            wedge += (f'<path d="M0 0L{300 * math.cos(a0):.1f} {300 * math.sin(a0):.1f}A300 300 0 0 0 {300 * math.cos(a1):.1f} {300 * math.sin(a1):.1f}z" '
                      f'fill="{th.a}" opacity="{0.16 * (1 - i / 9):.3f}"/>')
        out += (f'<g transform="translate({cx} {cy})"><g class="sweep">{wedge}<path d="M0 0H300" stroke="{th.b}" stroke-opacity=".5" stroke-width="1.2"/></g></g>')
        for _ in range(round(8 * density)):
            ang, rad = rng.uniform(0, 360), rng.uniform(50, 250)
            bx, by = cx + rad * math.cos(math.radians(ang)), cy + rad * math.sin(math.radians(ang))
            if not (x0 <= bx <= W - 8 and 8 <= by <= H - 8):
                continue
            out += (f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="{rng.choice([2, 2.5, 3])}" fill="{rng.choice([th.b, th.b, th.c])}" class="blip" '
                    f'style="animation-delay:{ang / 360 * T - T:.2f}s"/>')
        css += (f".sweep{{animation:sweep {T}s linear infinite}}@keyframes sweep{{to{{transform:rotate(360deg)}}}}"
                f".blip{{animation:blip {T}s linear infinite}}@keyframes blip{{0%{{opacity:1}}45%{{opacity:.12}}100%{{opacity:.12}}}}")
        return out + dust(8), css
    if kind == "graph":
        pts = [(rng.randint(max(x0, 20), W - 20), rng.randint(20, H - 20)) for _ in range(round(22 * density))]
        out, k = glows, 0
        for i, p in enumerate(pts):
            for q in pts[i + 1:]:
                d = math.dist(p, q)
                if 40 < d < 150:
                    k += 1
                    out += f'<path d="M{p[0]} {p[1]}L{q[0]} {q[1]}" stroke="{th.a}" stroke-opacity=".16"/>'
                    if k % 4 == 0:   # a signal runs along some links
                        out += (f'<path d="M{p[0]} {p[1]}L{q[0]} {q[1]}" stroke="{th.b}" stroke-opacity=".6" stroke-width="1.4" stroke-linecap="round" '
                                f'pathLength="100" stroke-dasharray="2 100" class="sig" style="animation-duration:{rng.choice([3, 4, 5])}s;animation-delay:-{rng.uniform(0, 5):.1f}s"/>')
        for p in pts:
            out += (f'<circle cx="{p[0]}" cy="{p[1]}" r="{rng.choice([2, 2.5, 3.5])}" fill="{rng.choice([th.a, th.a, th.b, th.c])}" class="dust" '
                    f'style="animation-duration:{rng.choice([4, 6, 8])}s;animation-delay:-{rng.uniform(0, 8):.1f}s"/>')
        css += ".sig{animation:sig 4s linear infinite}@keyframes sig{from{stroke-dashoffset:2}to{stroke-dashoffset:-100}}"
        return out, css
    if kind == "scan":
        y = H - 26
        ticks = "".join(f'<path d="M{x} {y}v{-12 if (x - x0) % 60 == 0 else -5}"/>' for x in range(x0 - x0 % 12, W, 12))
        out = (glows + f'<g stroke="{th.a}" stroke-opacity=".3">{ticks}<path d="M{x0} {y}H{W}" stroke-opacity=".2"/></g>'
               f'<g class="scan"><rect x="-90" width="90" height="{H}" fill="url(#scang)"/><rect x="-1.5" width="1.5" height="{H}" fill="{th.b}" opacity=".45"/></g>')
        css += f".scan{{animation:scan 9s linear infinite}}@keyframes scan{{from{{transform:translateX({x0}px)}}to{{transform:translateX({W + 100}px)}}}}"
        return out + dust(14), css
    if kind == "grid":
        step = 28
        lines = "".join(f'<path d="M{x} 0V{H}"/>' for x in range(x0 - x0 % step, W, step)) + "".join(f'<path d="M{x0} {y}H{W}"/>' for y in range(step, H, step))
        out = f'<g stroke="{th.ink}" stroke-opacity=".045">{lines}</g>' + glows
        for _ in range(round(12 * density)):
            gx, gy = rng.randrange(x0 - x0 % step, W - step, step), rng.randrange(0, H - step, step)
            out += (f'<rect x="{gx + 1}" y="{gy + 1}" width="{step - 2}" height="{step - 2}" rx="3" fill="{rng.choice([th.a, th.a, th.c])}" class="cell" '
                    f'style="animation-duration:{rng.choice([5, 7, 9])}s;animation-delay:-{rng.uniform(0, 9):.1f}s"/>')
        css += ".cell{animation:cell 7s ease-in-out infinite}@keyframes cell{0%,100%{opacity:0}50%{opacity:.16}}"
        return out, css
    if kind == "lamp":   # a far row of lit windows low on the horizon, and slow motes in the lamp light
        out, hy, x = glows, H - 34, x0
        while x < W - 8:
            if rng.random() < 0.6:
                out += (f'<rect x="{x}" y="{hy - rng.choice([0, 3, 6])}" width="2.5" height="3.5" rx=".6" fill="{rng.choice([th.a, th.b, th.b])}" class="win" '
                        f'style="animation-duration:{rng.choice([5, 7, 9])}s;animation-delay:-{rng.uniform(0, 9):.1f}s"/>')
            x += rng.choice([7, 9, 12, 16])
        out += f'<path d="M{x0} {hy + 8}H{W}" stroke="{th.a}" stroke-opacity=".18"/>'
        css += ".win{animation:win 7s ease-in-out infinite}@keyframes win{0%,100%{opacity:.75}50%{opacity:.2}}"
        return out + dust(26), css
    return glows + dust(34), css


def backdrop_defs(th):
    """Extra <defs> the backdrops need (only the scan line today)."""
    return (f'<linearGradient id="scang"><stop offset="0" stop-color="{th.a}" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{th.a}" stop-opacity=".16"/></linearGradient>')
