# README art kit

Helpers for building animated panels for a repository README: lettering drawn as outlines, glow, neon tubing, diagram boxes, moving connectors, and a looping timeline. Python standard library only.

- `kit.py`: the helpers, with the rules that keep panels working on GitHub at the top of the file. `Loop` is the timeline every GIF panel is built on.
- `starter.py`: a small banner built on `Loop`. Copy it to begin a new project's art.
- `perf.py`: measures a panel's frame rate the way GitHub shows it. Run it before every push.
- `capture.py`: fallback only. Turns a panel into a GIF for places that cannot show SVG. Not for READMEs.
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

0. **60 frames a second or more, always.** The README shows the animated `.svg` files themselves, which the browser draws at the screen's refresh rate. Never use GIFs for README art: a GIF plays at about 20 frames a second and looks laggy. Run `perf.py` on every panel before pushing; each must read `OK`.

1. **Entrance, scene, fade, repeat.** Build each panel on `kit.Loop`. Things arrive one after another in the first two seconds, the scene runs, `wrap()` fades it out, and it starts again. The entrance replays on every loop.
2. **Periods divide the loop.** Anything that repeats inside a panel (orbits, blinking dots, travelling dashes) needs a period that divides the loop length exactly, so the restart is seamless.
3. **Animate only opacity, transform and stroke-dashoffset.** Never animate a blur, and keep blur filters on a group that has no transform. Anything else drops frames.
4. **One family, own identity.** Dark panel, 16 px corners, hairline frame, Outfit lettering, a soft glow behind the name. Colours and the hero picture come from the project itself.
5. **Plain words.** Captions say what happens in the project's own terms. Numbers shown in a demo are labelled as examples.

## Putting it in a README

Reference each panel with a plain image tag pointing at the `.svg`:

```html
<img src="docs/readme-art/hero.svg" width="100%" alt="A full description of the panel">
```

- Plain `<img>` only. Do not wrap animated SVGs in a `<picture>` tag: the GitHub phone app showed a broken-image icon for that.
- Before pushing: `python3 perf.py docs/readme-art/*.svg`. Every line must say `OK` (16.67 ms a frame, nothing over 33 ms).
- Do not commit GIF copies. `capture.py` exists only for places that cannot show SVG at all.

To use the kit in another repository, copy `kit.py`, `perf.py` and a `glyphs.json` trimmed to the fonts used into a folder such as `docs/readme-art/`, write a `build.py` beside them that composes the panels, and commit the generated `.svg` files. The profile page in this repository is built the same way by `scripts/build.py`.
