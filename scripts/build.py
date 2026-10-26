"""Build the profile README and its animated SVGs (light + dark).

Usage: python scripts/build.py
Fetches the public contribution calendar, writes assets/*.svg and README.md.
Fonts in fonts/ are pre-subset Inter woff2 files (SIL OFL) embedded into each SVG.
"""
import base64
import datetime as dt
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
    "light": {"text": "#1d1d1f", "muted": "#6e6e73", "line": "#d2d2d7", "card": "#f5f5f7", "accent": "#0071e3",
              "on_accent": "#ffffff", "grad": ["#2563eb", "#7c3aed", "#db2777"], "glow": 0.22,
              "dots": ["#ebebf0", "#c7d7fe", "#8fb0fb", "#4f7ef7", "#1d4fd8"]},
    "dark": {"text": "#f5f5f7", "muted": "#86868b", "line": "#3a3a3c", "card": "#1c1c1e", "accent": "#2997ff",
             "on_accent": "#ffffff", "grad": ["#60a5fa", "#a78bfa", "#f472b6"], "glow": 0.3,
             "dots": ["#1c1c1e", "#1e3a8a", "#1d4ed8", "#3b82f6", "#93c5fd"]},
}

EYEBROW = "Creative Technologist"
TAGLINE = "Idea to production."
WORDS = ["Dream it.", "Design it.", "Build it.", "Train it.", "Ship it.", "Scale it."]
FIELDS = "AI/ML  ·  Software Engineering  ·  Cloud Infrastructure"

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
     "Scraped four marketplaces to price a used car. R² 0.75.",
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
    "r": ("Inter", 400, "inter-400"),
    "md": ("InterMedium", 500, "inter-500"),
    "sb": ("InterSemibold", 600, "inter-600"),
    "b": ("InterDisplay", 700, "inter-display-700"),
}
FALLBACK = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Helvetica, Arial, sans-serif"
# average glyph advance in em, used to size pills and wrap text
ADVANCE = {"r": 0.52, "md": 0.54, "sb": 0.56, "b": 0.58}

EASE = ".45 0 .55 1"
BASE_CSS = """
.f { opacity: 0; animation: fade 1.2s ease-out forwards; }
.u { opacity: 0; animation: up 1.2s cubic-bezier(.16,1,.3,1) forwards; }
@keyframes fade { to { opacity: 1; } }
@keyframes up { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: none; } }
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


def svg(width, height, theme, body, label, css=""):
    t = THEMES[theme]
    g0, g1, g2 = t["grad"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" fill="none" role="img" aria-label="{escape(label)}">
<defs>
  <linearGradient id="grad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{g0}"/><stop offset="0.5" stop-color="{g1}"/><stop offset="1" stop-color="{g2}"/>
  </linearGradient>
  <radialGradient id="glowA"><stop offset="0" stop-color="{g0}" stop-opacity="{t['glow']}"/><stop offset="1" stop-color="{g0}" stop-opacity="0"/></radialGradient>
  <radialGradient id="glowB"><stop offset="0" stop-color="{g2}" stop-opacity="{t['glow'] * 0.8:.2f}"/><stop offset="1" stop-color="{g2}" stop-opacity="0"/></radialGradient>
</defs>
<style>{font_css(body)}{BASE_CSS}{css}</style>
{body}
</svg>
"""


def delay(s):
    return f'style="animation-delay:{s:.2f}s"'


def text_width(text, size, cls):
    return len(text) * size * ADVANCE[cls]


def wrap(text, size, width, cls="r"):
    lines, line = [], ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if text_width(candidate, size, cls) > width and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    return lines + [line]


def glow(cx, cy, rx, ry, which, dx, dur):
    """A soft radial light that drifts slowly. No blur filter, so no hard edges."""
    return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#{which})">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;{dx} {dx // 4};0 0" dur="{dur}s" '
            f'repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="{EASE};{EASE}"/></ellipse>')


def top(theme, total, since):
    t = THEMES[theme]
    body = f"""<text class="sb f" {delay(0.1)} x="0" y="30" font-size="22" letter-spacing="-0.3" fill="{t['text']}">Ons Kouki</text>
<text class="r f" {delay(0.3)} x="{W / 2}" y="30" text-anchor="middle" font-size="19" fill="{t['muted']}"><tspan class="sb" fill="{t['text']}">{total:,}</tspan> contributions since {since}</text>
<text class="r f" {delay(0.5)} x="{W}" y="30" text-anchor="end" font-size="19" fill="{t['muted']}">readme.md</text>
<line class="f" {delay(0.5)} x1="0" y1="52.5" x2="{W}" y2="52.5" stroke="{t['line']}"/>"""
    return svg(W, 56, theme, body, f"Ons Kouki · {total} contributions since {since}")


def hero(theme):
    t = THEMES[theme]
    n, cycle = len(WORDS), 2.4
    words = "".join(
        f'<text class="b w" style="animation-delay:{1.4 + i * cycle:.1f}s" x="{W / 2}" y="398" text-anchor="middle" '
        f'font-size="74" letter-spacing="-2.5" fill="url(#grad)">{escape(w)}</text>' for i, w in enumerate(WORDS))
    css = (f".w{{opacity:0;transform-box:fill-box;transform-origin:center;animation:word {n * cycle:.1f}s cubic-bezier(.16,1,.3,1) infinite}}"
           "@keyframes word{0%{opacity:0;transform:translateY(28px) scale(.96);filter:blur(10px)}"
           "4%,14%{opacity:1;transform:none;filter:blur(0)}"
           "18%{opacity:0;transform:translateY(-24px) scale(1.02);filter:blur(10px)}100%{opacity:0}}")
    body = f"""{glow(470, 270, 420, 230, "glowA", 90, 14)}
{glow(760, 300, 380, 210, "glowB", -80, 17)}
<text class="sb u" {delay(0.2)} x="{W / 2}" y="96" text-anchor="middle" font-size="24" fill="url(#grad)">{escape(EYEBROW)}</text>
<text class="b u" {delay(0.35)} x="{W / 2}" y="236" text-anchor="middle" font-size="152" letter-spacing="-6" fill="{t['text']}">Ons Kouki</text>
<text class="md u" {delay(0.6)} x="{W / 2}" y="314" text-anchor="middle" font-size="42" letter-spacing="-0.8" fill="{t['muted']}">{escape(TAGLINE)}</text>
{words}
<text class="r u" {delay(0.9)} x="{W / 2}" y="478" text-anchor="middle" font-size="22" fill="{t['muted']}" xml:space="preserve">{escape(FIELDS)}</text>"""
    return svg(W, 520, theme, body, f"Ons Kouki, {EYEBROW}. {TAGLINE} {' '.join(WORDS)} {FIELDS}", css)


def button(theme, label, filled, i):
    """Apple-style pill button with an arrow that nudges up-right every few seconds."""
    t = THEMES[theme]
    size = 22
    width = round(text_width(label, size, "sb") + 84)
    fill, stroke, color = (t["accent"], "none", t["on_accent"]) if filled else ("none", t["accent"], t["accent"])
    hop = f'values="0 0;3 -3;0 0;0 0" keyTimes="0;0.05;0.1;1" dur="5s" begin="{2 + i * 1.6:.1f}s" repeatCount="indefinite"'
    body = f"""<g class="u" {delay(1 + i * 0.12)}>
<rect x="1.5" y="1.5" width="{width - 3}" height="57" rx="28.5" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>
<text class="sb" x="30" y="37" font-size="{size}" letter-spacing="-0.2" fill="{color}">{escape(label)}</text>
<g transform="translate({width - 44} 24)"><path d="M2 12 L12 2 M4 2 H12 V10" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<animateTransform attributeName="transform" type="translate" {hop}/></path></g>
</g>"""
    return svg(width, 60, theme, body, label), width


def graph(theme, calendars):
    t = THEMES[theme]
    cell, gap, ygap = 6.2, 1.4, 22
    years = sorted(calendars)
    block = (W - ygap * (len(years) - 1)) / len(years)
    step = min(cell + gap, block / 53)
    gy = 52
    out = [f'<text class="sb f" {delay(0.2)} x="0" y="26" font-size="22" fill="{t["text"]}">Activity</text>',
           f'<text class="r f" {delay(0.3)} x="{W}" y="26" text-anchor="end" font-size="18" fill="{t["muted"]}">Less <tspan fill="{t["dots"][1]}">●</tspan> <tspan fill="{t["dots"][2]}">●</tspan> <tspan fill="{t["dots"][3]}">●</tspan> <tspan fill="{t["dots"][4]}">●</tspan> More</text>']
    for yi, year in enumerate(years):
        x0 = yi * (block + ygap)
        jan1 = dt.date(year, 1, 1)
        offset = (jan1.weekday() + 1) % 7  # Sunday-first rows, like GitHub
        rects = []
        for date, level in sorted(calendars[year].items()):
            col, row = divmod((date - jan1).days + offset, 7)
            appear = 0.4 + yi * 0.4 + col * 0.02
            wave = 4 + (yi * 53 + col) * 0.035  # a soft brightness wave, left to right
            rects.append(f'<rect class="d l{level}" style="animation-delay:{appear:.2f}s,{wave:.2f}s" '
                         f'x="{x0 + col * step:.1f}" y="{gy + row * step:.1f}" width="{step - gap:.1f}" height="{step - gap:.1f}" rx="2"/>')
        out.append("".join(rects))
        out.append(f'<text class="md f" {delay(0.4 + yi * 0.4)} x="{x0}" y="{gy + 7 * step + 30:.0f}" font-size="18" fill="{t["muted"]}">{year}</text>')
    css = ("".join(f".l{i}{{fill:{c}}}" for i, c in enumerate(t["dots"]))
           + ".d{opacity:0;animation:fade 1s ease-out forwards,pulse 7s ease-in-out infinite}"
           "@keyframes pulse{0%,100%{fill-opacity:1}6%{fill-opacity:.4}14%{fill-opacity:1}}")
    return svg(W, int(gy + 7 * step + 40), theme, "\n".join(out), "Contribution activity", css)


def heading(theme, bold, rest):
    """Two-tone headline: the statement, then a quieter follow-up."""
    t = THEMES[theme]
    body = f"""<text class="b u" {delay(0.15)} x="0" y="96" font-size="56" letter-spacing="-1.8"><tspan fill="{t['text']}">{escape(bold)}</tspan> <tspan fill="{t['muted']}">{escape(rest)}</tspan></text>"""
    return svg(W, 118, theme, body, f"{bold} {rest}")


def glyph(slug, t):
    """Small looping animation that hints at each project, drawn in a 64×64 box."""
    a, g, spline4 = t["accent"], "url(#grad)", ";".join([EASE] * 4)
    if slug == "claritychains":  # linked rings turning
        rings = "".join(f'<circle cx="{32 + 10 * math.cos(k * 2.094):.1f}" cy="{32 + 10 * math.sin(k * 2.094):.1f}" r="12" stroke="{g}" stroke-width="2"/>' for k in range(3))
        return (f'<g>{rings}<animateTransform attributeName="transform" type="rotate" values="0 32 32;360 32 32" dur="14s" repeatCount="indefinite"/></g>'
                f'<circle cx="32" cy="32" r="3" fill="{a}"><animate attributeName="r" values="2;3.5;2" dur="2.4s" repeatCount="indefinite"/></circle>')
    if slug == "model":  # a price line drawing itself into a forecast cone
        return (f'<path d="M40,31 L60,14 L60,44 Z" fill="{a}" opacity="0.15"/><path d="M40,31 L60,26" stroke="{a}" stroke-dasharray="3 3" stroke-width="1.6"/>'
                f'<path d="M4,44 L14,38 L22,41 L32,28 L40,31" stroke="{g}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="60" stroke-dashoffset="60">'
                f'<animate attributeName="stroke-dashoffset" values="60;0;0;60" keyTimes="0;0.4;0.85;1" dur="4s" repeatCount="indefinite"/></path>'
                f'<line x1="4" y1="56" x2="60" y2="56" stroke="{t["line"]}" stroke-width="1.6"/>')
    if slug == "honeypot":  # a hexagon cell with something buzzing around it
        hexagon = " ".join(f"{32 + 18 * math.cos(math.pi / 3 * k + math.pi / 6):.1f},{32 + 18 * math.sin(math.pi / 3 * k + math.pi / 6):.1f}" for k in range(6))
        return (f'<polygon points="{hexagon}" stroke="{g}" stroke-width="2" stroke-linejoin="round"><animateTransform attributeName="transform" type="rotate" values="0 32 32;60 32 32;60 32 32" keyTimes="0;0.3;1" dur="5s" repeatCount="indefinite" calcMode="spline" keySplines="{EASE};0 0 1 1"/></polygon>'
                f'<circle r="3" fill="{a}"><animateMotion dur="3s" repeatCount="indefinite" path="M32,6 C62,6 62,58 32,58 C2,58 2,6 32,6Z"/></circle>')
    if slug == "rl-ddos":  # packets hitting a wall, only one gets through
        pulses = "".join(f'<circle r="2.6" fill="{a}"><animateMotion path="M2,32 H40" dur="1.8s" begin="{k * 0.6:.1f}s" repeatCount="indefinite"/>'
                         f'<animate attributeName="opacity" values="1;1;0" keyTimes="0;0.85;1" dur="1.8s" begin="{k * 0.6:.1f}s" repeatCount="indefinite"/></circle>' for k in range(3))
        return (f'<line x1="2" y1="32" x2="62" y2="32" stroke="{t["line"]}" stroke-width="1.6"/>{pulses}'
                f'<rect x="42" y="14" width="5" height="36" rx="2.5" fill="{g}"/>'
                f'<circle r="2.6" fill="{t["grad"][2]}"><animateMotion path="M47,32 H62" dur="1.8s" repeatCount="indefinite"/></circle>')
    if slug == "car-price":  # a gauge settling on a price
        times = f'keyTimes="0;0.3;0.5;0.75;1" calcMode="spline" keySplines="{spline4}"'
        return (f'<path d="M8,44 A24,24 0 0 1 56,44" stroke="{t["line"]}" stroke-width="4" stroke-linecap="round"/>'
                f'<path d="M8,44 A24,24 0 0 1 56,44" stroke="{g}" stroke-width="4" stroke-linecap="round" stroke-dasharray="76" stroke-dashoffset="76">'
                f'<animate attributeName="stroke-dashoffset" values="76;20;45;8;76" dur="5s" repeatCount="indefinite" {times}/></path>'
                f'<line x1="32" y1="44" x2="32" y2="26" stroke="{t["text"]}" stroke-width="2.4" stroke-linecap="round">'
                f'<animateTransform attributeName="transform" type="rotate" values="-80 32 44;35 32 44;-10 32 44;70 32 44;-80 32 44" dur="5s" repeatCount="indefinite" {times}/></line>'
                f'<circle cx="32" cy="44" r="3.5" fill="{t["text"]}"/>')
    return ""


def card(theme, slug, eyebrow, title, text, tech, width, i, live=False):
    """Bento card: soft rounded panel, eyebrow, big title, copy, tech line and a looping glyph."""
    t = THEMES[theme]
    h, pad = 300, 44
    wide = width > 800
    glyph_scale = 2.6 if wide else 1.3
    glyph_size = 64 * glyph_scale
    text_area = width - pad * 2 - (glyph_size + 40 if wide else 0)
    lines = wrap(text, 22, text_area)
    copy = "".join(f'<text class="r" x="{pad}" y="{150 + k * 32}" font-size="22" fill="{t["muted"]}">{escape(line)}</text>' for k, line in enumerate(lines))
    # wide card: glyph on the right; small card: glyph in the bottom-right corner
    gx, gy = (width - pad - glyph_size, (h - glyph_size) / 2 + 10) if wide else (width - pad - glyph_size + 6, h - pad - glyph_size + 14)
    badge = ""
    if live:
        lw = len(title) * (44 * 0.55 - 1.4) + pad + 18
        badge = f'''<g transform="translate({lw:.0f} 70)"><rect width="76" height="30" rx="15" fill="#30d158" fill-opacity="0.15"/>
<circle cx="18" cy="15" r="5" fill="#30d158"><animate attributeName="opacity" values="1;.25;1" dur="1.6s" repeatCount="indefinite"/></circle>
<text class="sb" x="47" y="20.5" text-anchor="middle" font-size="15" fill="#30d158">LIVE</text></g>'''
    hop = f'values="0 0;3 -3;0 0;0 0" keyTimes="0;0.05;0.1;1" dur="5s" begin="{3 + i * 1.3:.1f}s" repeatCount="indefinite"'
    body = f"""<g class="u" {delay(0.2 + i * 0.12)}>
<rect width="{width}" height="{h}" rx="30" fill="{t['card']}"/>
<g transform="translate({gx:.0f} {gy:.0f}) scale({glyph_scale})">{glyph(slug, t)}</g>
<text class="sb" x="{pad}" y="60" font-size="15" letter-spacing="1.2" fill="url(#grad)">{escape(eyebrow)}</text>
<text class="b" x="{pad}" y="104" font-size="44" letter-spacing="-1.4" fill="{t['text']}">{escape(title)}</text>
{badge}
{copy}
<text class="md" x="{pad}" y="{h - 40}" font-size="18" fill="{t['text']}" opacity="0.75">{escape(tech)}</text>
<g transform="translate({width - pad - 36} 34)"><circle cx="18" cy="18" r="18" fill="{t['text']}" fill-opacity="0.08"/>
<path d="M13 23 L23 13 M15 13 H23 V21" stroke="{t['text']}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><animateTransform attributeName="transform" type="translate" {hop}/></path></g>
</g>"""
    return svg(width, h, theme, body, f"{title}: {text}")


def marquee(theme):
    """One endless row of pills per category, alternating direction, fading at the edges."""
    t = THEMES[theme]
    size, row_h, label_w, pill_h = 19, 66, 210, 44
    out = [f'''<linearGradient id="edge" x1="0" y1="0" x2="{W}" y2="0" gradientUnits="userSpaceOnUse">
  <stop offset="{label_w / W:.3f}" stop-color="#000"/><stop offset="{(label_w + 60) / W:.3f}" stop-color="#fff"/>
  <stop offset="{(W - 80) / W:.3f}" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
<mask id="fade"><rect width="{W}" height="{len(STACK) * row_h}" fill="url(#edge)"/></mask>''']
    for r, (label, items) in enumerate(STACK):
        y = 10 + r * row_h
        pills, x = [], 0.0
        for item in items * 3:
            pw = text_width(item, size, "md") + 44
            pills.append(f'<rect x="{x:.1f}" y="{y}" width="{pw:.1f}" height="{pill_h}" rx="{pill_h / 2}" fill="{t["card"]}"/>'
                         f'<text class="md" x="{x + pw / 2:.1f}" y="{y + 28.5}" text-anchor="middle" font-size="{size}" fill="{t["text"]}">{escape(item)}</text>')
            x += pw + 12
        loop = x / 3  # width of one set of items
        direction = f"0 0;{-loop:.1f} 0" if r % 2 == 0 else f"{-loop:.1f} 0;0 0"
        out.append(f'''<text class="sb f" {delay(0.2 + r * 0.1)} x="0" y="{y + 29}" font-size="21" fill="{t['text']}">{escape(label)}</text>
<g mask="url(#fade)"><g class="f" {delay(0.4 + r * 0.1)}><g transform="translate({label_w} 0)"><g>{''.join(pills)}
  <animateTransform attributeName="transform" type="translate" values="{direction}" dur="{loop / 40:.1f}s" repeatCount="indefinite"/></g></g></g></g>''')
    return svg(W, len(STACK) * row_h, theme, "\n".join(out),
               "Toolbox: " + "; ".join(f"{a}: {', '.join(b)}" for a, b in STACK))


def outro(theme):
    t = THEMES[theme]
    body = f"""{glow(W / 2, 140, 420, 140, "glowA", 70, 15)}
<text class="b u" {delay(0.2)} x="{W / 2}" y="112" text-anchor="middle" font-size="84" letter-spacing="-3" fill="url(#grad)">To be continued.</text>
<text class="md u" {delay(0.45)} x="{W / 2}" y="170" text-anchor="middle" font-size="30" letter-spacing="-0.4" fill="{t['muted']}">Got a wild idea? Let's build it.</text>
<text class="r f" {delay(0.9)} x="{W / 2}" y="236" text-anchor="middle" font-size="18" fill="{t['muted']}">English · French · Arabic</text>"""
    return svg(W, 270, theme, body, "To be continued. Got a wild idea? Let's build it. Speaks English, French and Arabic.")


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
                 "work-title": heading(theme, "Things I've made.", "Built end to end."),
                 "stack-title": heading(theme, "Toolbox.", "Always growing."),
                 "stack": marquee(theme), "outro": outro(theme)}
        slug, eyebrow, title, text, tech, _ = FEATURED
        files[f"card-{slug}"] = card(theme, slug, eyebrow, title, text, tech, W, 0, live=True)
        for i, (slug, eyebrow, title, text, tech, _) in enumerate(WORK):
            files[f"card-{slug}"] = card(theme, slug, eyebrow, title, text, tech, small, i + 1)
        for i, (slug, label, _, filled) in enumerate(LINKS):
            files[f"button-{slug}"], widths[slug] = button(theme, label, filled, i)
        for name, content in files.items():
            (ASSETS / f"{name}-{theme}.svg").write_text(content, encoding="utf-8")

    # GitHub caches images hard: change the query string only when the content changes
    v = f"{total}-a{len(FONT_FACES)}"
    scale = 830 / W  # README column width in px over the SVG viewBox width
    buttons = "\n  ".join(f'<a href="{url}">{picture(f"button-{slug}", label, v, str(round(widths[slug] * scale)))}</a>'
                          for slug, label, url, _ in LINKS)
    pct = "49.6%"  # two cards plus the inline space between them fill the column
    cards = [f'<a href="{w[5]}">{picture(f"card-{w[0]}", f"{w[2]}: {w[3]}", v, pct)}</a>' for w in WORK]
    readme = f"""{picture("top", f"Ons Kouki · {total} contributions", v)}

{picture("hero", f"Ons Kouki, {EYEBROW}. {TAGLINE} {' '.join(WORDS)}", v)}

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
