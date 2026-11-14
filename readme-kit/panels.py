"""Ready-made panels that take a Theme, so a new README starts from content, not from drawing code.

    hero(th, name, kind, lines, chips, picture)   the banner; picture is a function you write
    terminal(th, title, script)                    a terminal that types real commands
    features(th, items, label)                     tiles whose icons draw themselves
    divider(th)                                    a thin line with a light running along it

Each returns (svg_text, loop_seconds). They are built on kit.Loop: entrance, scene, fade, repeat.
Show the .svg in the README with a plain <img> tag and check it with perf.py (60 fps or more).
"""
import random

from kit import EASE, GLYPHS, Loop, Type, blur, f2, panel, surface
from themes import backdrop, backdrop_defs, base_defs

S = 'fill="none" stroke-linecap="round" stroke-linejoin="round"'
FLOW = ".flow{animation:flow 1s linear infinite}@keyframes flow{to{stroke-dashoffset:-20}}"


def kf(name, stops):
    """@keyframes from [(percent, 'css declarations'), ...] for effects with their own short period."""
    return f"@keyframes {name}{{" + "".join(f"{f2(p)}%{{{css}}}" for p, css in stops) + "}"


def tick(x, y, colour, s=1.0, width=2.2, attrs=""):
    """A check mark centred near x, y."""
    return (f'<path d="M{f2(x - 5.5 * s)} {f2(y)}l{f2(4 * s)} {f2(4 * s)} {f2(7 * s)} {f2(-8 * s)}" stroke="{colour}" '
            f'stroke-width="{width}" {S} {attrs}/>')


def cross(x, y, colour, s=1.0, width=2.2, attrs=""):
    """An X centred on x, y."""
    return f'<path d="M{f2(x - 5 * s)} {f2(y - 5 * s)}l{f2(10 * s)} {f2(10 * s)}M{f2(x + 5 * s)} {f2(y - 5 * s)}l{f2(-10 * s)} {f2(10 * s)}" stroke="{colour}" stroke-width="{width}" {S} {attrs}/>'


def finish(lp, W, H, label, defs, base, content, css=""):
    """Wraps the content so it fades before the loop restarts, and assembles the panel."""
    body = base + "\n" + lp.wrap("\n".join(content))   # wrap() adds its keyframes, so it runs before the style is joined
    return panel(W, H, label, css + "".join(lp.css), defs, body)


def window(th, x, y, w, h, title, t, font=None, rx=14):
    """An app or terminal window frame: three dots, a centred title, a hairline under the bar."""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{th.stage}" stroke="{th.line}"/>'
            f'<path d="M{x} {y + 36}H{x + w}" stroke="{th.line}"/>'
            + "".join(f'<circle cx="{x + 22 + i * 18}" cy="{y + 18}" r="5" fill="{col}" opacity=".85"/>' for i, col in enumerate(("#FF5F57", "#FEBC2E", "#28C840")))
            + t.text(title, x + w / 2, y + 22.5, font or th.medium, 12.5, th.ink2, anchor="middle"))


# ------------------------------------------------------------------ hero
def hero(th, name, kind, lines, chips, picture, tag=None, label=None, W=840, H=400, L=16, seed=11, size=92):
    """The banner. Left: the name rising in with a glow, what kind of thing it is, one sentence, three tags.
    Right (x from about 400 to 820): picture(lp, t, th) -> (svg, defs, css), one moving picture of what
    the project does, drawn for this project. Use lp.enter(...) from about 0.7 s so it arrives after the name."""
    t = Type()
    lp = Loop(t, L)
    rng = random.Random(seed)
    back, css = backdrop(th, W, H, rng, x0=380)
    clip, base = surface(W, H, "url(#appbg)", th.line, extra=back)
    c = []
    wx, wy = 44, 150
    k = size / GLYPHS[th.display]["upm"]
    while t.width(name, th.display, size, th.track) > 340 and size > 40:   # long names shrink to fit the text column
        size -= 4
        k = size / GLYPHS[th.display]["upm"]
    c.append(lp.enter(f'<g filter="url(#halo)" opacity=".6">{t.text(name, wx, wy, th.display, size, th.a, track=th.track)}</g>', 0.5, dy=0, dur=1.4))
    c.append(t.text(name, wx, wy, th.display, size, th.ink, track=th.track, cls={i: f"r{i}" for i in range(len(name))}))
    for i in range(len(name)):
        hid, at = f"opacity:0;transform:translateY({-27.6 / k:.0f}px)", 0.15 + i * min(0.09, 0.5 / len(name))
        n = lp.kf([(0, hid), (at, hid + f";animation-timing-function:{EASE}"), (at + 0.7, "opacity:1;transform:translateY(0px)"), (L, "opacity:1;transform:translateY(0px)")], "r")
        css += f".r{i}{{animation:{n} {L}s linear infinite}}"
    # a sheen crosses the name twice per loop
    clipuses, cx = "", 0.0
    f = GLYPHS[th.display]
    for i, ch in enumerate(name):
        if f["g"].get(ch, {}).get("d"):
            clipuses += f'<use href="#{th.display}-{ord(ch):x}" transform="translate({f2(wx + cx * k)} {wy}) scale({k:.5f} {-k:.5f})"/>'
        cx += f["g"].get(ch, f["g"]["?"])["a"] + th.track / k + (f.get("k", {}).get(name[i:i + 2], 0) if i + 1 < len(name) else 0)
    sheen = lp.kf([(0, "transform:translateX(0px)"), (2.4, "transform:translateX(0px)"), (4, "transform:translateX(460px);animation-timing-function:steps(1,end)"),
                   (9.4, "transform:translateX(0px)"), (11, "transform:translateX(460px)"), (L, "transform:translateX(460px)")], "sh")
    c.append(f'<g clip-path="url(#wm)"><g {lp.anim(sheen)}><rect x="-70" y="50" width="46" height="130" fill="url(#sh)" transform="skewX(-18)"/></g></g>')

    ks = 24
    while t.width(kind, th.text, ks, 1.3) > (270 if tag else 340) and ks > 14:   # wide lettering shrinks to fit
        ks -= 1
    sub = t.text(kind, 48, 188, th.text, ks, th.ink2, track=1.3)
    ls = 15.5
    while max(t.width(s, th.text, ls) for s in lines) > 345 and ls > 11:
        ls -= 0.5
    if tag:
        sw = t.width(kind, th.text, ks, 1.3)
        tw = t.width(tag, th.strong, 13) + 24
        sub += (f'<rect x="{48 + sw + 14:.0f}" y="169" width="{tw:.0f}" height="24" rx="12" fill="{th.a}" fill-opacity=".16" stroke="{th.a}"/>'
                + t.text(tag, 48 + sw + 14 + tw / 2, 186, th.strong, 13, th.b, anchor="middle"))
    c.append(lp.enter(sub, 0.9, dy=8))
    c.append(lp.enter("".join(t.text(s, 48, 240 + i * 22, th.text, ls, th.soft) for i, s in enumerate(lines)), 1.2, dy=8))
    x = 48
    for i, word in enumerate(chips):
        w = t.width(word, th.medium, 12) + 30
        c.append(lp.enter(f'<rect x="{x}" y="294" width="{w:.0f}" height="26" rx="13" fill="{th.glass}" stroke="{th.line}"/>'
                          f'<circle cx="{x + 13}" cy="307" r="3" fill="{(th.ink2, th.b, th.c)[i % 3]}" class="blink" style="animation-delay:-{i * 0.5}s"/>'
                          + t.text(word, x + 22, 311.5, th.medium, 12, th.soft), 1.5 + i * 0.14, dy=10, dur=0.5))
        x += w + 12

    art, art_defs, art_css = picture(lp, t, th)
    c.append(art)
    defs = (clip + base_defs(th) + backdrop_defs(th) + blur("halo", 15, 70) + f'<clipPath id="wm">{clipuses}</clipPath>'
            + f'<linearGradient id="sh"><stop offset="0" stop-color="{th.b}" stop-opacity="0"/><stop offset=".5" stop-color="{th.b}"/>'
              f'<stop offset="1" stop-color="{th.b}" stop-opacity="0"/></linearGradient>' + art_defs + t.defs())
    css += FLOW + ".blink{animation:blink 2s ease-in-out infinite}@keyframes blink{50%{opacity:.25}}" + art_css
    return finish(lp, W, H, label or f"{name}. {kind}. {' '.join(lines)}", defs, base, c, css), L


# ------------------------------------------------------------------ terminal
def terminal(th, title, script, note=None, label=None, W=840, prompt="$", size=13.5, speed=0.055):
    """A terminal window that types commands and prints their output, then starts again.

    script is a list of steps:
      ("cmd", "npm ci")                      typed after the prompt, with a moving cursor
      ("out", "text")                        a plain output line
      ("ok", "text")                         an output line with a green tick
      ("hi", "text")                         an output line in the highlight colour
      ("warn", "text")                       an output line in the warning colour
      ("bar", "Installing", 1.6)             a progress bar that fills over that many seconds
      ("gap",)                               an empty line
    Use the project's real commands, and real output wording where you can; label made-up values as examples.
    note: one small line under the window."""
    t = Type()
    LH, x0, top = 23, 50, 86
    adv = GLYPHS[th.mono]["g"]["a"]["a"] * size / GLYPHS[th.mono]["upm"]
    n_lines = len(script)
    H = top + n_lines * LH + (46 if note else 26)
    # timings
    at, plan = 1.0, []
    for step in script:
        kind = step[0]
        if kind == "cmd":
            dur = max(0.45, len(step[1]) * speed)
            plan.append((at, at + dur))
            at += dur + 0.45
        elif kind == "bar":
            plan.append((at, at + step[2]))
            at += step[2] + 0.25
        elif kind == "gap":
            plan.append((at, at))
        else:
            plan.append((at, at))
            at += 0.22
    L = int(at + 3.2) + 1
    lp = Loop(t, L)
    clip, base = surface(W, H, th.panel, th.line)
    win = window(th, 22, 22, W - 44, H - 44 - (20 if note else 0), title, t, th.mono)
    cmds = [i for i, s in enumerate(script) if s[0] == "cmd"]
    css = ".cur{animation:cur 1s steps(1) infinite}@keyframes cur{50%{opacity:0}}"
    for i, step in enumerate(script):
        y = top + i * LH
        a, b = plan[i]
        kind = step[0]
        if kind == "cmd":
            text = step[1]
            w = len(text) * adv
            reveal = lp.kf([(0, "transform:scaleX(1)"), (a, f"transform:scaleX(1);animation-timing-function:steps({len(text)},end)"),
                            (b, "transform:scaleX(0)"), (L, "transform:scaleX(0)")], "t")
            nxt = next((plan[j][0] for j in cmds if j > i), L)   # the cursor stays here until the next command starts
            move = lp.kf([(0, "transform:translateX(0px);opacity:0"), (max(a - 0.5, 0), "transform:translateX(0px);opacity:0"), (max(a - 0.45, 0.01), "transform:translateX(0px);opacity:1"),
                          (a, f"transform:translateX(0px);opacity:1;animation-timing-function:steps({len(text)},end)"), (b, f"transform:translateX({w:.1f}px);opacity:1"),
                          (nxt - 0.5, f"transform:translateX({w:.1f}px);opacity:1"), (nxt - 0.45, f"transform:translateX({w:.1f}px);opacity:0"), (L, f"transform:translateX({w:.1f}px);opacity:0")], "u")
            cx = x0 + adv * 2
            win += (f'<g {lp.show(max(a - 0.5, 0), fade=0.1)}>' + t.text(prompt, x0, y, th.mono_bold, size, th.b) + "</g>"
                    + t.text(text, cx, y, th.mono, size, th.ink)
                    + f'<g transform="translate({cx + w + 1:.1f} {y - size:.0f})"><rect x="{-w - 1:.1f}" width="{w + 2:.1f}" height="{size * 1.5:.0f}" fill="{th.stage}" transform="scale(0 1)" {lp.anim(reveal)}/></g>'
                    + f'<g opacity="0" {lp.anim(move)}><rect x="{cx + 1:.1f}" y="{y - size + 1:.0f}" width="{adv - 1:.1f}" height="{size * 1.25:.0f}" rx="1.5" fill="{th.b}" class="cur"/></g>')
        elif kind == "bar":
            bw = 300
            win += (f'<g {lp.show(a, b + 0.1, fade=0.1)}>' + t.text(step[1], x0 + adv * 2, y, th.mono, size, th.ink2)
                    + f'<rect x="{x0 + adv * (len(step[1]) + 4):.0f}" y="{y - 9}" width="{bw}" height="8" rx="4" fill="{th.glass}"/></g>'
                    + f'<g {lp.show(a, b + 0.1, fade=0.1)}>' + lp.grow(round(x0 + adv * (len(step[1]) + 4)), y - 9, bw, 8, "url(#pg)", a, b, 4) + "</g>"
                    + f'<g {lp.show(b + 0.1, fade=0.1)}>' + tick(x0 + adv * 2 + 6, y - 4.5, th.ok, 0.8, 2) + t.text(step[1] + " done", x0 + adv * 4, y, th.mono, size, th.ink2) + "</g>")
        elif kind != "gap":
            colour = {"out": th.ink2, "ok": th.soft, "hi": th.b, "warn": th.warn}[kind]
            line = t.text(step[1], x0 + adv * (4 if kind == "ok" else 2), y, th.mono, size, colour)
            if kind == "ok":
                line = tick(x0 + adv * 2 + 6, y - 4.5, th.ok, 0.8, 2) + line
            win += f'<g {lp.show(a, fade=0.12)}>{line}</g>'
    c = [lp.enter(win, 0, dy=20, dur=0.8)]
    if note:
        c.append(lp.enter(t.text(note, 26, H - 16, th.text, 11.5, th.ink2), 0.6, dy=0))
    cmd_text = "; ".join(s[1] for s in script if s[0] == "cmd")
    return finish(lp, W, H, label or f"A terminal running: {cmd_text}.", clip + base_defs(th) + t.defs(), base, c, css), L


# ------------------------------------------------------------------ features
def features(th, items, label, cols=4, W=840, L=None):
    """Tiles whose icons draw themselves, then light up one after another.
    items: [(title, [line, line], icon_svg, "a" | "b" | "c")]. icon_svg is stroke art in a 28 x 28 box
    made of <path>, <rect> and <circle> (they get pathLength="1" so they can draw themselves)."""
    t = Type()
    rows = -(-len(items) // cols)
    gap, tw = 12, (W - 44 - 12 * (cols - 1)) / cols
    H = 44 + rows * 100 + (rows - 1) * gap
    L = L or max(12, round(2.6 + len(items) * 1.55 + 1.6))
    lp = Loop(t, L)
    clip, base = surface(W, H, th.panel, th.line)
    c, css = [], ""
    for i, (title, lines, art, key) in enumerate(items):
        colour = getattr(th, key)
        x, y = 22 + (i % cols) * (tw + gap), 22 + (i // cols) * (100 + gap)
        at, lit = 0.2 + i * 0.11, 2.6 + i * 1.55
        draw = lp.kf([(0, "stroke-dashoffset:1"), (at + 0.3, "stroke-dashoffset:1;animation-timing-function:ease-out"), (at + 1.4, "stroke-dashoffset:0"), (L, "stroke-dashoffset:0")], "d")
        css += f".d{i} *{{stroke-dasharray:1;animation:{draw} {L}s linear infinite}}"
        art = art.replace("<path ", '<path pathLength="1" ').replace("<rect ", '<rect pathLength="1" ').replace("<circle ", '<circle pathLength="1" ')
        tile = (f'<rect x="{x:.0f}" y="{y}" width="{tw:.0f}" height="100" rx="12" fill="{th.glass}" stroke="{th.line}"/>'
                f'<g opacity="0" {lp.show(lit, lit + 1.3, fade=0.2)}><rect x="{x:.0f}" y="{y}" width="{tw:.0f}" height="100" rx="12" fill="{colour}" fill-opacity=".1" stroke="{colour}" stroke-width="1.5"/>'
                f'<circle cx="{x + 30:.0f}" cy="{y + 28}" r="22" fill="url(#lit{key})"/></g>'
                f'<g transform="translate({x + 16:.0f} {y + 14})" fill="none" stroke="{colour}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" class="d{i}">{art}</g>'
                + t.text(title, x + 16, y + 62, th.strong, 13.5, th.ink))
        for j, line in enumerate(lines):
            tile += t.text(line, x + 16, y + 78 + j * 14, th.text, 11, th.ink2)
        c.append(lp.enter(tile, at, dy=16, dur=0.55))
    defs = clip + "".join(f'<radialGradient id="lit{k}"><stop offset="0" stop-color="{getattr(th, k)}" stop-opacity=".35"/><stop offset="1" stop-color="{getattr(th, k)}" stop-opacity="0"/></radialGradient>'
                          for k in "abc") + t.defs()
    return finish(lp, W, H, label, defs, base, c, css), L


# ------------------------------------------------------------------ divider
def divider(th, W=840, L=4):
    """A hairline with a light running along it, for between README sections."""
    body = (f'<rect y="4.5" width="{W}" height="1" fill="{th.line}"/>'
            f'<rect class="run" x="-170" y="3.5" width="170" height="3" rx="1.5" fill="url(#g)"/>')
    defs = (f'<linearGradient id="g"><stop offset="0" stop-color="{th.line}"/><stop offset=".6" stop-color="{th.a}"/>'
            f'<stop offset="1" stop-color="{th.b}"/></linearGradient>')
    return panel(W, 10, "", f".run{{animation:run {L}s ease-in-out infinite}}@keyframes run{{to{{transform:translateX({W + 170}px)}}}}", defs, body), L
