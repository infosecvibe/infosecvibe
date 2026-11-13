#!/usr/bin/env python3
"""Builds the animated panels for the infosecvibe profile README.

  assets/city.svg   night city: every tower is a week, every lit window a day
  assets/focus.svg  the four areas of work, as neon signs
  assets/stats.svg  headline numbers

Runs on the Python standard library only. Inside GitHub Actions it reads the
public contribution calendar (counts per day, never repository names) with the
workflow's own token. Run by hand without a token it draws an unlit city, or
use --sample FILE to draw from a JSON file of {"YYYY-MM-DD": count}.

Lettering is drawn from outlines of Audiowide, Monoton and Chakra Petch (all SIL
Open Font License) stored in glyphs.json, so the panels look the same on every
machine regardless of installed fonts.
"""
import datetime as dt
import json
import os
import pathlib
import random
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
GLYPHS = json.loads((ROOT / "scripts" / "glyphs.json").read_text())
LOGIN = os.environ.get("PROFILE_LOGIN") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "infosecvibe"

# ---------------------------------------------------------------- palette
NIGHT = "#05061a"      # top of the sky
PANEL = "#0a0920"      # panel surface
FRONT = "#090818"      # nearest towers
INK = "#f1efff"        # primary text
INK2 = "#b9b6e6"       # secondary text
MUTED = "#8a87bd"      # captions, axis labels
RULE = "#24215a"       # hairlines
CYAN = "#5eeaff"
PINK = "#ff6bdc"
AMBER = "#ffb648"
UNLIT = "#17153d"
RAMP = ["#135e75", "#1c93ae", "#35cde6", "#aef4ff"]  # one hue, dim to bright

# Lettering for the sign: "sign" is Audiowide bent as outline tubing, "signb" is the Monoton marquee.
SIGN_FONT = os.environ.get("SIGN_FONT", "sign")

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def f2(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def nice_date(d, year=True):
    return f"{d.day} {MONTHS[d.month - 1]}" + (f" {d.year}" if year else "")


# ---------------------------------------------------------------- lettering
class Type:
    """Sets text as glyph outlines, shared through <defs>."""

    def __init__(self):
        self.used = {}

    def width(self, s, font, size, track=0):
        f = GLYPHS[font]
        k = size / f["upm"]
        kern = sum(f.get("k", {}).get(a + c, 0) for a, c in zip(s, s[1:]))
        return (sum(f["g"].get(c, f["g"]["?"])["a"] for c in s) + kern) * k + track * max(len(s) - 1, 0)

    def text(self, s, x, y, font, size, fill, anchor="start", track=0, attrs="", cls=None):
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


def svg(w, h, label, style, defs, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{label}">\n<title>{label}</title>\n'
            f'<style>{style}@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>\n'
            f'<defs>{defs}</defs>\n{body}\n</svg>\n')


# ---------------------------------------------------------------- data
def graphql(query, variables, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-panels"})
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if out.get("errors"):
        raise RuntimeError(out["errors"])
    return out["data"]


CAL = "contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}"


def fetch(token):
    """Returns ({date: count} for the whole account, total shown on the profile, last-year weeks)."""
    now = dt.datetime.now(dt.timezone.utc)
    d = graphql("query($l:String!){user(login:$l){createdAt contributionsCollection{restrictedContributionsCount hasAnyRestrictedContributions %s}}}" % CAL,
                {"l": LOGIN}, token)["user"]
    cal = d["contributionsCollection"]["contributionCalendar"]
    cc = d["contributionsCollection"]
    (ROOT / "assets" / "sync.txt").write_text(
        f"synced {now:%Y-%m-%d %H}:00 UTC (to the hour)\ncalendar total {cal['totalContributions']}\n"
        f"private counted {cc['restrictedContributionsCount']}\nprivate visible {cc['hasAnyRestrictedContributions']}\n")
    days = {}
    for year in range(int(d["createdAt"][:4]), now.year + 1):
        to = min(dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc), now)
        y = graphql("query($l:String!,$f:DateTime!,$t:DateTime!){user(login:$l){"
                    "contributionsCollection(from:$f,to:$t){%s}}}" % CAL,
                    {"l": LOGIN, "f": f"{year}-01-01T00:00:00Z", "t": to.strftime("%Y-%m-%dT%H:%M:%SZ")}, token)
        for wk in y["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for day in wk["contributionDays"]:
                days[day["date"]] = day["contributionCount"]
    weeks = [[(dt.date.fromisoformat(x["date"]), x["contributionCount"]) for x in wk["contributionDays"]]
             for wk in cal["weeks"]]
    for wk in weeks:
        for date, n in wk:
            days[date.isoformat()] = n
    return days, cal["totalContributions"], weeks


def weeks_from_days(days, today):
    """Lays the past year out the way the profile calendar does: Sunday-first weeks."""
    start = today - dt.timedelta(days=364)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)  # back to Sunday
    weeks, cur, d = [], [], start
    while d <= today:
        cur.append((d, days.get(d.isoformat(), 0)))
        if len(cur) == 7:
            weeks.append(cur)
            cur = []
        d += dt.timedelta(days=1)
    if cur:
        weeks.append(cur)
    return weeks


def summarise(days, total, weeks, today):
    series = sorted((dt.date.fromisoformat(k), v) for k, v in days.items())
    best_len, best_span, run, run_start = 0, None, 0, None
    prev = None
    for d, n in series:
        if n > 0 and prev is not None and (d - prev).days == 1 and run > 0:
            run += 1
        elif n > 0:
            run, run_start = 1, d
        else:
            run = 0
        if run and run >= best_len:  # on a tie, the most recent streak wins
            best_len, best_span = run, (run_start, d)
        prev = d
    # current streak may end today or yesterday (today is not over yet)
    cur, cur_start = 0, None
    d = today if days.get(today.isoformat(), 0) > 0 else today - dt.timedelta(days=1)
    while days.get(d.isoformat(), 0) > 0:
        cur, cur_start = cur + 1, d
        d -= dt.timedelta(days=1)
    year_days = [(d, n) for wk in weeks for d, n in wk]
    busiest = max(year_days, key=lambda x: x[1]) if year_days else (today, 0)
    return {
        "total": total,
        "active": sum(1 for _, n in year_days if n > 0),
        "current": cur, "current_start": cur_start,
        "longest": best_len, "longest_span": best_span,
        "busiest": busiest,
    }


# ---------------------------------------------------------------- city
def skyline(rng, x0, x1, base, hmin, hmax, wmin, wmax, fill):
    out, lights, x = [], [], x0
    while x < x1:
        w, h = rng.randint(wmin, wmax), rng.randint(hmin, hmax)
        out.append(f'<rect x="{x}" y="{base - h}" width="{w}" height="{h + 2}"/>')
        if rng.random() < 0.3:  # stepped crown
            out.append(f'<rect x="{x + w // 4}" y="{base - h - 8}" width="{w // 2}" height="9"/>')
        for _ in range(rng.randint(0, 4)):
            lights.append((x + rng.randint(3, max(4, w - 5)), base - rng.randint(8, max(9, h - 6))))
        x += w + rng.randint(0, 3)
    return f'<g fill="{fill}">' + "".join(out) + "</g>", lights


def build_city(weeks):
    W, H, BASE = 840, 470, 420
    X0, PITCH, BW = 23, 15, 11
    t = Type()
    rng = random.Random(1337)
    b = []

    # sky, horizon haze
    b.append(f'<g clip-path="url(#clip)"><rect width="{W}" height="{H}" fill="url(#sky)"/>'
             f'<rect width="{W}" height="{H}" fill="url(#haze)"/>')

    # distant and middle skylines, with a few lights that drift on and off
    far, far_l = skyline(rng, -8, W, BASE, 80, 172, 20, 44, "#221c5c")
    mid, mid_l = skyline(rng, -14, W, BASE, 56, 118, 24, 52, "#151140")
    b.append(far)
    b.append("".join(
        f'<rect x="{x}" y="{y}" width="2" height="2" fill="{rng.choice([PINK, CYAN, AMBER])}" opacity=".45"'
        + (f' class="tw" style="animation-delay:{rng.random() * 6:.1f}s"' if i % 3 == 0 else "") + "/>"
        for i, (x, y) in enumerate(far_l)))
    b.append(mid)
    b.append("".join(
        f'<rect x="{x}" y="{y}" width="3" height="2" fill="{rng.choice([PINK, CYAN, CYAN, AMBER])}" opacity=".5"'
        + (f' class="tw" style="animation-delay:{rng.random() * 6:.1f}s"' if i % 3 == 0 else "") + "/>"
        for i, (x, y) in enumerate(mid_l)))

    # traffic in the air
    b.append('<g class="fly a"><rect x="-34" y="-.8" width="34" height="1.6" fill="url(#trail)"/>'
             '<circle r="1.9" fill="#fff"/></g>'
             '<g class="fly b"><rect x="0" y="-.7" width="26" height="1.4" fill="url(#trailr)"/>'
             '<circle r="1.6" fill="#ffe3f8"/></g>')

    # the data: one tower per week
    totals = [sum(n for _, n in wk) for wk in weeks]
    peak_week = max(totals) if totals else 0
    active = sorted(n for wk in weeks for _, n in wk if n > 0)
    cuts = [active[int(len(active) * q) - 1] for q in (0.25, 0.5, 0.75)] if len(active) >= 4 else [0, 0, 0]
    towers, unlit, lit, glow, labels = [], [], [], [], []
    tallest = None
    prev_month = None
    for i, wk in enumerate(weeks):
        x = X0 + i * PITCH
        first = wk[0][0]
        month = next((d.month for d, _ in wk if d.day == 1), None)
        if i == 0 and wk[0][0].day <= 14:
            month = first.month
        if month and month != prev_month and i < len(weeks) - 1:
            labels.append(t.text(MONTHS[month - 1], x, BASE + 17, "ui5", 10.5, MUTED))
            prev_month = month
        extra = round(130 * totals[i] / peak_week) if peak_week else 0
        top = BASE - 64 - extra
        if not totals[i]:  # a quiet week is an empty lot, waiting to be built on
            towers.append(f'<rect x="{x}" y="{BASE - 3}" width="{BW}" height="3" fill="#191646"/>')
            continue
        towers.append(f'<rect x="{x}" y="{top}" width="{BW}" height="{BASE - top}" fill="{FRONT}"/>'
                      f'<rect x="{x}" y="{top}" width="{BW}" height="1" fill="#34317a"/>')
        if extra and (tallest is None or top < tallest[1]):
            tallest = (x, top)
        for d, n in wk:
            row = (d.weekday() + 1) % 7  # Sunday at the top, as on the profile calendar
            y = BASE - 10 - (6 - row) * 8
            unlit.append(f'<rect x="{x + 2}" y="{y}" width="7" height="5"/>')
            if n > 0:
                level = sum(n > q for q in cuts)
                delay = 2.0 + i * 0.03 + rng.random() * 0.25
                lit.append(f'<rect x="{x + 2}" y="{y}" width="7" height="5" rx="1" fill="{RAMP[level]}" '
                           f'class="on" style="animation-delay:{delay:.2f}s"/>')
                if level >= 3:
                    glow.append(f'<rect x="{x}" y="{y - 2}" width="11" height="9" fill="{RAMP[level]}"/>')
    b.append("".join(towers))
    if tallest:
        tx, ty = tallest[0] + BW / 2, tallest[1]
        b.append(f'<line x1="{tx}" y1="{ty}" x2="{tx}" y2="{ty - 16}" stroke="#34317a" stroke-width="1"/>'
                 f'<circle cx="{tx}" cy="{ty - 17}" r="5" fill="{AMBER}" opacity=".35" filter="url(#soft)" class="beacon"/>'
                 f'<circle cx="{tx}" cy="{ty - 17}" r="1.8" fill="{AMBER}" class="beacon"/>')
    b.append(f'<g fill="{UNLIT}">' + "".join(unlit) + "</g>")
    b.append('<g filter="url(#soft)" opacity=".75" class="glowin">' + "".join(glow) + "</g>")
    b.append("".join(lit))

    # rain, then the street
    b.append(f'<rect class="rain" x="-10" y="-190" width="{W + 80}" height="{H + 200}" fill="url(#rain)"/>')
    b.append(f'<rect y="{BASE}" width="{W}" height="{H - BASE}" fill="#070616"/>'
             f'<rect y="{BASE}" width="{W}" height="1" fill="#3a3780"/></g>')
    b.append("".join(labels))

    # legend
    cap = ("Each tower is a week. Each lit window is a day with contributions. Taller means a busier week."
           if peak_week else "The lights come on after the first sync.")
    b.append(t.text(cap, 23, BASE + 39, "ui5", 10.5, MUTED))
    lx = W - 23
    b.append(t.text("More", lx, BASE + 39, "ui5", 10.5, MUTED, anchor="end"))
    lx -= t.width("More", "ui5", 10.5) + 6
    for c in reversed(RAMP):
        lx -= 9
        b.append(f'<rect x="{lx}" y="{BASE + 33}" width="7" height="6" rx="1" fill="{c}"/>')
        lx -= 2
    b.append(t.text("Less", lx - 4, BASE + 39, "ui5", 10.5, MUTED, anchor="end"))

    # the sign: neon tubing bent around the outline of each letter
    font = SIGN_FONT
    name = LOGIN.upper() if font == "signb" else LOGIN
    cls = {7: "fl"} if len(name) > 7 else None
    size, track = 100, 3
    while t.width(name, font, size, track) > 640:
        size -= 1
    k = size / GLYPHS[font]["upm"]

    def tube(colour, px, fill="none"):
        return t.text(name, W / 2, 150, font, size, fill, anchor="middle", track=track, cls=cls,
                      attrs=f'stroke="{colour}" stroke-width="{px / k:.1f}" stroke-linejoin="round"')
    if font == "signb":
        sign = (f'<g filter="url(#wide)" opacity=".85">{tube("#ff4fd8", 4, "#ff2fcb")}</g>'
                f'<g filter="url(#tight)">{tube("#ff4fd8", 4, "#ff4fd8")}</g>'
                + tube("#ff62dd", 4, "#ff62dd") + tube("#fff0fc", 0.01, "#fff0fc"))
    else:
        sign = (f'<g filter="url(#wide)" opacity=".9">{tube("#ff2fcb", 8)}</g>'
                f'<g filter="url(#tight)">{tube("#ff4fd8", 6.5, "#ff4fd822")}</g>'
                + tube("#ff62dd", 4.8) + tube("#fff0fc", 2))
    b.append(f'<g class="sign">{sign}</g>')
    b.append(t.text("Threat intelligence, DFIR and security tooling", W / 2, 190, "ui5", 17, "#a6f4ff",
                    anchor="middle", track=0.5, attrs='class="tag"'))
    b.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{CYAN}" stroke-opacity=".22"/>')

    defs = (
        f'<clipPath id="clip"><rect width="{W}" height="{H}" rx="16"/></clipPath>'
        f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{NIGHT}"/>'
        '<stop offset=".55" stop-color="#0e0b30"/><stop offset=".9" stop-color="#2b1459"/></linearGradient>'
        f'<radialGradient id="haze" cx="420" cy="{BASE + 10}" r="460" gradientUnits="userSpaceOnUse">'
        '<stop offset="0" stop-color="#ff4fd8" stop-opacity=".34"/><stop offset=".5" stop-color="#7a3cff" stop-opacity=".12"/>'
        '<stop offset="1" stop-color="#7a3cff" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="trail"><stop offset="0" stop-color="#5eeaff" stop-opacity="0"/><stop offset="1" stop-color="#5eeaff"/></linearGradient>'
        '<linearGradient id="trailr"><stop offset="0" stop-color="#ff6bdc"/><stop offset="1" stop-color="#ff6bdc" stop-opacity="0"/></linearGradient>'
        '<pattern id="rain" width="60" height="180" patternUnits="userSpaceOnUse">'
        '<g stroke="#b9c6ff" stroke-width=".8" stroke-linecap="round" opacity=".13">'
        '<path d="M52 8l-5 15M21 44l-5 15M44 92l-6 18M9 120l-5 15M33 150l-4 12M58 60l-4 12"/></g></pattern>'
        '<filter id="wide" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="16"/></filter>'
        '<filter id="tight" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur stdDeviation="5"/></filter>'
        '<filter id="soft" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="2.6"/></filter>'
        + t.defs())
    style = (
        ".sign{animation:strike 1.7s .25s both}"
        "@keyframes strike{0%{opacity:0}7%{opacity:.9}9%{opacity:.08}15%{opacity:.75}17%{opacity:.12}"
        "24%{opacity:1}27%{opacity:.55}31%{opacity:1}100%{opacity:1}}"
        ".fl{animation:buzz 9s 4s infinite}"
        "@keyframes buzz{0%,91%,95%,98%,100%{opacity:1}92%{opacity:.3}96%{opacity:.55}}"
        ".tag{animation:rise 1s 1.5s both}@keyframes rise{from{opacity:0}to{opacity:1}}"
        ".on{animation:lit .5s both}@keyframes lit{0%{opacity:0}55%{opacity:1}70%{opacity:.35}100%{opacity:1}}"
        ".glowin{animation:glow 1.4s 3.4s both}@keyframes glow{from{opacity:0}to{opacity:.75}}"
        ".tw{animation:tw 5s infinite alternate}@keyframes tw{0%,40%{opacity:.5}60%,100%{opacity:.08}}"
        ".beacon{animation:blink 1.8s infinite}@keyframes blink{0%,55%{opacity:1}56%,100%{opacity:.12}}"
        ".rain{animation:fall .85s linear infinite}@keyframes fall{to{transform:translate(-60px,180px)}}"
        ".fly.a{animation:fa 15s 3s linear infinite both}@keyframes fa{from{transform:translate(-60px,262px)}to{transform:translate(900px,236px)}}"
        ".fly.b{animation:fb 22s 6s linear infinite both}@keyframes fb{from{transform:translate(900px,300px)}to{transform:translate(-60px,318px)}}"
    )
    label = (f"{LOGIN}: a night city where every tower is a week of the past year "
             f"and every lit window is a day with contributions")
    return svg(W, H, label, style, defs, "\n".join(b))


# ---------------------------------------------------------------- focus
def build_focus():
    W, H = 840, 196
    t = Type()
    b = [f'<rect width="{W}" height="{H}" rx="16" fill="{PANEL}"/>'
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{RULE}"/>']
    items = [
        ("Threat intelligence", ["Turning raw reporting into", "something a defender can use."], CYAN,
         '<path class="d" pathLength="1" d="M28 30L12 14M28 30L45 11M28 30L10 46M28 30L46 45"/>'
         '<circle class="d" pathLength="1" cx="12" cy="14" r="4.5" fill="{bg}"/><circle class="d" pathLength="1" cx="45" cy="11" r="4.5" fill="{bg}"/>'
         '<circle class="d" pathLength="1" cx="10" cy="46" r="4.5" fill="{bg}"/><circle class="d" pathLength="1" cx="46" cy="45" r="4.5" fill="{bg}"/>'
         '<circle class="pulse" cx="28" cy="30" r="6" fill="{c}" stroke="none"/>'),
        ("DFIR", ["Working out what happened,", "in what order, and proving it."], PINK,
         '<circle class="d" pathLength="1" cx="24" cy="24" r="16"/><path class="d" pathLength="1" d="M36 36L50 50"/>'
         '<path class="d scan" pathLength="1" d="M15 19H33M15 25H28M15 31H31" stroke-width="2"/>'),
        ("Threat hunting", ["Going looking before", "the alert fires."], CYAN,
         '<circle class="d" pathLength="1" cx="28" cy="28" r="23"/><circle class="d" pathLength="1" cx="28" cy="28" r="12" stroke-opacity=".55"/>'
         '<g transform="translate(28 28)"><path class="sweep" d="M0 0V-23"/></g>'
         '<circle class="blip" cx="39" cy="17" r="2.6" fill="{c}" stroke="none"/>'),
        ("Security tooling", ["Building the small, sharp tools", "the job keeps asking for."], PINK,
         '<rect class="d" pathLength="1" x="4" y="9" width="48" height="38" rx="6"/>'
         '<path class="d" pathLength="1" d="M14 21L22 28L14 35"/><path class="cur" d="M27 36H39"/>'),
    ]
    for i, (name, lines, colour, art) in enumerate(items):
        cx = 120 + i * 200
        art = art.replace("{c}", colour).replace("{bg}", PANEL)
        g = (f'<g transform="translate({cx - 28} 26)" fill="none" stroke="{colour}" stroke-width="2.4" '
             f'stroke-linecap="round" stroke-linejoin="round" style="--d:{0.15 + i * 0.28:.2f}s">')
        b.append(g.replace('stroke-width="2.4"', 'stroke-width="5" opacity=".5" filter="url(#g)"') + art + "</g>")
        b.append(g + art + "</g>")
        b.append(t.text(name, cx, 122, "ui6", 17, INK, anchor="middle"))
        for j, line in enumerate(lines):
            b.append(t.text(line, cx, 147 + j * 18, "ui5", 12.5, INK2, anchor="middle"))
        if i:
            b.append(f'<rect x="{cx - 100}" y="34" width="1" height="{H - 68}" fill="{RULE}"/>')
    defs = '<filter id="g" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="3.5"/></filter>' + t.defs()
    style = (
        ".d{stroke-dasharray:1;animation:draw 1.1s var(--d) both ease-out}@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
        ".pulse{animation:pulse 2.4s infinite ease-in-out}@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}"
        ".sweep{animation:spin 4s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}"
        ".blip{animation:blip 4s infinite}@keyframes blip{0%,8%{opacity:0}12%{opacity:1}70%,100%{opacity:0}}"
        ".cur{animation:cur 1.1s steps(1) infinite}@keyframes cur{50%{opacity:0}}"
        ".scan{animation:draw 1.1s var(--d) both ease-out,scan 5s 2s infinite}@keyframes scan{0%,100%{opacity:1}50%{opacity:.4}}"
    )
    return svg(W, H, "Areas of work: threat intelligence, DFIR, threat hunting and security tooling", style, defs, "\n".join(b))


# ---------------------------------------------------------------- stats
def build_stats(s, synced, have_data):
    W, H = 840, 150
    t = Type()
    b = [f'<rect width="{W}" height="{H}" rx="16" fill="{PANEL}"/>'
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{RULE}"/>']
    dash = "–" if False else "-"
    if have_data:
        span = s["longest_span"]
        tiles = [
            (f'{s["total"]:,}', "contributions in the past year",
             f'{s["active"]} active day{"" if s["active"] == 1 else "s"}'),
            (str(s["current"]), "day streak, current",
             f'since {nice_date(s["current_start"], False)}' if s["current"] else "no streak running today"),
            (str(s["longest"]), "day streak, longest",
             dash if not span else nice_date(span[1]) if span[0] == span[1]
             else f'{nice_date(span[0], False)} to {nice_date(span[1])}'),
            (str(s["busiest"][1]), "most in a single day",
             nice_date(s["busiest"][0]) if s["busiest"][1] else dash),
        ]
    else:
        tiles = [(dash, x, "") for x in ("contributions in the past year", "day streak, current",
                                         "day streak, longest", "most in a single day")]
    for i, (value, label, ctx) in enumerate(tiles):
        x = 34 + i * 200
        if i:
            b.append(f'<rect x="{x - 20}" y="26" width="1" height="82" fill="{RULE}"/>')
        b.append(t.text(value, x, 62, "ui7", 40, INK))
        b.append(t.text(label, x, 86, "ui5", 12, INK2))
        if ctx:
            b.append(t.text(ctx, x, 104, "ui5", 11, MUTED))
    note = (f"Rebuilt automatically from contribution activity. Synced {nice_date(synced)}."
            if have_data else "Waiting for the first sync.")
    b.append(f'<rect x="34" y="120" width="{W - 68}" height="1" fill="{RULE}"/>')
    b.append(f'<circle cx="38" cy="134" r="3" fill="{CYAN}" class="live"/>')
    b.append(t.text(note, 48, 138, "ui5", 10.5, MUTED))
    style = ".live{animation:live 2.2s infinite ease-in-out}@keyframes live{0%,100%{opacity:1}50%{opacity:.25}}"
    label = "Contribution numbers" + (
        f': {s["total"]} in the past year, current streak {s["current"]} days, longest streak {s["longest"]} days, '
        f'busiest day {s["busiest"][1]}' if have_data else "")
    return svg(W, H, label, style, t.defs(), "\n".join(b))


# ---------------------------------------------------------------- main
def main():
    today = dt.datetime.now(dt.timezone.utc).date()
    token = os.environ.get("GITHUB_TOKEN")
    have_data = True
    if "--sample" in sys.argv:
        days = json.loads(pathlib.Path(sys.argv[sys.argv.index("--sample") + 1]).read_text())
        today = max(dt.date.fromisoformat(k) for k in days)
        weeks = weeks_from_days(days, today)
        total = sum(n for wk in weeks for _, n in wk)
    elif token:
        for attempt in range(3):
            try:
                days, total, weeks = fetch(token)
                break
            except Exception as err:  # a blip should not fail the run; the last good panels stay up
                problem = err
                time.sleep(5 * (attempt + 1))
        else:
            print(f"::warning::Could not read the contribution calendar ({problem}). Keeping the current panels.")
            return
        today = max(d for wk in weeks for d, _ in wk)
    else:
        days, total, weeks, have_data = {}, 0, weeks_from_days({}, today), False
    stats = summarise(days, total, weeks, today)
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    (out / "city.svg").write_text(build_city(weeks))
    (out / "focus.svg").write_text(build_focus())
    (out / "stats.svg").write_text(build_stats(stats, today, have_data))
    print(f"built panels for {LOGIN}: {total} contributions, {len(weeks)} weeks, "
          f"current streak {stats['current']}, longest {stats['longest']}")


if __name__ == "__main__":
    main()
