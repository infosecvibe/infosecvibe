#!/usr/bin/env python3
"""A starting point for a project banner built on kit.Loop. Copy it, rename things, change the picture.

    python3 starter.py                      # writes hero.svg next to this file
    python3 capture.py hero.svg . --loop 12 --start 0 --fps 20 --gif --bg transparent

The banner plays an entrance, runs for a while, fades and starts again, so the GIF
repeats the entrance every loop. Every repeating effect has a period that divides
the loop length (12 s here: 1, 2, 3, 4, 6 and 12 all work).
"""
import pathlib

from kit import EASE, GLYPHS, Loop, Type, blur, flow, panel, surface

HERE = pathlib.Path(__file__).resolve().parent
BG, GLASS, LINE = "#070A14", "#151B2E", "#27304A"
A, B = "#0A84FF", "#64D2FF"          # take these from the project's own theme
INK, INK2, SOFT = "#FFFFFF", "#98A1BC", "#D6DBEE"
NAME, KIND = "Nova", "What kind of thing it is"
LINES = ["One plain sentence about what it does,", "split over two short lines."]
CHIPS = ["Built with X", "Does Y", "Runs on Z"]


def build():
    W, H, L = 840, 400, 12
    t = Type()
    lp = Loop(t, L)
    back = f'<circle cx="660" cy="140" r="260" fill="url(#glow)"/>'
    clip, base = surface(W, H, "url(#bg)", LINE, extra=back)
    c, css = [], ""

    # the name: a glow fades in behind it while the letters rise one by one
    c.append(lp.enter(f'<g filter="url(#halo)" opacity=".6">{t.text(NAME, 44, 150, "out6", 92, A)}</g>', 0.5, dy=0, dur=1.4))
    c.append(t.text(NAME, 44, 150, "out6", 92, INK, cls={i: f"r{i}" for i in range(len(NAME))}))
    for i in range(len(NAME)):
        hid, at = "opacity:0;transform:translateY(-300px)", 0.15 + i * 0.09   # glyph units, y points up
        name = lp.kf([(0, hid), (at, hid + f";animation-timing-function:{EASE}"), (at + 0.7, "opacity:1;transform:translateY(0px)"),
                      (L, "opacity:1;transform:translateY(0px)")], "r")
        css += f".r{i}{{animation:{name} {L}s linear infinite}}"
    c.append(lp.enter(t.text(KIND, 48, 188, "out4", 24, INK2, track=1.3), 0.9, dy=8))
    c.append(lp.enter("".join(t.text(s, 48, 240 + i * 22, "out4", 15.5, SOFT) for i, s in enumerate(LINES)), 1.2, dy=8))
    x = 48
    for i, word in enumerate(CHIPS):
        w = t.width(word, "out5", 12) + 30
        c.append(lp.enter(f'<rect x="{x}" y="294" width="{w:.0f}" height="26" rx="13" fill="{GLASS}" stroke="{LINE}"/>'
                          f'<circle cx="{x + 13}" cy="307" r="3" fill="{B}"/>' + t.text(word, x + 22, 311.5, "out5", 12, SOFT), 1.5 + i * 0.14, dy=10, dur=0.5))
        x += w + 12

    # the picture: replace this with one moving picture of what the project does
    for i, label in enumerate(("In", "Work", "Out")):
        bx = 470 + i * 120
        c.append(lp.enter(f'<rect x="{bx}" y="160" width="90" height="76" rx="12" fill="{GLASS}" stroke="{LINE}"/>'
                          + t.text(label, bx + 45, 204, "out6", 15, INK, anchor="middle"), 1.0 + i * 0.25, dy=16))
        if i:
            c.append(lp.enter(flow(f"M{bx - 28} 198H{bx - 3}", B, speed=1), 1.8, dy=0))

    defs = (clip + f'<radialGradient id="bg" cx="100%" cy="0%" r="95%"><stop offset="0" stop-color="#0B2C66"/><stop offset=".45" stop-color="{BG}"/>'
            f'<stop offset="1" stop-color="#03040A"/></radialGradient>'
            f'<radialGradient id="glow"><stop offset="0" stop-color="{A}" stop-opacity=".2"/><stop offset="1" stop-color="{A}" stop-opacity="0"/></radialGradient>'
            + blur("halo", 15, 70) + t.defs())
    body = base + lp.wrap("".join(c))          # wrap() before joining lp.css: it adds the fade-out keyframes
    css += ".flow{animation:flow 1s linear infinite}@keyframes flow{to{stroke-dashoffset:-20}}" + "".join(lp.css)
    return panel(W, H, f"{NAME}. {' '.join(LINES)}", css, defs, body)


if __name__ == "__main__":
    (HERE / "hero.svg").write_text(build())
    print("built hero.svg")
