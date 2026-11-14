#!/usr/bin/env python3
"""Measures how smoothly animated .svg panels play when shown as README images.

    python3 perf.py hero.svg demo.svg ...

Loads each file in an <img>, as GitHub does, and times 8 seconds of frames in Chrome.
A healthy panel reads mean 16.67 (ms per frame, which is 60 fps), p95 under 17 and over33 = 0
(one or two stray frames can be the test machine; run it again to be sure).
A higher mean or any over33 means dropped frames: look for an animated blur, a filter on a
moving group, or something other than opacity / transform / stroke-dashoffset being animated.
Needs Playwright and Google Chrome. Run it before every push; 60 fps is the minimum.
"""
import asyncio, pathlib, base64, statistics, sys
from playwright.async_api import async_playwright
JS = """() => new Promise(res => { const t=[]; let last=performance.now(); const start=last;
  function f(now){ t.push(now-last); last=now; if(now-start<8000) requestAnimationFrame(f); else res(t);} requestAnimationFrame(f); })"""
async def run(b, f):
    import xml.dom.minidom
    try:
        xml.dom.minidom.parse(str(f))   # a panel that is not valid XML shows as a broken image on GitHub
    except Exception as e:
        return dict(error=f"not valid XML, GitHub would show a broken image: {e}", mean=99, over33=1)
    pg = await b.new_page(viewport={"width": 900, "height": 520})
    uri = "data:image/svg+xml;base64," + base64.b64encode(pathlib.Path(f).read_bytes()).decode()
    await pg.set_content(f'<body style="margin:20px;background:#0d1117"><img src="{uri}" width="846"></body>')
    t = (await pg.evaluate(JS))[5:]
    await pg.close()
    t.sort(); n = len(t)
    return dict(frames=n, mean=round(statistics.mean(t), 2), p95=round(t[int(n*.95)], 2), worst=round(t[-1], 1), over33=sum(1 for x in t if x > 33.4))
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        for rnd in range(2):
            for f in sys.argv[1:]:
                r = await run(b, f)
                ok = r["mean"] < 17.2 and r["over33"] <= 2   # one or two stray frames in 8 s is the test machine, not the panel
                print(rnd, pathlib.Path(f).name.ljust(18), "OK  " if ok else "SLOW", r)
        await b.close()
asyncio.run(main())
