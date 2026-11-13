# README art kit

Helpers for building animated SVG panels for a repository README: lettering drawn as outlines, glow, neon tubing, diagram boxes and moving connectors. Python standard library only.

- `kit.py`: the helpers, with the rules that keep panels working on GitHub at the top of the file
- `glyphs.json`: letter outlines for Chakra Petch, Outfit, Inter, Audiowide and Monoton (all SIL Open Font License)

To use it in another repository, copy both files into a folder such as `docs/readme-art/`, write a small `build.py` beside them that composes the panels for that project, and reference the generated `.svg` files from the README by relative path. The profile page in this repository is built the same way by `scripts/build.py`.
