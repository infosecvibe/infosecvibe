#!/usr/bin/env python3
"""A starting point for a new repository's README art. Copy it, pick a theme, change the content.

    python3 starter.py              # writes hero.svg, terminal.svg, features.svg, divider.svg here
    python3 starter.py hunt         # the same content in another preset, to compare moods
    python3 perf.py *.svg           # every panel must say OK (60 fps) before you push

Steps for a real project:
  1. Pick the preset that matches what the repo is for (see themes.py), then replace its accents
     with the project's own colours if it has any.
  2. Fill in the real name, sentence, tags and commands. Check every claim in the code.
  3. Rewrite picture(): one moving picture of what THIS project does. This is the part that
     makes the repo its own; never ship the placeholder.
  4. Add the project's story panels (demo, how-it-works, anything else) on kit.Loop.
"""
import pathlib
import sys

from kit import flow
from panels import divider, features, hero, terminal
from themes import pick

HERE = pathlib.Path(__file__).resolve().parent
KIND = sys.argv[1] if len(sys.argv) > 1 else "study"
TH = pick(KIND)                       # e.g. pick("intel", a="#7C3AED") to use the project's own accent

NAME, WHAT = "Nova", "What kind of thing it is"
LINES = ["One plain sentence about what it does,", "split over two short lines."]
CHIPS = ["Built with X", "Does Y", "Runs on Z"]


def picture(lp, t, th):
    """Placeholder: three boxes joined by moving dashes. Replace with the project's own picture."""
    out = ""
    for i, label in enumerate(("In", "Work", "Out")):
        x = 458 + i * 124
        out += lp.enter(f'<rect x="{x}" y="160" width="92" height="76" rx="12" fill="{th.glass}" stroke="{th.line}"/>'
                        f'<rect x="{x}" y="172" width="3" height="52" rx="1.5" fill="{(th.a, th.b, th.c)[i]}"/>'
                        + t.text(label, x + 47, 204, th.strong, 15, th.ink, anchor="middle"), 1.0 + i * 0.25, dy=16)
        if i:
            out += lp.enter(flow(f"M{x - 30} 198H{x - 3}", th.b, speed=1), 1.9, dy=0)
    return out, "", ""


SCRIPT = [("cmd", "git clone <this repo> && cd nova"), ("bar", "Installing", 1.4), ("cmd", "nova run --example"),
          ("out", "reading example input"), ("ok", "3 items processed"), ("hi", "report written to out/report.html")]
ICON = '<rect x="3" y="5" width="22" height="18" rx="4"/><path d="M8 14l4 4 8-9"/>'
ITEMS = [("First thing it does", ["One short line,", "then another."], ICON, "a"), ("Second thing", ["One short line,", "then another."], ICON, "b"),
         ("Third thing", ["One short line,", "then another."], ICON, "c"), ("Fourth thing", ["One short line,", "then another."], ICON, "a")]

if __name__ == "__main__":
    out = {"hero": hero(TH, NAME, WHAT, LINES, CHIPS, picture)[0],
           "terminal": terminal(TH, "nova", SCRIPT, note="An illustration. Your output will differ.")[0],
           "features": features(TH, ITEMS, "What Nova does: four things.")[0],
           "divider": divider(TH)[0]}
    for name, svg in out.items():
        (HERE / f"{name}.svg").write_text(svg)
    print(f"built {', '.join(out)} in the '{TH.name}' theme")
