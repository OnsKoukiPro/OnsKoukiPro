"""Build the profile README and its animated line-art SVGs (light + dark).

Usage: python scripts/build.py
Fetches the public contribution calendar, writes assets/*.svg and README.md.
Headlines are drawn stroke by stroke from Relief SingleLine (a single-line plotter font, SIL OFL),
stored as path data in fonts/relief-singleline.json. Everything else is set in JetBrains Mono (SIL OFL).
"""
import base64
import datetime as dt
import json
import math
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
    "light": {"ink": "#0f1115", "muted": "#6b7280", "faint": "#d0d4da", "grid": "#e3e6ea", "bg": "#ffffff",
              "acc": "#ff4f1f", "live": "#16a34a"},
    "dark": {"ink": "#e6edf3", "muted": "#8b949e", "faint": "#30363d", "grid": "#1f252d", "bg": "#0d1117",
             "acc": "#ff6a3d", "live": "#3fb950"},
}

ROLE = "Creative Technologist"
WORDS = ["dream it", "design it", "build it", "train it", "ship it", "scale it"]
FIELDS = ["AI/ML", "Software Engineering", "Cloud Infrastructure"]

FEATURED = ("claritychains", "AI · PROCUREMENT", "ClarityChains",
            "LLM agents that read supplier offers, flag the traps and pick a winner. "
            "Concept, UX, models, backend and deployment, end to end.",
            "React · Django · FastAPI · LangChain · Azure OpenAI", "https://clarity-chains.vercel.app")
WORK = [
    ("model", "FORECASTING", "claritychains-model",
     "Price forecasts and a hedging optimiser for lithium, cobalt and nickel.",
     "Python · Streamlit · SciPy", f"https://github.com/{USER}/claritychains-model"),
    ("honeypot", "SECURITY", "Honeypot-CK8s",
     "A honeynet inside a vCluster. Attackers get in, I get dashboards.",
     "Kubernetes · Fluentd · OpenSearch", f"https://github.com/{USER}/Honeypot-CK8s"),
    ("rl-ddos", "NETWORKS · RL", "RL × SDN",
     "A network that learns when to block a flood. 94.6% detection.",
     "Ryu · Mininet · TensorFlow",
     f"https://github.com/{USER}/RL-based-DDos-Mitigation-in-SDN-based-broadband-networks"),
    ("car-price", "MACHINE LEARNING", "Car Price ML",
     "Scraped 4 marketplaces to price a used car. R² 0.75.",
     "BeautifulSoup · pandas · scikit-learn", f"https://github.com/{USER}/ML-Car-Price-Prediction"),
]

LINKS = [
    ("linkedin", "LinkedIn", "https://www.linkedin.com/in/ons-kouki/", True),
    ("email", "Email", "mailto:ons.koukipro@gmail.com", False),
    ("demo", "Live demo", "https://clarity-chains.vercel.app", False),
]

STACK = [
    ("ML & Data", ["PyTorch", "TensorFlow", "scikit-learn", "LangChain", "pandas", "Airflow", "Druid", "Superset"]),
    ("Backend", ["Python", "FastAPI", "Django", "NestJS", "Node.js", "Spring", "PostgreSQL", "Redis"]),
    ("Cloud", ["AWS", "Azure", "Kubernetes", "Helm", "Argo CD", "Terraform", "Pulumi", "GitHub Actions"]),
    ("Security & Web", ["Vault", "Keycloak", "OpenSearch", "Grafana", "TypeScript", "React", "Next.js", "Angular"]),
]

FONT_FACES = {  # css class -> (family, weight, file)
    "m": ("JBMono", 400, "jbmono-400"),
    "mb": ("JBMonoBold", 700, "jbmono-700"),
}
FALLBACK = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
MONO = 0.6  # JetBrains Mono advance in em
LINE_GLYPHS = json.loads((FONTS / "relief-singleline.json").read_text(encoding="utf-8"))

EASE = ".65 0 .35 1"
BASE_CSS = """
.f { opacity: 0; animation: fade 1s ease-out forwards; }
.dw { stroke-dasharray: 1 1; stroke-dashoffset: 1; animation: draw 1.1s cubic-bezier(.65,0,.35,1) forwards; }
.blink { animation: blink 1.1s steps(1) infinite; }
@keyframes fade { to { opacity: 1; } }
@keyframes draw { to { stroke-dashoffset: 0; } }
@keyframes blink { 50% { opacity: 0; } }
"""


def font_css(body):
    """Embed only the fonts whose class is used in this SVG."""
    used = {c for classes in re.findall(r'class="([^"]+)"', body) for c in classes.split()}
    css = []
    for cls, (family, weight, file) in FONT_FACES.items():
        if cls in used:
            data = base64.b64encode((FONTS / f"{file}.woff2").read_bytes()).decode()
            css.append(f"@font-face{{font-family:{family};font-weight:{weight};"
                       f"src:url(data:font/woff2;base64,{data}) format('woff2')}}"
                       f".{cls}{{font-family:{family},{FALLBACK};font-weight:{weight}}}")
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


def svg(width, height, body, label, css=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" fill="none" role="img" aria-label="{escape(label)}">
<style>{font_css(body)}{BASE_CSS}{css}</style>
{body}
</svg>
"""


def delay(s):
    return f'style="animation-delay:{s:.2f}s"'


def mono(text, x, y, size, fill, bold=False, anchor="start", spacing=0, extra=""):
    cls = "mb" if bold else "m"
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text class="{cls}{" " + extra if extra else ""}" x="{x:.1f}" y="{y:.1f}" font-size="{size}"{ls} '
            f'text-anchor="{anchor}" fill="{fill}" xml:space="preserve">{escape(text)}</text>')


def mono_width(text, size, spacing=0):
    return len(text) * (size * MONO + spacing)


def wrap(text, size, width):
    lines, line, limit = [], "", int(width // (size * MONO))
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if len(candidate) > limit and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    return lines + [line]


def line_width(text, size, track=0):
    return sum(LINE_GLYPHS.get(c, [280])[0] for c in text) * size / 1000 + track * (len(text) - 1)


def line_text(text, x, y, size, color, stroke=2.4, start=0.0, per=0.07, anchor="start", track=0):
    """Plotter lettering: each glyph is one open stroke that draws itself, left to right."""
    s = size / 1000
    if anchor != "start":
        x -= line_width(text, size, track) / (2 if anchor == "middle" else 1)
    paths, k = [], 0
    for ch in text:
        adv, d = LINE_GLYPHS.get(ch, [280, ""])
        if d:
            paths.append(f'<path class="dw" style="animation-delay:{start + k * per:.2f}s" pathLength="1" d="{d}" '
                         f'transform="translate({x:.1f} {y:.1f}) scale({s:.4f} {-s:.4f})" stroke-width="{stroke / s:.1f}"/>')
            k += 1
        x += adv * s + track
    return (f'<g stroke="{color}" stroke-linecap="round" stroke-linejoin="round">{"".join(paths)}</g>', x)


def crop_marks(t, w, h, inset=10, arm=16):
    """Registration corners like on a print proof."""
    out = []
    for cx, sx in ((inset, 1), (w - inset, -1)):
        for cy, sy in ((inset, 1), (h - inset, -1)):
            out.append(f"M{cx} {cy + sy * arm} V{cy} H{cx + sx * arm}")
    return f'<path class="f" d="{" ".join(out)}" stroke="{t["muted"]}" stroke-width="1.4"/>'


def crosshair(x, y, t, r=7):
    return (f'<g class="f" {delay(0.6)} stroke="{t["muted"]}" stroke-width="1"><path d="M{x - r * 1.8} {y} H{x + r * 1.8} M{x} {y - r * 1.8} V{y + r * 1.8}"/>'
            f'<circle cx="{x}" cy="{y}" r="{r}"/></g>')


def dot_grid(t, w, h, step=24):
    return (f'<defs><pattern id="grid" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
            f'<circle cx="{step / 2}" cy="{step / 2}" r="1.1" fill="{t["grid"]}"/></pattern></defs>'
            f'<rect class="f" width="{w}" height="{h}" fill="url(#grid)"/>')


def top(theme, total, since):
    t = THEMES[theme]
    ticks = []
    for i, x in enumerate(range(0, W + 1, 12)):
        h = 12 if x % 120 == 0 else 7 if x % 60 == 0 else 4
        ticks.append(f"M{min(max(x, 0.75), W - 0.75)} 62 V{62 - h}")
    body = f"""{mono("ONS.KOUKI", 0, 26, 16, t["ink"], bold=True, spacing=2, extra="f")}
<g class="f" {delay(0.2)}>{mono(f"{total:,} CONTRIBUTIONS · SINCE {since}", W / 2, 26, 14, t["muted"], anchor="middle", spacing=1.5)}</g>
<g class="f" {delay(0.3)}><circle cx="{W - mono_width("README.MD", 14, 1.5) - 18}" cy="21" r="4" fill="{t["acc"]}" class="blink"/>{mono("README.MD", W, 26, 14, t["muted"], anchor="end", spacing=1.5)}</g>
<clipPath id="reveal"><rect width="0" height="70"><animate attributeName="width" from="0" to="{W}" dur="1.6s" begin="0.2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="{EASE}"/></rect></clipPath>
<g clip-path="url(#reveal)" stroke="{t["faint"]}" stroke-width="1.5"><path d="{" ".join(ticks)}"/><path d="M0 62.25 H{W}"/></g>"""
    return svg(W, 64, body, f"Ons Kouki · {total} contributions since {since}")


def globe(cx, cy, r, t):
    """Wireframe globe: latitude rings stay put, meridians breathe to fake a rotation."""
    out = [f'<circle class="dw" {delay(0.4)} pathLength="1" cx="{cx}" cy="{cy}" r="{r}" stroke="{t["ink"]}" stroke-width="1.6"/>']
    for k, lat in enumerate((-60, -30, 0, 30, 60)):
        a = math.radians(lat)
        rx = r * math.cos(a)
        out.append(f'<ellipse class="dw" {delay(0.6 + k * 0.08)} pathLength="1" cx="{cx}" cy="{cy + r * math.sin(a):.1f}" rx="{rx:.1f}" ry="{rx * 0.16:.1f}" '
                   f'stroke="{t["muted"]}" stroke-width="1"/>')
    samples, n = 24, 6
    for m in range(n):
        phase = math.pi * m / n
        vals = ";".join(f"{r * abs(math.sin(phase + math.pi * s / samples)):.1f}" for s in range(samples + 1))
        out.append(f'<ellipse class="f" {delay(1.0)} cx="{cx}" cy="{cy}" ry="{r}" rx="{r * abs(math.sin(phase)):.1f}" stroke="{t["muted"]}" stroke-width="1">'
                   f'<animate attributeName="rx" values="{vals}" dur="16s" repeatCount="indefinite"/></ellipse>')
    # tilted orbit with a satellite
    orbit = f"M{cx - r * 1.32},{cy} a{r * 1.32},{r * 0.36} 0 1,0 {r * 2.64},0 a{r * 1.32},{r * 0.36} 0 1,0 {-r * 2.64},0"
    out.append(f'<g transform="rotate(-18 {cx} {cy})"><path class="f" {delay(1.2)} d="{orbit}" stroke="{t["acc"]}" stroke-width="1.2" stroke-dasharray="2 6"/>'
               f'<g class="f" {delay(1.4)}><circle r="5" fill="{t["acc"]}"><animateMotion dur="9s" repeatCount="indefinite" path="{orbit}"/></circle>'
               f'<circle r="12" stroke="{t["acc"]}" stroke-width="1"><animateMotion dur="9s" repeatCount="indefinite" path="{orbit}"/>'
               f'<animate attributeName="r" values="6;16;6" dur="2s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;0;1" dur="2s" repeatCount="indefinite"/></circle></g></g>')
    # dimension: radius
    out.append(f'<g class="f" {delay(1.6)} stroke="{t["muted"]}" stroke-width="1"><path d="M{cx} {cy} L{cx + r * 0.71:.1f} {cy - r * 0.71:.1f}"/><circle cx="{cx}" cy="{cy}" r="2.5" fill="{t["muted"]}"/></g>')
    out.append(f'<g class="f" {delay(1.7)}>{mono("R 1.0 · WORLD", cx + r * 0.74, cy - r * 0.74 - 8, 12, t["muted"], spacing=1)}</g>')
    return "\n".join(out)


def typer(x, y, size, t, start=1.8, cycle=2.6):
    """Terminal prompt that types each word, holds it, then wipes it."""
    cw, total = size * MONO, len(WORDS) * cycle
    clips, texts, cur_x, cur_t = [], [], [], []
    for i, word in enumerate(WORDS):
        steps = [k * 0.07 for k in range(len(word) + 1)]
        times = [0] + steps[1:] + [cycle - 0.35, cycle - 0.34]
        widths = [0] + [k * cw for k in range(1, len(word) + 1)] + [len(word) * cw, 0]
        key = ";".join(f"{v / total:.4f}" for v in times + [total])
        clips.append(f'<clipPath id="tw{i}"><rect x="{x}" y="{y - size}" height="{size * 1.4}" width="0">'
                     f'<animate attributeName="width" values="{";".join(f"{v:.1f}" for v in widths + [0])}" keyTimes="{key}" calcMode="discrete" '
                     f'dur="{total}s" begin="{start + i * cycle:.2f}s" repeatCount="indefinite"/></rect></clipPath>')
        texts.append(f'<g clip-path="url(#tw{i})">{mono(word, x, y, size, t["ink"], bold=True)}</g>')
        for tm, wd in zip(times, widths):
            cur_t.append((i * cycle + tm) / total)
            cur_x.append(x + wd + 4)
    # SMIL keyTimes need to start at 0 and end at 1, strictly ordered
    pairs = sorted(set(zip([round(v, 4) for v in cur_t], cur_x)))
    keys, vals, seen = [], [], set()
    for k, v in pairs:
        if k not in seen and k < 1:
            keys.append(k)
            vals.append(v)
            seen.add(k)
    cursor = (f'<rect class="blink" x="{x}" y="{y - size * 0.82:.1f}" width="{cw * 0.62:.1f}" height="{size * 0.98:.1f}" fill="{t["acc"]}">'
              f'<animate attributeName="x" values="{";".join(f"{v:.1f}" for v in vals)}" keyTimes="{";".join(f"{k:.4f}" for k in keys)}" '
              f'calcMode="discrete" dur="{total}s" begin="{start:.2f}s" repeatCount="indefinite"/></rect>')
    return "\n".join(clips + texts) + "\n" + cursor


def hero(theme):
    t = THEMES[theme]
    h, x0 = 560, 48
    name, name_end = line_text("Ons Kouki", x0, 268, 150, t["ink"], stroke=3.2, start=0.3, per=0.16)
    mid = (x0 + name_end) / 2
    dim_label = "IDEA → PRODUCTION"
    lw = mono_width(dim_label, 13, 2) + 24
    fields = "  /  ".join(f.upper() for f in FIELDS)
    body = f"""{dot_grid(t, W, h)}
{crop_marks(t, W, h)}
<g class="f" {delay(0.1)}><rect x="{x0}" y="62" width="10" height="10" fill="{t["acc"]}"/>{mono(f"FIG.00 — {ROLE.upper()}", x0 + 22, 72, 15, t["ink"], bold=True, spacing=2)}</g>
<g class="f" {delay(0.2)}>{mono("SCALE 1:1 · REV " + str(dt.date.today().year), W - 48, 72, 13, t["muted"], anchor="end", spacing=1.5)}</g>
{name}
<g class="f" {delay(1.6)} stroke="{t["muted"]}" stroke-width="1.2">
  <path d="M{x0} 300 V324 M{name_end} 300 V324 M{x0} 312 H{mid - lw / 2:.1f} M{mid + lw / 2:.1f} 312 H{name_end}"/>
  <path d="M{x0 + 10} 307 L{x0} 312 L{x0 + 10} 317 M{name_end - 10} 307 L{name_end} 312 L{name_end - 10} 317"/>
</g>
<g class="f" {delay(1.7)}>{mono(dim_label, mid, 317, 13, t["muted"], anchor="middle", spacing=2)}</g>
<g class="f" {delay(1.6)}>{mono("~/ons $", x0, 410, 34, t["acc"], bold=True)}</g>
{typer(x0 + mono_width("~/ons $ ", 34), 410, 34, t)}
<g class="f" {delay(2.0)}><path d="M{x0} 470.5 H{x0 + 40}" stroke="{t["acc"]}" stroke-width="2"/>{mono(fields, x0, 500, 15, t["muted"], spacing=2)}</g>
{crosshair(1150, 512, t)}
{globe(960, 270, 140, t)}"""
    return svg(W, h, body, f"Ons Kouki, {ROLE}. Idea to production: {', '.join(WORDS)}. {', '.join(FIELDS)}")


def button(theme, label, filled, i):
    """Outlined key with accent corner ticks and an arrow that nudges every few seconds."""
    t = THEMES[theme]
    size, sp, h = 16, 2, 54
    text = label.upper()
    width = round(mono_width(text, size, sp) + 86)
    fill, color = (t["ink"], t["bg"]) if filled else ("none", t["ink"])
    ticks = f"M1 13 V1 H13 M{width - 13} 1 H{width - 1} V13 M1 {h - 13} V{h - 1} H13 M{width - 13} {h - 1} H{width - 1} V{h - 13}"
    hop = f'values="0 0;3 -3;0 0;0 0" keyTimes="0;0.05;0.1;1" dur="5s" begin="{2 + i * 1.6:.1f}s" repeatCount="indefinite"'
    body = f"""<g class="f" {delay(0.6 + i * 0.12)}>
<rect x="5" y="5" width="{width - 10}" height="{h - 10}" fill="{fill}" stroke="{t["ink"]}" stroke-width="1.4"/>
<path class="dw" {delay(0.8 + i * 0.12)} pathLength="1" d="{ticks}" stroke="{t["acc"]}" stroke-width="2"/>
{mono(text, 26, 33, size, color, bold=True, spacing=sp)}
<g transform="translate({width - 42} 19)"><path d="M2 14 L14 2 M5 2 H14 V11" stroke="{t["acc"]}" stroke-width="2.2" stroke-linecap="square">
<animateTransform attributeName="transform" type="translate" {hop}/></path></g>
</g>"""
    return svg(width, h, body, label), width


def graph(theme, calendars):
    t = THEMES[theme]
    gap, ygap = 1.8, 26
    years = sorted(calendars)
    block = (W - ygap * (len(years) - 1)) / len(years)
    step = block / 53
    cell = step - gap
    gy = 50
    alphas = [0, 0.3, 0.55, 0.8, 1]
    legend_x = W - 5 * (cell + 6) - mono_width(" MORE", 12, 1)
    legend = "".join(f'<rect class="l{i}" x="{legend_x + i * (cell + 6):.1f}" y="13" width="{cell:.1f}" height="{cell:.1f}"/>' for i in range(5))
    out = [f'<g class="f" {delay(0.1)}>{mono("FIG.01 — ACTIVITY.LOG", 0, 24, 15, t["ink"], bold=True, spacing=2)}</g>',
           f'<g class="f" {delay(0.2)}>{mono("LESS", legend_x - 10, 22, 12, t["muted"], anchor="end", spacing=1)}{legend}'
           f'{mono("MORE", W, 22, 12, t["muted"], anchor="end", spacing=1)}</g>']
    for yi, year in enumerate(years):
        x0 = yi * (block + ygap)
        jan1 = dt.date(year, 1, 1)
        offset = (jan1.weekday() + 1) % 7  # Sunday-first rows, like GitHub
        rects = []
        for date, level in sorted(calendars[year].items()):
            col, row = divmod((date - jan1).days + offset, 7)
            rects.append(f'<rect class="d l{level}" style="animation-delay:{0.3 + yi * 0.3 + col * 0.015:.2f}s" '
                         f'x="{x0 + col * step + 0.5:.1f}" y="{gy + row * step + 0.5:.1f}" width="{cell - 1:.1f}" height="{cell - 1:.1f}"/>')
        out.append("".join(rects))
        out.append(f'<g class="f" {delay(0.3 + yi * 0.3)}><path d="M{x0} {gy + 7 * step + 12:.1f} H{x0 + block - 4:.1f}" stroke="{t["faint"]}"/>'
                   f'{mono(str(year), x0, gy + 7 * step + 32, 13, t["muted"], spacing=1.5)}</g>')
    height = gy + 7 * step + 40
    # a scan line sweeping over the grid
    out.append(f'<defs><linearGradient id="scan" x1="0" x2="1"><stop offset="0" stop-color="{t["acc"]}" stop-opacity="0"/>'
               f'<stop offset="1" stop-color="{t["acc"]}" stop-opacity="0.22"/></linearGradient></defs>'
               f'<g><rect x="-80" y="{gy - 6}" width="80" height="{7 * step + 10:.1f}" fill="url(#scan)"/>'
               f'<path d="M0 {gy - 6} V{gy + 7 * step + 4:.1f}" stroke="{t["acc"]}" stroke-width="1.5"/>'
               f'<animateTransform attributeName="transform" type="translate" values="-10 0;{W + 90} 0" dur="7s" begin="2s" repeatCount="indefinite"/></g>')
    css = (f".l0{{fill:none;stroke:{t['faint']};stroke-width:1}}"
           + "".join(f".l{i}{{fill:{t['acc']};fill-opacity:{a}}}" for i, a in enumerate(alphas) if i)
           + ".d{opacity:0;animation:fade .6s ease-out forwards}")
    return svg(W, int(height), "\n".join(out), "Contribution activity", css)


def heading(theme, index, label, title, note):
    """Section index, a hand-drawn title and a rule that runs to the edge."""
    t = THEMES[theme]
    drawn, end = line_text(title, 0, 112, 70, t["ink"], stroke=2.6, start=0.2, per=0.06)
    body = f"""<g class="f" {delay(0.05)}>{mono(index, 0, 30, 15, t["acc"], bold=True, spacing=2)}{mono("/ " + label, 34, 30, 15, t["muted"], spacing=2)}</g>
{drawn}
<path class="dw" {delay(0.8)} pathLength="1" d="M{end + 28:.0f} 104.5 H{W - 8}" stroke="{t["faint"]}" stroke-width="1.5"/>
<circle class="f" {delay(1.6)} cx="{W - 5}" cy="104.5" r="4.5" stroke="{t["acc"]}" stroke-width="1.6"/>
<g class="f" {delay(1.2)}>{mono(note, W - 20, 90, 13, t["muted"], anchor="end", spacing=2)}</g>"""
    return svg(W, 132, body, f"{title}. {note}")


def glyph(slug, t):
    """Small looping line drawing that hints at each project, in a 64×64 box."""
    a, ink, muted = t["acc"], t["ink"], t["muted"]
    if slug == "claritychains":  # linked rings turning
        rings = "".join(f'<circle cx="{32 + 10 * math.cos(k * 2.094):.1f}" cy="{32 + 10 * math.sin(k * 2.094):.1f}" r="12" stroke="{ink}" stroke-width="1.2"/>' for k in range(3))
        return (f'<circle cx="32" cy="32" r="29" stroke="{muted}" stroke-width="0.6" stroke-dasharray="1.5 3"/>'
                f'<g>{rings}<animateTransform attributeName="transform" type="rotate" values="0 32 32;360 32 32" dur="14s" repeatCount="indefinite"/></g>'
                f'<circle cx="32" cy="32" r="3" fill="{a}"><animate attributeName="r" values="2;3.5;2" dur="2.4s" repeatCount="indefinite"/></circle>')
    if slug == "model":  # a price line drawing itself into a forecast cone
        return (f'<path d="M40,31 L60,14 M40,31 L60,44" stroke="{muted}" stroke-width="1" stroke-dasharray="2 2"/><path d="M40,31 L60,26" stroke="{a}" stroke-width="1.6"/>'
                f'<path d="M4,44 L14,38 L22,41 L32,28 L40,31" stroke="{ink}" stroke-width="1.8" stroke-linejoin="round" stroke-dasharray="60" stroke-dashoffset="60">'
                f'<animate attributeName="stroke-dashoffset" values="60;0;0;60" keyTimes="0;0.4;0.85;1" dur="4s" repeatCount="indefinite"/></path>'
                f'<path d="M4,56 H60 M4,56 V8" stroke="{muted}" stroke-width="1"/>')
    if slug == "honeypot":  # a hexagon cell with something buzzing around it
        hexagon = " ".join(f"{32 + 18 * math.cos(math.pi / 3 * k + math.pi / 6):.1f},{32 + 18 * math.sin(math.pi / 3 * k + math.pi / 6):.1f}" for k in range(6))
        inner = " ".join(f"{32 + 9 * math.cos(math.pi / 3 * k + math.pi / 6):.1f},{32 + 9 * math.sin(math.pi / 3 * k + math.pi / 6):.1f}" for k in range(6))
        return (f'<polygon points="{inner}" stroke="{muted}" stroke-width="1"/>'
                f'<polygon points="{hexagon}" stroke="{ink}" stroke-width="1.6" stroke-linejoin="round"><animateTransform attributeName="transform" type="rotate" values="0 32 32;60 32 32;60 32 32" keyTimes="0;0.3;1" dur="5s" repeatCount="indefinite" calcMode="spline" keySplines="{EASE};0 0 1 1"/></polygon>'
                f'<circle r="2.6" fill="{a}"><animateMotion dur="3s" repeatCount="indefinite" path="M32,6 C62,6 62,58 32,58 C2,58 2,6 32,6Z"/></circle>')
    if slug == "rl-ddos":  # packets hitting a wall, only one gets through
        pulses = "".join(f'<rect x="-2" y="-2" width="4" height="4" fill="{ink}"><animateMotion path="M2,32 H40" dur="1.8s" begin="{k * 0.6:.1f}s" repeatCount="indefinite"/>'
                         f'<animate attributeName="opacity" values="1;1;0" keyTimes="0;0.85;1" dur="1.8s" begin="{k * 0.6:.1f}s" repeatCount="indefinite"/></rect>' for k in range(3))
        return (f'<line x1="2" y1="32" x2="62" y2="32" stroke="{muted}" stroke-width="1" stroke-dasharray="2 2"/>{pulses}'
                f'<rect x="42" y="14" width="5" height="36" stroke="{ink}" stroke-width="1.4"/>'
                f'<rect x="-2" y="-2" width="4" height="4" fill="{a}"><animateMotion path="M47,32 H62" dur="1.8s" repeatCount="indefinite"/></rect>')
    if slug == "car-price":  # a gauge settling on a price
        times = f'keyTimes="0;0.3;0.5;0.75;1" calcMode="spline" keySplines="{";".join([EASE] * 4)}"'
        ticks = " ".join(f"M{32 + 27 * math.cos(math.pi * (1 + k / 8)):.1f} {44 + 27 * math.sin(math.pi * (1 + k / 8)):.1f} L{32 + 31 * math.cos(math.pi * (1 + k / 8)):.1f} {44 + 31 * math.sin(math.pi * (1 + k / 8)):.1f}" for k in range(9))
        return (f'<path d="{ticks}" stroke="{muted}" stroke-width="1"/><path d="M8,44 A24,24 0 0 1 56,44" stroke="{muted}" stroke-width="1"/>'
                f'<line x1="32" y1="44" x2="32" y2="22" stroke="{a}" stroke-width="1.8">'
                f'<animateTransform attributeName="transform" type="rotate" values="-80 32 44;35 32 44;-10 32 44;70 32 44;-80 32 44" dur="5s" repeatCount="indefinite" {times}/></line>'
                f'<circle cx="32" cy="44" r="3" stroke="{ink}" stroke-width="1.4"/>')
    return ""


def card(theme, slug, eyebrow, title, text, tech, width, i, live=False):
    """Spec sheet: hairline frame, accent corners, drawn title, mono copy and a looping line drawing."""
    t = THEMES[theme]
    h, pad = 300, 40
    wide = width > 800
    gs = 2.8 if wide else 1.25
    gsize = 64 * gs
    text_area = width - pad * 2 - (gsize + 60 if wide else 0)
    title_room = text_area - (110 if live else 0) - (0 if wide else 56)
    size = min(52, title_room / line_width(title, 1))
    drawn, title_end = line_text(title, pad, 122, size, t["ink"], stroke=2.2, start=0.3 + i * 0.1, per=0.05)
    lines = wrap(text, 16, text_area)
    copy = "".join(mono(line, pad, 166 + k * 25, 16, t["muted"]) for k, line in enumerate(lines))
    gx, gy = (width - pad - gsize - 20, (h - gsize) / 2 + 6) if wide else (width - pad - gsize + 4, h - pad - gsize + 14)
    corners = (f"M0.75 18 V0.75 H18 M{width - 18} 0.75 H{width - 0.75} V18 "
               f"M0.75 {h - 18} V{h - 0.75} H18 M{width - 18} {h - 0.75} H{width - 0.75} V{h - 18}")
    badge = ""
    if live:
        badge = f'''<g class="f" {delay(1.2)} transform="translate({title_end + 22:.0f} 94)"><rect x="0.75" y="0.75" width="82" height="28" stroke="{t["live"]}" stroke-width="1.4"/>
<circle cx="17" cy="15" r="4.5" fill="{t["live"]}"><animate attributeName="opacity" values="1;.2;1" dur="1.6s" repeatCount="indefinite"/></circle>
{mono("LIVE", 50, 20, 13, t["live"], bold=True, anchor="middle", spacing=2)}</g>'''
    hop = f'values="0 0;3 -3;0 0;0 0" keyTimes="0;0.05;0.1;1" dur="5s" begin="{3 + i * 1.3:.1f}s" repeatCount="indefinite"'
    body = f"""<g class="f" {delay(0.1 + i * 0.1)}>
<rect x="0.75" y="0.75" width="{width - 1.5}" height="{h - 1.5}" stroke="{t["faint"]}" stroke-width="1.5"/>
<g transform="translate({gx:.0f} {gy:.0f}) scale({gs})">{glyph(slug, t)}</g>
{mono(f"P.{i:02d}", pad, 52, 13, t["acc"], bold=True, spacing=2)}{mono("— " + eyebrow, pad + mono_width("P.00 ", 13, 2), 52, 13, t["muted"], spacing=2)}
{copy}
{mono("› " + tech, pad, h - 34, 14, t["ink"])}
<g transform="translate({width - pad - 36} 24)"><rect x="0.75" y="0.75" width="34.5" height="34.5" stroke="{t["faint"]}" stroke-width="1.5"/>
<path d="M12 24 L24 12 M15 12 H24 V21" stroke="{t["ink"]}" stroke-width="1.8" stroke-linecap="square"><animateTransform attributeName="transform" type="translate" {hop}/></path></g>
</g>
<path class="dw" {delay(0.3 + i * 0.1)} pathLength="1" d="{corners}" stroke="{t["acc"]}" stroke-width="2"/>
{drawn}
{badge}"""
    return svg(round(width), h, body, f"{title}: {text}")


def circuit(theme):
    """Toolbox as a circuit: each category is a trace, each tool a chip; a pulse lights them up in turn."""
    t = THEMES[theme]
    size, sp, row_h, chip_h, x_node, top_y = 14, 0.5, 84, 36, 236, 36
    x_end = W - 8
    out = [f'<path class="dw" {delay(0.1)} pathLength="1" d="M{x_node} {top_y} V{top_y + (len(STACK) - 1) * row_h}" stroke="{t["faint"]}" stroke-width="1.5"/>']
    for r, (label, items) in enumerate(STACK):
        y = top_y + r * row_h
        dur = 6 + r * 0.9
        begin = 1.2 + r * 0.7
        widths = [mono_width(item, size, sp) + 26 for item in items]
        span = x_end - 24 - (x_node + 24)
        gap = (span - sum(widths)) / (len(items) - 1)
        chips, x = [], x_node + 24
        for k, (item, cw) in enumerate(zip(items, widths)):
            p = (x + cw / 2 - x_node) / (x_end - x_node)
            keys = f"0;{max(p - 0.04, 0.001):.3f};{p:.3f};{min(p + 0.12, 0.999):.3f};1"
            chips.append(f'<g class="f" {delay(0.4 + r * 0.12 + k * 0.05)}><rect x="{x:.1f}" y="{y - chip_h / 2}" width="{cw:.1f}" height="{chip_h}" fill="{t["bg"]}" stroke="{t["faint"]}" stroke-width="1.4">'
                         f'<animate attributeName="stroke" values="{t["faint"]};{t["faint"]};{t["acc"]};{t["faint"]};{t["faint"]}" keyTimes="{keys}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/></rect>'
                         f'{mono(item, x + cw / 2, y + 5, size, t["ink"], anchor="middle", spacing=sp)}</g>')
            x += cw + gap
        trace = f"M{x_node} {y} H{x_end}"
        out.append(f'''<path class="dw" {delay(0.2 + r * 0.12)} pathLength="1" d="{trace}" stroke="{t["faint"]}" stroke-width="1.5"/>
<circle class="f" {delay(0.3 + r * 0.12)} cx="{x_node}" cy="{y}" r="4" fill="{t["bg"]}" stroke="{t["acc"]}" stroke-width="1.6"/>
<rect class="f" {delay(0.3 + r * 0.12)} x="{x_end - 3}" y="{y - 3}" width="6" height="6" fill="{t["muted"]}"/>
<g class="f" {delay(0.15 + r * 0.12)}>{mono(f"{r + 1:02d}", 0, y + 5, 13, t["acc"], bold=True, spacing=1.5)}{mono(label.upper(), 34, y + 5, 14, t["ink"], bold=True, spacing=1.5)}</g>
<g class="f" {delay(1)}><circle r="3.5" fill="{t["acc"]}"><animateMotion path="{trace}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/></circle></g>
{"".join(chips)}''')
    height = top_y + (len(STACK) - 1) * row_h + 40
    return svg(W, height, "\n".join(out), "Toolbox: " + "; ".join(f"{a}: {', '.join(b)}" for a, b in STACK))


def outro(theme):
    t = THEMES[theme]
    h = 300
    drawn, _ = line_text("To be continued", W / 2, 140, 96, t["ink"], stroke=2.8, start=0.2, per=0.07, anchor="middle")
    prompt = "> got a wild idea? let's build it"
    pw = mono_width(prompt, 22)
    body = f"""{crop_marks(t, W, h)}
{drawn}
<g class="f" {delay(1.4)}>{mono(prompt, W / 2 - 8, 202, 22, t["muted"], anchor="middle")}
<rect class="blink" x="{W / 2 - 8 + pw / 2 + 6:.1f}" y="184" width="10" height="22" fill="{t["acc"]}"/></g>
<g class="f" {delay(1.8)}><path d="M{W / 2 - 230} 258.5 H{W / 2 - 110} M{W / 2 + 110} 258.5 H{W / 2 + 230}" stroke="{t["faint"]}" stroke-width="1.5"/>
{mono("EN · FR · AR — EOF", W / 2, 263, 13, t["muted"], anchor="middle", spacing=2)}</g>"""
    return svg(W, h, body, "To be continued. Got a wild idea? Let's build it. Speaks English, French and Arabic.")


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
    small = (W - 20) / 2
    for theme in THEMES:
        files = {"top": top(theme, total, this_year - 4), "hero": hero(theme), "graph": graph(theme, calendars),
                 "work-title": heading(theme, "02", "WORK", "Things I've made", "BUILT END TO END"),
                 "stack-title": heading(theme, "03", "STACK", "Toolbox", "ALWAYS GROWING"),
                 "stack": circuit(theme), "outro": outro(theme)}
        slug, eyebrow, title, text, tech, _ = FEATURED
        files[f"card-{slug}"] = card(theme, slug, eyebrow, title, text, tech, W, 1, live=True)
        for i, (slug, eyebrow, title, text, tech, _) in enumerate(WORK):
            files[f"card-{slug}"] = card(theme, slug, eyebrow, title, text, tech, small, i + 2)
        for i, (slug, label, _, filled) in enumerate(LINKS):
            files[f"button-{slug}"], widths[slug] = button(theme, label, filled, i)
        for name, content in files.items():
            (ASSETS / f"{name}-{theme}.svg").write_text(content, encoding="utf-8")

    # GitHub caches images hard: change the query string only when the content changes
    v = f"{total}-l1"
    scale = 830 / W  # README column width in px over the SVG viewBox width
    buttons = "\n  ".join(f'<a href="{url}">{picture(f"button-{slug}", label, v, str(round(widths[slug] * scale)))}</a>'
                          for slug, label, url, _ in LINKS)
    pct = "49.6%"  # two cards plus the inline space between them fill the column
    cards = [f'<a href="{w[5]}">{picture(f"card-{w[0]}", f"{w[2]}: {w[3]}", v, pct)}</a>' for w in WORK]
    readme = f"""{picture("top", f"Ons Kouki · {total} contributions", v)}

{picture("hero", f"Ons Kouki, {ROLE}. Idea to production: {', '.join(WORDS)}.", v)}

<p align="center">
  {buttons}
</p>

{picture("graph", "Contribution activity", v)}

{picture("work-title", "Things I've made. Built end to end.", v)}

<a href="{FEATURED[5]}">{picture(f"card-{FEATURED[0]}", f"{FEATURED[2]}: {FEATURED[3]}", v)}</a>
<p>
{cards[0]}
{cards[1]}
{cards[2]}
{cards[3]}
</p>

{picture("stack-title", "Toolbox. Always growing.", v)}

{picture("stack", "; ".join(f"{a}: {', '.join(b)}" for a, b in STACK), v)}

{picture("outro", "To be continued. Got a wild idea? Let's build it.", v)}
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(f"{total} contributions, {len(list(ASSETS.glob('*.svg')))} svgs")


if __name__ == "__main__":
    build()
