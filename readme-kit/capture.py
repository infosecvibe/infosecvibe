#!/usr/bin/env python3
"""Turns an animated .svg or .html panel into a looping .gif (--gif) and/or .webp (--webp).

    python3 capture.py panel.svg out_dir --loop 16 --start 0 --fps 20 --gif --bg transparent

Why: the GitHub phone app shows a broken-image icon for some animated SVG setups,
while ordinary image files always load. Capture the panel once and reference the
.gif from the README with a plain <img>.

How: the page's CSS animations are paused and stepped frame by frame, so the
result is smooth and loops exactly.

  --start 0         for a panel built on kit.Loop: the entrance is part of the loop
                    and replays every time. (The default, --start = --loop, skips
                    one-off entrance animations instead, which leaves a GIF with no intro.)
  --bg transparent  keeps the panel's rounded corners see-through, so it sits on
                    GitHub's light and dark themes alike. Any other value is a corner colour.
  --fps 20          GIF frame times are whole hundredths of a second, so 20 or 25 play evenly.

Needs: Playwright (pip install playwright), Google Chrome and ffmpeg. If gifsicle is
installed (npm i gifsicle, or your package manager) the GIF is also optimised with it,
which matters a lot with --bg transparent; --lossy 0 keeps that step lossless.
"""
import argparse, asyncio, pathlib, shutil, subprocess, tempfile


async def frames(src, tmp, loop, start, fps, scale, width, bg):
    from playwright.async_api import async_playwright
    src = pathlib.Path(src).resolve()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=shutil.which("google-chrome") or shutil.which("chromium"), args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": width, "height": 800}, device_scale_factor=scale)
        await pg.goto(src.as_uri())  # opened as a file, so a panel may reference local images
        el = await pg.query_selector("svg" if src.suffix == ".svg" else "#panel")
        clear = bg == "transparent"
        if not clear:
            await pg.evaluate("c => { document.documentElement.style.background = c; }", bg)  # corner colour
        await pg.wait_for_timeout(300)
        n = round(loop * fps)
        for i in range(n):
            t = (start + i / fps) * 1000
            await pg.evaluate("t => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t; })", t)
            await el.screenshot(path=f"{tmp}/f{i:04d}.png", omit_background=clear)
        await b.close()
        return n


def main():
    a = argparse.ArgumentParser()
    a.add_argument("src"); a.add_argument("out_dir")
    a.add_argument("--loop", type=float, required=True); a.add_argument("--start", type=float, default=None)
    a.add_argument("--fps", type=int, default=15); a.add_argument("--scale", type=float, default=1.5)
    a.add_argument("--width", type=int, default=840); a.add_argument("--name", default=None)
    a.add_argument("--bg", default="#000000"); a.add_argument("--colors", type=int, default=128); a.add_argument("--lossy", type=int, default=35)
    a.add_argument("--quality", type=int, default=82); a.add_argument("--gif", action="store_true"); a.add_argument("--webp", action="store_true")
    o = a.parse_args()
    start = o.loop if o.start is None else o.start
    name = o.name or pathlib.Path(o.src).stem
    out = pathlib.Path(o.out_dir); out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        n = asyncio.run(frames(o.src, tmp, o.loop, start, o.fps, o.scale, o.width, o.bg))
        ff = ["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(o.fps), "-i", f"{tmp}/f%04d.png"]
        if o.webp:
            subprocess.run(ff + ["-c:v", "libwebp_anim", "-lossless", "0", "-q:v", str(o.quality), "-compression_level", "6", "-loop", "0",
                                 str(out / f"{name}.webp")], check=True)
        if o.gif:
            clear = o.bg == "transparent"
            gif = str(out / f"{name}.gif")
            subprocess.run(ff + ["-vf", f"split[a][b];[a]palettegen=max_colors={o.colors}:stats_mode=diff{':reserve_transparent=1' if clear else ''}[p];"
                                        f"[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle{':alpha_threshold=128' if clear else ''}", gif], check=True)
            gs = shutil.which("gifsicle")
            if gs:  # two passes: lossy compression only works well on an already optimised file
                subprocess.run([gs, "-O3", "--no-warnings", "-b", gif], check=True)
                if o.lossy:
                    subprocess.run([gs, "-O3", "--no-warnings", f"--lossy={o.lossy}", "-b", gif], check=True)
            elif clear:
                print("gifsicle not found: the transparent GIF is not optimised and will be very large")
    for f in sorted(out.glob(f"{name}.*")):
        if f.suffix in (".webp", ".gif"):
            print(f"{f.name}: {n} frames, {f.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
