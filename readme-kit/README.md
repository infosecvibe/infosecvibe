# README art kit

Helpers for building animated panels for a repository README: lettering drawn as outlines, glow, neon tubing, diagram boxes, moving connectors, and a looping timeline. Python standard library only.

- `kit.py`: the helpers, with the rules that keep panels working on GitHub at the top of the file. `Loop` is the timeline every GIF panel is built on.
- `starter.py`: a small banner built on `Loop`. Copy it to begin a new project's art.
- `capture.py`: turns an animated panel into a looping GIF, frame by frame.
- `glyphs.json`: letter outlines for Chakra Petch, Outfit, Inter, Audiowide and Monoton (all SIL Open Font License)

## The standard a project README is held to

Every picture in the README moves and is drawn for the project. No still screenshots and no screenshot slideshows in the README itself; real screenshots belong in a linked gallery.

A full set is six panels and a divider:

| Panel | What it is |
|---|---|
| `hero` | The name with a glow, one plain sentence, three small tags, and one moving picture of what the project does |
| `demo` | A window with the steps listed down the side and each step acted out in turn: text types itself, bars fill, an answer gets picked |
| `devices` | Only if it runs on more than one kind of screen: each device drawn with a different live screen |
| `features` | Tiles whose icons draw themselves, lighting up one after another |
| `how-it-works` | The real architecture as boxes and connectors, with a light tracing two or three named requests and a caption for each |
| `security` or similar | One more story the project has to tell, shown as a request moving through stages |
| `divider` | A thin line with a light running along it, between sections |

Rules for how they move:

1. **Entrance, scene, fade, repeat.** Build each panel on `kit.Loop`. Things arrive one after another in the first two seconds, the scene runs, `wrap()` fades it out, and it starts again. A GIF captured this way replays the entrance on every loop.
2. **Periods divide the loop.** Anything that repeats inside a panel (orbits, blinking dots, travelling dashes) needs a period that divides the loop length exactly, or the GIF jumps where it restarts.
3. **Keep the backdrop still.** Glows and gradients stay put; only small things move. A blurred shape that pulses, or a large shape that drifts, multiplies the GIF's size.
4. **One family, own identity.** Dark panel, 16 px corners, hairline frame, Outfit lettering, a soft glow behind the name. Colours and the hero picture come from the project itself.
5. **Plain words.** Captions say what happens in the project's own terms. Numbers shown in a demo are labelled as examples.

## Putting it in a README

The GitHub phone app can show a broken-image icon for animated SVGs, so the README shows GIFs:

```bash
python3 capture.py hero.svg . --loop 16 --start 0 --fps 20 --gif --bg transparent
```

- `--start 0` keeps the entrance in the loop. `--bg transparent` keeps the rounded corners see-through, so the panel sits on GitHub's light and dark themes alike.
- Needs Playwright, Google Chrome and ffmpeg. Install gifsicle as well (`npm i gifsicle`); without it a transparent GIF is many times larger.
- Aim for under about 1.5 MB a panel and under 4 MB for the hero. If a panel is heavier, something large is changing every frame (see rule 3).
- Reference each GIF with a plain image tag: `<img src="docs/readme-art/hero.gif" width="100%" alt="...">`. Write the alt text as a full description of the panel.

To use the kit in another repository, copy `kit.py`, `capture.py` and a `glyphs.json` trimmed to the fonts used into a folder such as `docs/readme-art/`, write a `build.py` beside them that composes the panels, and commit the `.svg` sources next to the `.gif` files. The profile page in this repository is built the same way by `scripts/build.py`.
