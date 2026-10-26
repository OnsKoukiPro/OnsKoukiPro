"""Build the profile README and its animated SVGs (light + dark).

Usage: python scripts/build.py
Fetches the public contribution calendar, writes assets/*.svg and README.md.
Fonts in fonts/ are pre-subset woff2 files (SIL OFL) embedded into each SVG.
"""
import base64
import datetime as dt
import math
import random
import re
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

USER = "OnsKoukiPro"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONTS = ROOT / "fonts"
RAW = f"https://raw.githubusercontent.com/{USER}/{USER}/main/assets"
W = 1200

THEMES = {
    "light": {"accent": "#6d28d9", "text": "#1f2328", "muted": "#59636e", "line": "#d0d7de",
              "blobs": ["#a78bfa", "#67e8f9", "#f9a8d4"], "blob_opacity": 0.55,
              "grad": ["#6d28d9", "#0891b2", "#db2777"],
              "dots": ["#ebedf0", "#ddd6fe", "#a78bfa", "#7c3aed", "#5b21b6"]},
    "dark": {"accent": "#a78bfa", "text": "#e6edf3", "muted": "#9198a1", "line": "#30363d",
             "blobs": ["#7c3aed", "#0891b2", "#db2777"], "blob_opacity": 0.5,
             "grad": ["#a78bfa", "#22d3ee", "#f472b6"],
             "dots": ["#161b22", "#2e1065", "#5b21b6", "#7c3aed", "#a78bfa"]},
}

ROLE = "creative technologist · ict engineer"
WORDS = ["dream it.", "sketch it.", "build it.", "train it.", "ship it.", "scale it."]
BLURB = ["AI/ML, software engineering and cloud infrastructure in one head.",
         "I like owning the whole loop, from the first sketch to the dashboard."]

WORK = [
    ("claritychains", "ClarityChains", "LLM agents that read supplier offers, flag the traps and pick a winner",
     "react · django · langchain", "https://clarity-chains.vercel.app"),
    ("model", "claritychains-model", "Price forecasts and a hedging optimiser for lithium, cobalt and nickel",
     "python · streamlit · scipy", f"https://github.com/{USER}/claritychains-model"),
    ("honeypot", "Honeypot-CK8s", "A honeynet in a vCluster. Attackers get in, I get dashboards",
     "k8s · fluentd · opensearch", f"https://github.com/{USER}/Honeypot-CK8s"),
    ("rl-ddos", "RL × SDN", "A network that learns when to block a flood (94.6% detection)",
     "ryu · mininet · tensorflow",
     f"https://github.com/{USER}/RL-based-DDos-Mitigation-in-SDN-based-broadband-networks"),
    ("car-price", "Car Price ML", "Scraped four marketplaces to price a used car (R² 0.75)",
     "bs4 · pandas · sklearn", f"https://github.com/{USER}/ML-Car-Price-Prediction"),
]

LINKS = [
    ("linkedin", "LinkedIn", "https://www.linkedin.com/in/ons-kouki/"),
    ("email", "Email", "mailto:ons.koukipro@gmail.com"),
    ("demo", "Live demo", "https://clarity-chains.vercel.app"),
]

STACK = [
    ("ml & data", ["pytorch", "tensorflow", "scikit-learn", "langchain", "pandas", "airflow", "druid", "superset"]),
    ("backend", ["python", "fastapi", "django", "nestjs", "node", "spring", "postgres", "redis"]),
    ("cloud", ["aws", "azure", "kubernetes", "helm", "argo cd", "terraform", "pulumi", "github actions"]),
    ("security & web", ["vault", "keycloak", "opensearch", "grafana", "typescript", "react", "next.js", "angular"]),
]

FONT_FACES = {  # css class -> (family, weight, style, file)
    "s": ("Serif", 400, "normal", "serif"),
    "si": ("SerifItalic", 400, "italic", "serif-italic"),
    "g": ("Grotesk", 400, "normal", "grotesk-400"),
    "gb": ("GroteskBold", 600, "normal", "grotesk-600"),
    "m": ("Mono", 400, "normal", "mono-400"),
}
FALLBACK = {"s": "Georgia, serif", "si": "Georgia, serif",
            "g": "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif",
            "gb": "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif",
            "m": "ui-monospace, Menlo, Consolas, monospace"}

BASE_CSS = """
.f { opacity: 0; animation: fade 1.4s ease-out forwards; }
.u { opacity: 0; animation: up 1.3s cubic-bezier(.2,.7,.2,1) forwards; }
@keyframes fade { to { opacity: 1; } }
@keyframes up { from { opacity: 0; transform: translateY(26px); } to { opacity: 1; transform: none; } }
"""


def font_css(body):
    """Embed only the fonts whose class is used in this SVG."""
    used = {c for classes in re.findall(r'class="([^"]+)"', body) for c in classes.split()}
    css = []
    for cls, (family, weight, style, file) in FONT_FACES.items():
        if cls in used:
            data = base64.b64encode((FONTS / f"{file}.woff2").read_bytes()).decode()
            css.append(f"@font-face{{font-family:{family};font-weight:{weight};font-style:{style};"
                       f"src:url(data:font/woff2;base64,{data}) format('woff2')}}"
                       f".{cls}{{font-family:{family},{FALLBACK[cls]};font-weight:{weight};font-style:{style}}}")
    return "".join(css)


def fetch_calendar(year):
    url = f"https://github.com/users/{USER}/contributions?from={year}-01-01&to={year}-12-31"
    html = urllib.request.urlopen(url, timeout=30).read().decode()
    levels = {}
    for td in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", html):
        date, level = re.search(r'data-date="([^"]+)"', td), re.search(r'data-level="(\d)"', td)
        if date and level:
            levels[dt.date.fromisoformat(date.group(1))] = int(level.group(1))
    total = sum(int(n) for n in re.findall(r">(\d+) contributions? on ", html))
    return levels, total


def svg(width, height, theme, body, label, css=""):
    t = THEMES[theme]
    g0, g1, g2 = t["grad"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" fill="none" role="img" aria-label="{escape(label)}">
<defs>
  <linearGradient id="grad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{g0}"/><stop offset="0.5" stop-color="{g1}"/><stop offset="1" stop-color="{g2}"/>
  </linearGradient>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="300" y2="0">
    <stop offset="0" stop-color="{t['accent']}"/><stop offset="0.45" stop-color="{t['accent']}"/>
    <stop offset="0.5" stop-color="{g1}"/>
    <stop offset="0.55" stop-color="{t['accent']}"/><stop offset="1" stop-color="{t['accent']}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-400 0;{width} 0;{width} 0" keyTimes="0;0.25;1" dur="10s" repeatCount="indefinite"/>
  </linearGradient>
</defs>
<style>{font_css(body)}{BASE_CSS}{css}</style>
{body}
</svg>
"""


def delay(s):
    return f'style="animation-delay:{s:.2f}s"'


def arrow(t, size, begin):
    """A ↗ that sits right after the label and hops up-right every few seconds."""
    hop = 'values="{a};{b};{a};{a}" keyTimes="0;0.05;0.1;1" dur="5s" begin="%.1fs" repeatCount="indefinite"' % begin
    return (f'<tspan dx="8" font-size="{size}" fill="{t["accent"]}">↗'
            f'<animate attributeName="dx" {hop.format(a=8, b=12)}/>'
            f'<animate attributeName="dy" {hop.format(a=-2, b=-6)}/></tspan>')


EASE = ".45 0 .55 1"


def blob_path(cx, cy, r, rng, n=7):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * rng.uniform(0.75, 1.25)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(n):  # closed Catmull-Rom spline as cubic béziers
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d + "Z"


def blobs(t, specs, blur):
    """Soft gradient blobs that morph and drift. Fixed seed so every build is identical."""
    rng = random.Random(7)
    out = [f'<filter id="soft" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="{blur}"/></filter>',
           f'<g filter="url(#soft)" opacity="{t["blob_opacity"]}">']
    for (cx, cy, r, dur), color in zip(specs, t["blobs"]):
        shapes = [blob_path(cx, cy, r, rng) for _ in range(3)]
        out.append(f'''<path fill="{color}" d="{shapes[0]}">
  <animate attributeName="d" values="{';'.join(shapes + shapes[:1])}" dur="{dur}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.33;0.66;1" keySplines="{EASE};{EASE};{EASE}"/>
  <animateTransform attributeName="transform" type="translate" values="0 0;{rng.randint(-60, 60)} {rng.randint(-25, 25)};0 0" dur="{dur * 1.4:.0f}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="{EASE};{EASE}"/>
</path>''')
    return "\n".join(out) + "</g>"


def sparkles(points):
    return "".join(
        f'<text class="s" x="{x}" y="{y}" font-size="{s}" fill="url(#grad)" opacity="0">✦'
        f'<animate attributeName="opacity" values="0;1;0" dur="{3 + i % 3}s" begin="{i * 0.7:.1f}s" repeatCount="indefinite"/></text>'
        for i, (x, y, s) in enumerate(points))


def top(theme, total, since):
    t = THEMES[theme]
    body = f"""<text class="si f" {delay(0.2)} x="0" y="32" font-size="30" fill="{t['text']}">Ons Kouki</text>
<text class="g f" {delay(0.5)} x="{W / 2}" y="31" text-anchor="middle" font-size="21" fill="{t['muted']}"><tspan class="gb" fill="url(#shine)">{total:,}</tspan> contributions since {since}</text>
<text class="m f" {delay(0.8)} x="{W}" y="31" text-anchor="end" font-size="19" fill="{t['muted']}">readme.md</text>
<line class="f" {delay(0.8)} x1="0" y1="52" x2="{W}" y2="52" stroke="{t['line']}"/>"""
    return svg(W, 58, theme, body, f"Ons Kouki · {total} contributions since {since}")


def link(theme, label, i):
    t = THEMES[theme]
    width = len(label) * 13 + 44
    body = f'<text class="gb f" {delay(1 + i * 0.3)} x="0" y="26" font-size="24" fill="url(#shine)">{escape(label)}{arrow(t, 18, 2 + i * 1.7)}</text>'
    return svg(width, 34, theme, body, label), width


def waves(y0, count=3):
    """Thin sine lines that sway, a nod to signals and networks."""
    out = []
    for k in range(count):
        y, amp = y0 + k * 14, 16 - k * 4
        a = f"M0,{y} " + " ".join(f"Q{x + 75},{y + (-1) ** (x // 150) * amp} {x + 150},{y}" for x in range(0, W, 150))
        b = f"M0,{y} " + " ".join(f"Q{x + 75},{y - (-1) ** (x // 150) * amp} {x + 150},{y}" for x in range(0, W, 150))
        out.append(f'''<path d="{a}" stroke="url(#grad)" stroke-width="{1.6 - k * 0.4:.1f}" opacity="{0.7 - k * 0.2:.1f}">
  <animate attributeName="d" values="{a};{b};{a}" dur="{6 + k * 2}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="{EASE};{EASE}"/>
</path>''')
    return "".join(out)


def hero(theme):
    t = THEMES[theme]
    step, n = 72, len(WORDS)
    # rotating word: hold each word, then glide up to the next one
    values, times = [], []
    for i in range(n):
        values += [f"0 {-i * step}", f"0 {-i * step}"]
        times += [i / n, (i + 0.8) / n]
    values.append(f"0 {-n * step}")
    times.append(1)
    splines = ["0 0 1 1" if k % 2 == 0 else ".65 0 .35 1" for k in range(len(values) - 1)]
    words = "".join(f'<text class="si" x="0" y="{i * step}" font-size="68" fill="url(#grad)">{escape(w)}</text>'
                    for i, w in enumerate(WORDS + WORDS[:1]))
    body = f"""{blobs(t, [(860, 230, 120, 16), (1010, 300, 100, 13), (760, 340, 85, 19)], 42)}
{sparkles([(1080, 110, 26), (690, 140, 16), (1130, 400, 18), (930, 455, 14), (640, 300, 12)])}
<text class="m u" {delay(0.3)} x="4" y="70" font-size="18" letter-spacing="3" fill="{t['accent']}">✦ {escape(ROLE.upper())}</text>
<text class="u" {delay(0.5)} x="0" y="215" font-size="150" letter-spacing="-3"><tspan class="s" fill="{t['text']}">Ons </tspan><tspan class="si" fill="url(#grad)">Kouki</tspan></text>
<g class="u" {delay(0.9)}>
  <text class="s" x="4" y="318" font-size="68" fill="{t['text']}">I</text>
  <clipPath id="window"><rect x="0" y="258" width="700" height="80"/></clipPath>
  <g clip-path="url(#window)"><g transform="translate(44 318)"><g>
    {words}
    <animateTransform attributeName="transform" type="translate" values="{';'.join(values)}" keyTimes="{';'.join(f'{x:.4f}' for x in times)}" calcMode="spline" keySplines="{';'.join(splines)}" dur="{n * 2.2:.1f}s" repeatCount="indefinite"/>
  </g></g></g>
</g>
<text class="g u" {delay(1.2)} x="4" y="392" font-size="24" fill="{t['muted']}">{escape(BLURB[0])}</text>
<text class="g u" {delay(1.35)} x="4" y="426" font-size="24" fill="{t['muted']}">{escape(BLURB[1])}</text>
<g class="f" {delay(1.6)}>{waves(500)}</g>"""
    return svg(W, 560, theme, body, f"Ons Kouki, {ROLE}. I dream it, sketch it, build it, train it, ship it, scale it. {' '.join(BLURB)}")


def graph(theme, calendars):
    t = THEMES[theme]
    cell, gap, ygap = 6.2, 1.3, 18
    years = sorted(calendars)
    block = (W - ygap * (len(years) - 1)) / len(years)
    step = min(cell + gap, block / 53)
    gy = 48
    out = [f'<text class="m f" {delay(0.3)} x="0" y="24" font-size="17" fill="{t["muted"]}">$ git log --graph --since={years[0]}</text>']
    for yi, year in enumerate(years):
        x0 = yi * (block + ygap)
        jan1 = dt.date(year, 1, 1)
        offset = (jan1.weekday() + 1) % 7  # Sunday-first rows, like GitHub
        rects = []
        for date, level in sorted(calendars[year].items()):
            col, row = divmod((date - jan1).days + offset, 7)
            appear = 0.6 + yi * 0.5 + col * 0.025
            wave = 4 + (yi * 53 + col) * 0.035  # a brightness wave that sweeps left to right
            rects.append(f'<rect class="d l{level}" style="animation-delay:{appear:.2f}s,{wave:.2f}s" '
                         f'x="{x0 + col * step:.1f}" y="{gy + row * step:.1f}" width="{step - gap:.1f}" height="{step - gap:.1f}" rx="1.6"/>')
        out.append("".join(rects))
        out.append(f'<text class="si f" {delay(0.6 + yi * 0.5)} x="{x0}" y="{gy + 7 * step + 30:.0f}" font-size="24" fill="{t["accent"]}">{year}</text>')
    css = ("".join(f".l{i}{{fill:{c}}}" for i, c in enumerate(t["dots"]))
           + ".d{opacity:0;animation:fade 1s ease-out forwards,pulse 7s ease-in-out infinite}"
           "@keyframes pulse{0%,100%{fill-opacity:1}6%{fill-opacity:.35}14%{fill-opacity:1}}")
    return svg(W, int(gy + 7 * step + 40), theme, "\n".join(out), "Contribution graph", css)


def heading(theme, plain, italic, note=""):
    t = THEMES[theme]
    body = f"""<text class="u" {delay(0.2)} x="0" y="62" font-size="62"><tspan class="s" fill="{t['text']}">{escape(plain)} </tspan><tspan class="si" fill="url(#grad)">{escape(italic)}</tspan></text>
<text class="m f" {delay(0.6)} x="{W}" y="60" text-anchor="end" font-size="17" fill="{t['muted']}">{escape(note)}</text>
<line class="f" {delay(0.5)} x1="0" y1="86" x2="{W}" y2="86" stroke="{t['line']}"/>"""
    return svg(W, 92, theme, body, f"{plain} {italic}")


def glyph(slug, t):
    """Small looping animation that hints at each project, drawn in a 64×64 box."""
    a, g, spline4 = t["accent"], "url(#grad)", ";".join([EASE] * 4)
    if slug == "claritychains":  # linked rings turning
        rings = "".join(f'<circle cx="{32 + 10 * math.cos(k * 2.094):.1f}" cy="{32 + 10 * math.sin(k * 2.094):.1f}" r="12" stroke="{g}" stroke-width="2.2"/>' for k in range(3))
        return (f'<g>{rings}<animateTransform attributeName="transform" type="rotate" values="0 32 32;360 32 32" dur="12s" repeatCount="indefinite"/></g>'
                f'<circle cx="32" cy="32" r="3" fill="{a}"><animate attributeName="r" values="2;4;2" dur="2s" repeatCount="indefinite"/></circle>')
    if slug == "model":  # a price line drawing itself into a forecast cone
        return (f'<path d="M40,31 L60,14 L60,44 Z" fill="{a}" opacity="0.18"/><path d="M40,31 L60,26" stroke="{a}" stroke-dasharray="3 3" stroke-width="2"/>'
                f'<path d="M4,44 L14,38 L22,41 L32,28 L40,31" stroke="{g}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="60" stroke-dashoffset="60">'
                f'<animate attributeName="stroke-dashoffset" values="60;0;0;60" keyTimes="0;0.4;0.85;1" dur="4s" repeatCount="indefinite"/></path>'
                f'<line x1="4" y1="56" x2="60" y2="56" stroke="{t["line"]}" stroke-width="2"/>')
    if slug == "honeypot":  # a hexagon cell with something buzzing around it
        hexagon = " ".join(f"{32 + 18 * math.cos(math.pi / 3 * k + math.pi / 6):.1f},{32 + 18 * math.sin(math.pi / 3 * k + math.pi / 6):.1f}" for k in range(6))
        return (f'<polygon points="{hexagon}" stroke="{g}" stroke-width="2.4"><animateTransform attributeName="transform" type="rotate" values="0 32 32;60 32 32;60 32 32" keyTimes="0;0.3;1" dur="5s" repeatCount="indefinite"/></polygon>'
                f'<circle r="3.5" fill="{a}"><animateMotion dur="3s" repeatCount="indefinite" path="M32,6 C62,6 62,58 32,58 C2,58 2,6 32,6Z"/></circle>')
    if slug == "rl-ddos":  # packets hitting a wall, only one gets through
        pulses = "".join(f'<circle r="3" fill="{a}"><animateMotion path="M2,32 H40" dur="1.8s" begin="{k * 0.6:.1f}s" repeatCount="indefinite"/>'
                         f'<animate attributeName="opacity" values="1;1;0" keyTimes="0;0.85;1" dur="1.8s" begin="{k * 0.6:.1f}s" repeatCount="indefinite"/></circle>' for k in range(3))
        return (f'<line x1="2" y1="32" x2="62" y2="32" stroke="{t["line"]}" stroke-width="2"/>{pulses}'
                f'<rect x="42" y="12" width="6" height="40" rx="3" fill="{g}"><animate attributeName="opacity" values="1;.5;1" dur="0.6s" repeatCount="indefinite"/></rect>'
                f'<circle r="3" fill="{t["grad"][1]}"><animateMotion path="M48,32 H62" dur="1.8s" repeatCount="indefinite"/></circle>')
    if slug == "car-price":  # a gauge settling on a price
        times = 'keyTimes="0;0.3;0.5;0.75;1" calcMode="spline" keySplines="%s"' % spline4
        return (f'<path d="M8,44 A24,24 0 0 1 56,44" stroke="{t["line"]}" stroke-width="5" stroke-linecap="round"/>'
                f'<path d="M8,44 A24,24 0 0 1 56,44" stroke="{g}" stroke-width="5" stroke-linecap="round" stroke-dasharray="76" stroke-dashoffset="76">'
                f'<animate attributeName="stroke-dashoffset" values="76;20;45;8;76" dur="5s" repeatCount="indefinite" {times}/></path>'
                f'<line x1="32" y1="44" x2="32" y2="24" stroke="{a}" stroke-width="3" stroke-linecap="round">'
                f'<animateTransform attributeName="transform" type="rotate" values="-80 32 44;35 32 44;-10 32 44;70 32 44;-80 32 44" dur="5s" repeatCount="indefinite" {times}/></line>'
                f'<circle cx="32" cy="44" r="4" fill="{a}"/>')
    return ""


def work(theme, slug, name, text, stack, i):
    t = THEMES[theme]
    body = f"""<g class="u" {delay(0.3 + i * 0.15)}>
<g transform="translate(0 14)">{glyph(slug, t)}</g>
<text class="gb" x="96" y="40" font-size="27" fill="url(#shine)">{escape(name)}{arrow(t, 20, 3 + i * 1.3)}</text>
<text class="m" x="{W}" y="40" text-anchor="end" font-size="17" fill="{t['muted']}">{escape(stack)}</text>
<text class="g" x="96" y="74" font-size="21" fill="{t['muted']}">{escape(text)}</text>
<line x1="96" y1="96" x2="{W}" y2="96" stroke="{t['line']}"/>
</g>"""
    return svg(W, 100, theme, body, f"{name}: {text}")


def marquee(theme):
    """One endless ticker per category, alternating direction, fading out at the edges."""
    t = THEMES[theme]
    size, row_h, label_w = 22, 60, 250
    out = [f'''<linearGradient id="edge" x1="0" y1="0" x2="{W}" y2="0" gradientUnits="userSpaceOnUse">
  <stop offset="{label_w / W:.3f}" stop-color="#000"/><stop offset="{(label_w + 70) / W:.3f}" stop-color="#fff"/>
  <stop offset="{(W - 90) / W:.3f}" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
<mask id="fade"><rect width="{W}" height="{len(STACK) * row_h}" fill="url(#edge)"/></mask>''']
    for r, (label, items) in enumerate(STACK):
        y = 40 + r * row_h
        chunk = "   ✦   ".join(items) + "   ✦   "
        width = len(chunk) * size * 0.6  # JetBrains Mono advance is 0.6em
        direction = f"0 0;{-width:.1f} 0" if r % 2 == 0 else f"{-width:.1f} 0;0 0"
        out.append(f'''<text class="si f" {delay(0.3 + r * 0.15)} x="0" y="{y}" font-size="34" fill="url(#grad)">{escape(label)}</text>
<g mask="url(#fade)"><g class="f" {delay(0.5 + r * 0.15)}><text class="m" x="{label_w}" y="{y - 2}" font-size="{size}" fill="{t['text']}" xml:space="preserve">{escape(chunk * 3)}</text>
  <animateTransform attributeName="transform" type="translate" values="{direction}" dur="{width / 45:.1f}s" repeatCount="indefinite"/></g></g>''')
    return svg(W, len(STACK) * row_h, theme, "\n".join(out),
               "Toolbox: " + "; ".join(f"{a}: {', '.join(b)}" for a, b in STACK))


def outro(theme):
    t = THEMES[theme]
    squiggle = "M6,128 " + " ".join(f"Q{x + 18},{118 if (x // 36) % 2 == 0 else 138} {x + 36},128" for x in range(6, 470, 36))
    body = f"""{sparkles([(500, 60, 30), (548, 96, 16), (600, 40, 12)])}
<text class="si u" {delay(0.2)} x="0" y="92" font-size="76" fill="url(#grad)">to be continued…</text>
<path d="{squiggle}" stroke="url(#grad)" stroke-width="3" stroke-linecap="round" stroke-dasharray="620" stroke-dashoffset="620">
  <animate attributeName="stroke-dashoffset" values="620;0;0;620" keyTimes="0;0.3;0.85;1" dur="8s" begin="1s" repeatCount="indefinite"/>
</path>
<text class="g f" {delay(1)} x="{W}" y="92" text-anchor="end" font-size="20" fill="{t['muted']}">got a wild idea? let's build it.</text>
<text class="m f" {delay(1.2)} x="{W}" y="126" text-anchor="end" font-size="16" fill="{t['muted']}">english · french · arabic</text>"""
    return svg(W, 160, theme, body, "To be continued. Got a wild idea? Let's build it. Speaks English, French and Arabic.")


def picture(name, alt, version, width="100%"):
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{RAW}/{name}-dark.svg?v={version}">'
            f'<img src="{RAW}/{name}-light.svg?v={version}" alt="{escape(alt)}" width="{width}"></picture>')


def build():
    this_year = dt.date.today().year
    years = [this_year - 2, this_year - 1, this_year]
    calendars, total = {}, 0
    for year in [this_year - 4, this_year - 3] + years:
        levels, n = fetch_calendar(year)
        total += n
        if year in years:
            calendars[year] = levels

    ASSETS.mkdir(exist_ok=True)
    for old in ASSETS.glob("*.svg"):
        old.unlink()
    widths = {}
    for theme in THEMES:
        files = {"top": top(theme, total, this_year - 4), "hero": hero(theme), "graph": graph(theme, calendars),
                 "work-title": heading(theme, "Things I've", "made", f"({len(WORK):02d})"),
                 "stack-title": heading(theme, "My", "toolbox", "always growing"),
                 "stack": marquee(theme), "outro": outro(theme)}
        for i, (slug, label, _) in enumerate(LINKS):
            files[f"link-{slug}"], widths[slug] = link(theme, label, i)
        for i, (slug, name, text, tech, _) in enumerate(WORK):
            files[f"work-{slug}"] = work(theme, slug, name, text, tech, i)
        for name, content in files.items():
            (ASSETS / f"{name}-{theme}.svg").write_text(content, encoding="utf-8")

    # GitHub caches images hard: change the query string only when the content changes
    v = f"{total}-{sum(len(w[2]) for w in WORK) + len(BLURB[0])}"
    links = "\n".join(f'<a href="{url}">{picture(f"link-{slug}", label, v, str(round(widths[slug] * 0.7)))}</a>'
                      for slug, label, url in LINKS)
    work_rows = "\n".join(f'<a href="{url}">{picture(f"work-{slug}", f"{name}: {text}", v)}</a>'
                          for slug, name, text, _, url in WORK)
    readme = f"""{picture("top", f"Ons Kouki · {total} contributions", v)}

{links}

{picture("hero", f"Ons Kouki, {ROLE}. I dream it, sketch it, build it, train it, ship it, scale it.", v)}

{picture("graph", "Contribution graph", v)}

{picture("work-title", "Things I've made", v)}
{work_rows}

{picture("stack-title", "My toolbox", v)}
{picture("stack", "; ".join(f"{a}: {', '.join(b)}" for a, b in STACK), v)}

{picture("outro", "To be continued. Got a wild idea? Let's build it.", v)}
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(f"{total} contributions, {len(list(ASSETS.glob('*.svg')))} svgs")


if __name__ == "__main__":
    build()
