"""Build the profile README and its animated terminal-style SVGs (light + dark).

Usage: python scripts/build.py
Fetches the public contribution calendar, writes assets/*.svg and README.md.
Headlines are set in Instrument Serif, everything else in JetBrains Mono at light weights (both SIL OFL).
Headlines type themselves character by character; labels and cards are revealed by a swipe bar.
Toolbox icons are Simple Icons paths (CC0), vendored in icons/stack.json.
"""
import base64
import datetime as dt
import itertools
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
    "light": {"ink": "#111111", "muted": "#6e6e73", "faint": "#d2d2d7", "grid": "#ececef", "bg": "#ffffff",
              "acc": "#2563eb", "ok": "#16a34a"},
    "dark": {"ink": "#ededed", "muted": "#8b949e", "faint": "#30363d", "grid": "#1c2128", "bg": "#0d1117",
             "acc": "#58a6ff", "ok": "#3fb950"},
}

ROLE = "ICT Engineer"
WORDS = ["dream it", "design it", "build it", "train it", "ship it", "scale it"]
FIELDS = ["AI/ML", "Software Engineering", "Cloud Infrastructure"]

FEATURED = [  # (slug, eyebrow, title, text, tech, url, badge)
    ("claritychains", "AI · PROCUREMENT", "ClarityChains",
     "LLM agents that read supplier offers, flag the traps and pick a winner. "
     "Concept, UX, models, backend and deployment, end to end.",
     "React · Django · FastAPI · LangChain · Azure OpenAI", "https://clarity-chains.vercel.app", "LIVE"),
    ("repan", "REPAN · PUBLIC HEALTH", "Pandemic Analytics",
     "Regional pandemic analytics for East African health ministries. "
     "55 commits upstream: data pipelines, roles, Keycloak auth, translations.",
     "Next.js · Django · Airflow · Druid · Superset · Keycloak",
     "https://github.com/Speedykom/SpeedyMesh_Ecosystem-Regional-Pandemic-Analytics/commits?author=OnsKoukiPro", "OPEN SOURCE"),
]
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
]

STACK = [
    ("ML & Data", ["PyTorch", "TensorFlow", "scikit-learn", "LangChain", "pandas", "Airflow", "Druid", "Superset"]),
    ("Backend", ["Python", "FastAPI", "Django", "NestJS", "Node.js", "Spring", "PostgreSQL", "Redis"]),
    ("Cloud", ["AWS", "Azure", "Kubernetes", "Helm", "Argo CD", "Terraform", "Pulumi", "GitHub Actions"]),
    ("Security & Web", ["Vault", "Keycloak", "OpenSearch", "Grafana", "TypeScript", "React", "Next.js", "Angular"]),
]

FONT_FACES = {  # weight -> (css class, family, file)
    200: ("w2", "JBMonoXL", "jbmono-200"),
    300: ("w3", "JBMonoL", "jbmono-300"),
    400: ("w4", "JBMono", "jbmono-400"),
    "serif": ("s", "ISerif", "iserif"),
    "italic": ("si", "ISerifItalic", "iserif-italic"),
}
SERIF = json.loads((FONTS / "iserif-advances.json").read_text(encoding="utf-8"))
ICONS = json.loads((ROOT / "icons" / "stack.json").read_text(encoding="utf-8"))
FALLBACK = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
MONO = 0.6  # JetBrains Mono advance in em

EASE = ".65 0 .35 1"
BASE_CSS = """
.f { animation: fade 1s ease-out both; }
.dw { stroke-dasharray: 1 1; animation: draw 1.1s cubic-bezier(.65,0,.35,1) both; }
.blink { animation: blink 1.1s steps(1) infinite; }
@keyframes fade { from { opacity: 0; } }
@keyframes draw { from { stroke-dashoffset: 1; } to { stroke-dashoffset: 0; } }
@keyframes blink { 50% { opacity: 0; } }
"""
_ids = itertools.count()
# Every element is drawn in its finished state; animations hide it at t=0 and reveal it later.
# Renderers that skip SMIL (static previews, some apps) then still show the whole page.
HIDE = '<set attributeName="{0}" to="{1}" begin="0s" fill="freeze"/>'


def uid(prefix):
    return f"{prefix}{next(_ids)}"


def font_css(body):
    """Embed only the fonts whose class is used in this SVG."""
    used = {c for classes in re.findall(r'class="([^"]+)"', body) for c in classes.split()}
    css = []
    for weight, (cls, family, file) in FONT_FACES.items():
        if cls in used:
            data = base64.b64encode((FONTS / f"{file}.woff2").read_bytes()).decode()
            if isinstance(weight, int):
                css.append(f"@font-face{{font-family:{family};font-weight:{weight};"
                           f"src:url(data:font/woff2;base64,{data}) format('woff2')}}"
                           f".{cls}{{font-family:{family},{FALLBACK};font-weight:{weight}}}")
            else:
                css.append(f"@font-face{{font-family:{family};src:url(data:font/woff2;base64,{data}) format('woff2')}}"
                           f".{cls}{{font-family:{family},Georgia,serif;font-kerning:none"
                           f"{';font-style:italic' if weight == 'italic' else ''}}}")
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


def mono(text, x, y, size, fill, weight=400, anchor="start", spacing=0, extra=""):
    cls = FONT_FACES[weight][0]
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


def typed(text, x, y, size, color, begin, per=0.06, weight=300, spacing=0, anchor="start", cursor="hide"):
    """Type text one character at a time behind a caret. cursor: "hide" after typing, "blink" forever, or None."""
    cw = size * MONO + spacing
    n = len(text)
    if anchor != "start":
        x -= n * cw / (2 if anchor == "middle" else 1)
    cid, dur = uid("ty"), (n + 1) * per
    widths = [k * cw + (size * 0.2 if k == n else 0) for k in range(n + 1)]
    keys = ";".join(f"{k / (n + 1):.4f}" for k in range(n + 1))
    timing = f'keyTimes="{keys}" calcMode="discrete" dur="{dur:.2f}s" begin="{begin:.2f}s" fill="freeze"'
    out = [f'<clipPath id="{cid}"><rect x="{x - 1:.1f}" y="{y - size * 1.05:.1f}" height="{size * 1.45:.1f}" width="{widths[-1]:.1f}">'
           f'{HIDE.format("width", 0)}<animate attributeName="width" values="{";".join(f"{v:.1f}" for v in widths)}" {timing}/></rect></clipPath>',
           f'<g clip-path="url(#{cid})">{mono(text, x, y, size, color, weight, spacing=spacing)}</g>']
    if cursor:
        gap, cw_bar = size * 0.06, max(1.5, size * 0.045)
        xs = ";".join(f"{x + gap + min(v, n * cw):.1f}" for v in widths)
        end = begin + dur
        tail = (f'<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1.1s" begin="{end:.2f}s" repeatCount="indefinite"/>'
                if cursor == "blink" else f'<set attributeName="opacity" to="0" begin="{end + 0.7:.2f}s" fill="freeze"/>')
        out.append(f'<rect x="{x + gap:.1f}" y="{y - size * 0.8:.1f}" width="{cw_bar:.1f}" height="{size * 0.95:.1f}" fill="{color}" opacity="0">'
                   f'<set attributeName="opacity" to="1" begin="{begin:.2f}s" fill="freeze"/>'
                   f'<animate attributeName="x" values="{xs}" {timing}/>{tail}</rect>')
    return "".join(out)


def headline(parts, x, y, size, t, begin, per=0.07, anchor="start", cursor="hide"):
    """Serif headline typed one character at a time. parts: [(text, italic, color)]."""
    advs = [SERIF["iserif-italic" if italic else "iserif"].get(ch, 0.3) * size for text, italic, _ in parts for ch in text]
    n = len(advs)
    if anchor != "start":
        x -= sum(advs) / (2 if anchor == "middle" else 1)
    cum = [0.0]
    for a in advs:
        cum.append(cum[-1] + a)
    widths = cum[:-1] + [cum[-1] + size * 0.2]
    cid, dur = uid("hl"), (n + 1) * per
    keys = ";".join(f"{k / (n + 1):.4f}" for k in range(n + 1))
    timing = f'keyTimes="{keys}" calcMode="discrete" dur="{dur:.2f}s" begin="{begin:.2f}s" fill="freeze"'
    spans = "".join(f'<tspan class="{"si" if italic else "s"}" fill="{color}">{escape(text)}</tspan>' for text, italic, color in parts)
    out = [f'<clipPath id="{cid}"><rect x="{x - size * 0.1:.1f}" y="{y - size * 1.05:.1f}" height="{size * 1.4:.1f}" width="{widths[-1] + size * 0.1:.1f}">'
           f'{HIDE.format("width", 0)}<animate attributeName="width" values="{";".join(f"{v + size * 0.1:.1f}" for v in widths)}" {timing}/></rect></clipPath>',
           f'<g clip-path="url(#{cid})"><text x="{x:.1f}" y="{y:.1f}" font-size="{size}" xml:space="preserve">{spans}</text></g>']
    if cursor:
        end = begin + dur
        tail = (f'<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1.1s" begin="{end:.2f}s" repeatCount="indefinite"/>'
                if cursor == "blink" else f'<set attributeName="opacity" to="0" begin="{end + 0.7:.2f}s" fill="freeze"/>')
        xs = ";".join(f"{x + v + size * 0.04:.1f}" for v in cum)
        out.append(f'<rect x="{x:.1f}" y="{y - size * 0.72:.1f}" width="{max(1.5, size * 0.02):.1f}" height="{size * 0.86:.1f}" fill="{t["acc"]}" opacity="0">'
                   f'<set attributeName="opacity" to="1" begin="{begin:.2f}s" fill="freeze"/>'
                   f'<animate attributeName="x" values="{xs}" {timing}/>{tail}</rect>')
    return "".join(out), x + cum[-1]


def swipe(content, x, y, w, h, color, begin, dur=0.8):
    """A bar sweeps in from the left, uncovers the content and leaves to the right."""
    timing = f'keyTimes="0;0.5;1" calcMode="spline" keySplines="{EASE};{EASE}" dur="{dur}s" begin="{begin:.2f}s" fill="freeze"'
    return (f'<g>{content}{HIDE.format("opacity", 0)}<set attributeName="opacity" to="1" begin="{begin + dur / 2:.2f}s" fill="freeze"/></g>'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="0" height="{h:.1f}" fill="{color}">'
            f'<animate attributeName="width" values="0;{w:.1f};0" {timing}/>'
            f'<animate attributeName="x" values="{x:.1f};{x:.1f};{x + w:.1f}" {timing}/></rect>')


def label(text, x, y, size, t, begin, color=None, spacing=2, anchor="start", weight=400):
    """Uppercase mono label revealed by a swipe."""
    w = mono_width(text, size, spacing)
    left = x - (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
    return swipe(mono(text, x, y, size, color or t["muted"], weight, anchor, spacing),
                 left - 4, y - size * 0.95, w + 6, size * 1.3, t["acc"], begin)


def top(theme, total, since):
    t = THEMES[theme]
    ticks = []
    for x in range(0, W + 1, 12):
        h = 10 if x % 120 == 0 else 6 if x % 60 == 0 else 3
        ticks.append(f"M{min(max(x, 0.5), W - 0.5)} 56 V{56 - h}")
    rw = mono_width("README.MD", 13, 2)
    body = f"""{label("ONS.KOUKI", 0, 24, 14, t, 0.1, t["ink"])}
{label(f"{total:,} CONTRIBUTIONS · SINCE {since}", W / 2, 24, 13, t, 0.3, anchor="middle")}
{label("README.MD", W, 24, 13, t, 0.5, anchor="end")}
<circle cx="{W - rw - 16:.1f}" cy="19.5" r="3.5" fill="{t["ok"]}">{HIDE.format("opacity", 0)}<set attributeName="opacity" to="1" begin="0.9s" fill="freeze"/>
<animate attributeName="opacity" values="1;0.15;1" dur="2s" begin="0.9s" repeatCount="indefinite"/></circle>
<clipPath id="reveal"><rect width="{W}" height="70">{HIDE.format("width", 0)}<animate attributeName="width" from="0" to="{W}" dur="1.6s" begin="0.2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="{EASE}"/></rect></clipPath>
<g clip-path="url(#reveal)" stroke="{t["faint"]}" stroke-width="1"><path d="{" ".join(ticks)}"/><path d="M0 56.5 H{W}"/></g>"""
    return svg(W, 58, body, f"Ons Kouki · {total} contributions since {since}")


def globe(cx, cy, r, t):
    """Wireframe globe: latitude rings stay put, meridians breathe to fake a rotation."""
    out = [f'<circle class="dw" {delay(0.4)} pathLength="1" cx="{cx}" cy="{cy}" r="{r}" stroke="{t["ink"]}" stroke-width="1.2"/>']
    for k, lat in enumerate((-60, -30, 0, 30, 60)):
        a = math.radians(lat)
        rx = r * math.cos(a)
        out.append(f'<ellipse class="dw" {delay(0.6 + k * 0.08)} pathLength="1" cx="{cx}" cy="{cy + r * math.sin(a):.1f}" rx="{rx:.1f}" ry="{rx * 0.16:.1f}" '
                   f'stroke="{t["faint"]}" stroke-width="1"/>')
    samples, n = 24, 6
    for m in range(n):
        phase = math.pi * m / n
        vals = ";".join(f"{r * abs(math.sin(phase + math.pi * s / samples)):.1f}" for s in range(samples + 1))
        out.append(f'<ellipse class="f" {delay(1.0)} cx="{cx}" cy="{cy}" ry="{r}" rx="{r * abs(math.sin(phase)):.1f}" stroke="{t["muted"]}" stroke-width="0.8">'
                   f'<animate attributeName="rx" values="{vals}" dur="16s" repeatCount="indefinite"/></ellipse>')
    # tilted orbit with a satellite
    orbit = f"M{cx - r * 1.32},{cy} a{r * 1.32},{r * 0.36} 0 1,0 {r * 2.64},0 a{r * 1.32},{r * 0.36} 0 1,0 {-r * 2.64},0"
    out.append(f'<g transform="rotate(-18 {cx} {cy})"><path class="f" {delay(1.2)} d="{orbit}" stroke="{t["muted"]}" stroke-width="1" stroke-dasharray="2 6"/>'
               f'<g class="f" {delay(1.4)}><circle r="4" fill="{t["ink"]}"><animateMotion dur="9s" repeatCount="indefinite" path="{orbit}"/></circle>'
               f'<circle r="10" stroke="{t["ink"]}" stroke-width="0.8"><animateMotion dur="9s" repeatCount="indefinite" path="{orbit}"/>'
               f'<animate attributeName="r" values="5;14;5" dur="2s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;0;1" dur="2s" repeatCount="indefinite"/></circle></g></g>')
    out.append(f'<g class="f" {delay(1.6)} stroke="{t["muted"]}" stroke-width="0.8"><path d="M{cx} {cy} L{cx + r * 0.71:.1f} {cy - r * 0.71:.1f}"/><circle cx="{cx}" cy="{cy}" r="2" fill="{t["muted"]}"/></g>')
    out.append(f'<g class="f" {delay(1.7)}>{mono("R 1.0 · WORLD", cx + r * 0.74, cy - r * 0.74 - 8, 11, t["muted"], spacing=1)}</g>')
    return "\n".join(out)


def typer(x, y, size, t, start=2.6, cycle=2.8):
    """Prompt that types each word, selects it like a text field, then clears it."""
    cw, total = size * MONO, len(WORDS) * cycle
    clips, texts, cur_x, cur_t = [], [], [], []
    for i, word in enumerate(WORDS):
        steps = [k * 0.07 for k in range(len(word) + 1)]
        times = [0] + steps[1:] + [cycle - 0.35, cycle - 0.34]
        widths = [0] + [k * cw for k in range(1, len(word) + 1)] + [len(word) * cw, 0]
        key = ";".join(f"{v / total:.4f}" for v in times + [total])
        base = f'width="{len(word) * cw:.1f}">{HIDE.format("width", 0)}' if i == 0 else 'width="0">'
        clips.append(f'<clipPath id="tw{i}"><rect x="{x}" y="{y - size}" height="{size * 1.4}" {base}'
                     f'<animate attributeName="width" values="{";".join(f"{v:.1f}" for v in widths + [0])}" keyTimes="{key}" calcMode="discrete" '
                     f'dur="{total}s" begin="{start + i * cycle:.2f}s" repeatCount="indefinite"/></rect></clipPath>')
        texts.append(f'<g clip-path="url(#tw{i})">{mono(word, x, y, size, t["ink"], 300)}</g>')
        # select-all highlight just before the word is cleared
        sel = [0, (cycle - 0.75) / total, (cycle - 0.34) / total]
        texts.append(f'<rect x="{x - 2}" y="{y - size * 0.86:.1f}" width="{len(word) * cw + 4:.1f}" height="{size * 1.12:.1f}" fill="{t["acc"]}" opacity="0">'
                     f'<animate attributeName="opacity" values="0;0.2;0" keyTimes="{";".join(f"{v:.4f}" for v in sel)}" calcMode="discrete" '
                     f'dur="{total}s" begin="{start + i * cycle:.2f}s" repeatCount="indefinite"/></rect>')
        for tm, wd in zip(times, widths):
            cur_t.append((i * cycle + tm) / total)
            cur_x.append(x + wd + 3)
    # SMIL keyTimes need to start at 0 and end at 1, strictly ordered
    pairs = sorted(set(zip([round(v, 4) for v in cur_t], cur_x)))
    keys, vals, seen = [], [], set()
    for k, v in pairs:
        if k not in seen and k < 1:
            keys.append(k)
            vals.append(v)
            seen.add(k)
    cursor = (f'<rect x="{x + 3}" y="{y - size * 0.8:.1f}" width="2" height="{size * 0.95:.1f}" fill="{t["acc"]}" opacity="0">'
              f'<set attributeName="opacity" to="1" begin="{start - 0.4:.2f}s" fill="freeze"/>'
              f'<animate attributeName="x" values="{";".join(f"{v:.1f}" for v in vals)}" keyTimes="{";".join(f"{k:.4f}" for k in keys)}" '
              f'calcMode="discrete" dur="{total}s" begin="{start:.2f}s" repeatCount="indefinite"/></rect>')
    return "\n".join(clips + texts) + "\n" + cursor


def hero(theme):
    t = THEMES[theme]
    h, x0 = 470, 0
    fields = "  /  ".join(f.upper() for f in FIELDS)
    prompt = "~/ons $ "
    body = f"""{typed("$ whoami", x0, 46, 17, t["muted"], 0.2, per=0.07, weight=400)}
{headline([("Ons Kouki", False, t["ink"])], x0 - 4, 178, 150, t, 1.0, per=0.09)[0]}
{label(ROLE.upper(), x0, 238, 17, t, 2.0, t["ink"], spacing=6)}
<g class="f" {delay(2.3)}>{mono(prompt, x0, 340, 30, t["ok"], 300)}</g>
{typer(x0 + mono_width(prompt, 30), 340, 30, t)}
<path class="dw" {delay(2.6)} pathLength="1" d="M{x0} 398.5 H{x0 + 40}" stroke="{t["acc"]}" stroke-width="1.5"/>
{label(fields, x0, 432, 14, t, 2.8)}
{globe(985, 230, 128, t)}"""
    return svg(W, h, body, f"Ons Kouki, {ROLE}. Idea to production: {', '.join(WORDS)}. {', '.join(FIELDS)}")


def button(theme, text, filled, i):
    """Hairline key, revealed by a swipe, with an arrow that nudges every few seconds."""
    t = THEMES[theme]
    size, sp, h = 15, 2, 52
    text = text.upper()
    width = round(mono_width(text, size, sp) + 84)
    fill, color = (t["ink"], t["bg"]) if filled else ("none", t["ink"])
    hop = f'values="0 0;3 -3;0 0;0 0" keyTimes="0;0.05;0.1;1" dur="5s" begin="{2 + i * 1.6:.1f}s" repeatCount="indefinite"'
    key = f"""<rect x="4.5" y="4.5" width="{width - 9}" height="{h - 9}" fill="{fill}" stroke="{t["ink"]}" stroke-width="1"/>
{mono(text, 24, 31, size, color, 400, spacing=sp)}
<g transform="translate({width - 40} 18)"><path d="M2 14 L14 2 M5 2 H14 V11" stroke="{color}" stroke-width="1.4" stroke-linecap="square">
<animateTransform attributeName="transform" type="translate" {hop}/></path></g>"""
    return svg(width, h, swipe(key, 4, 4, width - 8, h - 8, t["acc"], 0.4 + i * 0.15), text), width


def graph(theme, calendars):
    t = THEMES[theme]
    gap, ygap = 1.8, 26
    years = sorted(calendars)
    block = (W - ygap * (len(years) - 1)) / len(years)
    step = block / 53
    cell = step - gap
    gy = 50
    alphas = [0, 0.3, 0.55, 0.8, 1]
    legend_x = W - 5 * (cell + 6) - mono_width(" MORE", 11, 1)
    legend = "".join(f'<rect class="l{i}" x="{legend_x + i * (cell + 6):.1f}" y="12" width="{cell:.1f}" height="{cell:.1f}"/>' for i in range(5))
    out = [label("01 / ACTIVITY.LOG", 0, 24, 13, t, 0.1, t["acc"]),
           f'<g class="f" {delay(0.4)}>{mono("LESS", legend_x - 10, 21, 11, t["muted"], anchor="end", spacing=1)}{legend}'
           f'{mono("MORE", W, 21, 11, t["muted"], anchor="end", spacing=1)}</g>']
    cells = []
    for yi, year in enumerate(years):
        x0 = yi * (block + ygap)
        jan1 = dt.date(year, 1, 1)
        offset = (jan1.weekday() + 1) % 7  # Sunday-first rows, like GitHub
        for date, level in sorted(calendars[year].items()):
            col, row = divmod((date - jan1).days + offset, 7)
            cells.append(f'<rect class="l{level}" x="{x0 + col * step + 0.5:.1f}" y="{gy + row * step + 0.5:.1f}" width="{cell - 1:.1f}" height="{cell - 1:.1f}"/>')
        cells.append(f'<path d="M{x0} {gy + 7 * step + 12:.1f} H{x0 + block - 4:.1f}" stroke="{t["faint"]}"/>'
                     f'{mono(str(year), x0, gy + 7 * step + 30, 12, t["muted"], spacing=1.5)}')
    height = gy + 7 * step + 38
    # the grid is wiped in left to right, then a thin scan line keeps passing over it
    out.append(f'<clipPath id="gw"><rect y="0" height="{height:.0f}" width="{W}">{HIDE.format("width", 0)}<animate attributeName="width" values="0;{W}" dur="2.2s" begin="0.3s" '
               f'fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="{EASE}"/></rect></clipPath><g clip-path="url(#gw)">{"".join(cells)}</g>')
    out.append(f'<g><path d="M0 {gy - 6} V{gy + 7 * step + 4:.1f}" stroke="{t["acc"]}" stroke-width="1.2" opacity="0.7"/>'
               f'<animateTransform attributeName="transform" type="translate" values="-10 0;{W + 10} 0" dur="8s" begin="2.6s" repeatCount="indefinite"/></g>')
    css = (f".l0{{fill:none;stroke:{t['faint']};stroke-width:.8}}"
           + "".join(f".l{i}{{fill:{t['ok']};fill-opacity:{a}}}" for i, a in enumerate(alphas) if i))
    return svg(W, int(height), "\n".join(out), "Contribution activity", css)


def heading(theme, index, name, plain, accent, note):
    """Section index, a typed serif title with an italic accent and a hairline that runs to the edge."""
    t = THEMES[theme]
    title = plain + accent
    drawn, end = headline([(plain, False, t["ink"]), (accent, True, t["acc"])], -2, 100, 64, t, 0.5, per=0.055)
    body = f"""{label(f"{index} / {name}", 0, 26, 13, t, 0.05, t["acc"])}
{drawn}
<path class="dw" {delay(0.6 + len(title) * 0.055)} pathLength="1" d="M{end + 28:.0f} 88.5 H{W - 8}" stroke="{t["faint"]}" stroke-width="1"/>
<circle class="f" {delay(1.4 + len(title) * 0.055)} cx="{W - 4}" cy="88.5" r="3.5" stroke="{t["acc"]}" stroke-width="1.2"/>
{label(note, W - 20, 72, 12, t, 1.0 + len(title) * 0.055, anchor="end")}"""
    return svg(W, 120, body, f"{title}. {note}")


def glyph(slug, t):
    """Small looping line drawing that hints at each project, in a 64×64 box."""
    ink, muted = t["ink"], t["muted"]
    if slug == "claritychains":  # linked rings turning
        rings = "".join(f'<circle cx="{32 + 10 * math.cos(k * 2.094):.1f}" cy="{32 + 10 * math.sin(k * 2.094):.1f}" r="12" stroke="{ink}" stroke-width="0.9"/>' for k in range(3))
        return (f'<circle cx="32" cy="32" r="29" stroke="{muted}" stroke-width="0.5" stroke-dasharray="1.5 3"/>'
                f'<g>{rings}<animateTransform attributeName="transform" type="rotate" values="0 32 32;360 32 32" dur="14s" repeatCount="indefinite"/></g>'
                f'<circle cx="32" cy="32" r="2.4" fill="{ink}"><animate attributeName="r" values="1.6;3;1.6" dur="2.4s" repeatCount="indefinite"/></circle>')
    if slug == "repan":  # regions on a map, hotspots pinging in turn
        spots = [(14, 20), (30, 12), (48, 22), (22, 40), (40, 44), (54, 50)]
        links = " ".join(f"M{a[0]} {a[1]} L{b[0]} {b[1]}" for a, b in [(0, 1), (1, 2), (0, 3), (3, 4), (2, 4), (4, 5)] for a, b in [(spots[a], spots[b])])
        pings = "".join(f'<circle cx="{x}" cy="{y}" r="2" stroke="{t["ok"]}" stroke-width="0.8"><animate attributeName="r" values="2;9" dur="3s" begin="{k * 0.5:.1f}s" repeatCount="indefinite"/>'
                        f'<animate attributeName="opacity" values="1;0" dur="3s" begin="{k * 0.5:.1f}s" repeatCount="indefinite"/></circle>' for k, (x, y) in enumerate(spots))
        dots = "".join(f'<circle cx="{x}" cy="{y}" r="1.8" fill="{ink}"/>' for x, y in spots)
        return f'<path d="{links}" stroke="{muted}" stroke-width="0.6" stroke-dasharray="1.5 2"/>{pings}{dots}'
    if slug == "model":  # a price line drawing itself into a forecast cone
        return (f'<path d="M40,31 L60,14 M40,31 L60,44" stroke="{muted}" stroke-width="0.8" stroke-dasharray="2 2"/><path d="M40,31 L60,26" stroke="{ink}" stroke-width="1"/>'
                f'<path d="M4,44 L14,38 L22,41 L32,28 L40,31" stroke="{ink}" stroke-width="1.3" stroke-linejoin="round" stroke-dasharray="60" stroke-dashoffset="60">'
                f'<animate attributeName="stroke-dashoffset" values="60;0;0;60" keyTimes="0;0.4;0.85;1" dur="4s" repeatCount="indefinite"/></path>'
                f'<path d="M4,56 H60 M4,56 V8" stroke="{muted}" stroke-width="0.8"/>')
    if slug == "honeypot":  # a hexagon cell with something buzzing around it
        hexagon = " ".join(f"{32 + 18 * math.cos(math.pi / 3 * k + math.pi / 6):.1f},{32 + 18 * math.sin(math.pi / 3 * k + math.pi / 6):.1f}" for k in range(6))
        inner = " ".join(f"{32 + 9 * math.cos(math.pi / 3 * k + math.pi / 6):.1f},{32 + 9 * math.sin(math.pi / 3 * k + math.pi / 6):.1f}" for k in range(6))
        return (f'<polygon points="{inner}" stroke="{muted}" stroke-width="0.8"/>'
                f'<polygon points="{hexagon}" stroke="{ink}" stroke-width="1.1" stroke-linejoin="round"><animateTransform attributeName="transform" type="rotate" values="0 32 32;60 32 32;60 32 32" keyTimes="0;0.3;1" dur="5s" repeatCount="indefinite" calcMode="spline" keySplines="{EASE};0 0 1 1"/></polygon>'
                f'<circle r="2" fill="{ink}"><animateMotion dur="3s" repeatCount="indefinite" path="M32,6 C62,6 62,58 32,58 C2,58 2,6 32,6Z"/></circle>')
    if slug == "rl-ddos":  # packets hitting a wall, only one gets through
        pulses = "".join(f'<rect x="-1.5" y="-1.5" width="3" height="3" fill="{muted}"><animateMotion path="M2,32 H40" dur="1.8s" begin="{k * 0.6:.1f}s" repeatCount="indefinite"/>'
                         f'<animate attributeName="opacity" values="1;1;0" keyTimes="0;0.85;1" dur="1.8s" begin="{k * 0.6:.1f}s" repeatCount="indefinite"/></rect>' for k in range(3))
        return (f'<line x1="2" y1="32" x2="62" y2="32" stroke="{muted}" stroke-width="0.8" stroke-dasharray="2 2"/>{pulses}'
                f'<rect x="42" y="14" width="5" height="36" stroke="{ink}" stroke-width="1"/>'
                f'<rect x="-1.5" y="-1.5" width="3" height="3" fill="{ink}"><animateMotion path="M47,32 H62" dur="1.8s" repeatCount="indefinite"/></rect>')
    if slug == "car-price":  # a gauge settling on a price
        times = f'keyTimes="0;0.3;0.5;0.75;1" calcMode="spline" keySplines="{";".join([EASE] * 4)}"'
        ticks = " ".join(f"M{32 + 27 * math.cos(math.pi * (1 + k / 8)):.1f} {44 + 27 * math.sin(math.pi * (1 + k / 8)):.1f} L{32 + 31 * math.cos(math.pi * (1 + k / 8)):.1f} {44 + 31 * math.sin(math.pi * (1 + k / 8)):.1f}" for k in range(9))
        return (f'<path d="{ticks}" stroke="{muted}" stroke-width="0.8"/><path d="M8,44 A24,24 0 0 1 56,44" stroke="{muted}" stroke-width="0.8"/>'
                f'<line x1="32" y1="44" x2="32" y2="22" stroke="{ink}" stroke-width="1.2">'
                f'<animateTransform attributeName="transform" type="rotate" values="-80 32 44;35 32 44;-10 32 44;70 32 44;-80 32 44" dur="5s" repeatCount="indefinite" {times}/></line>'
                f'<circle cx="32" cy="44" r="2.5" stroke="{ink}" stroke-width="1"/>')
    return ""


def card(theme, slug, eyebrow, title, text, tech, width, i, badge_text=None):
    """Spec sheet: a swipe uncovers a hairline frame, a typed title, mono copy and a looping line drawing."""
    t = THEMES[theme]
    h, pad = 290, 40
    wide = width > 800
    gs = 2.6 if wide else 1.2
    gsize = 64 * gs
    text_area = width - pad * 2 - (gsize + 60 if wide else 0)
    badge_w = mono_width(badge_text or "", 12, 2) + 40
    title_room = text_area - (badge_w + 30 if badge_text else 0) - (0 if wide else 56)
    size = min(48, title_room / sum(SERIF["iserif"].get(ch, 0.3) for ch in title))
    drawn, title_end = headline([(title, False, t["ink"])], pad - 2, 114, round(size, 1), t, 0.8 + i * 0.15, per=0.05)
    lines = wrap(text, 15, text_area)
    copy = "".join(mono(line, pad, 158 + k * 24, 15, t["muted"], 300) for k, line in enumerate(lines))
    gx, gy = (width - pad - gsize - 20, (h - gsize) / 2 + 6) if wide else (width - pad - gsize + 4, h - pad - gsize + 14)
    begin = 0.2 + i * 0.15
    badge = ""
    if badge_text:
        badge = f'''<g transform="translate({title_end + 22:.0f} 91)"><rect x="0.5" y="0.5" width="{badge_w:.0f}" height="26" stroke="{t["ok"]}" stroke-width="1"/>
<circle cx="15" cy="13.5" r="3.5" fill="{t["ok"]}"><animate attributeName="opacity" values="1;.15;1" dur="1.6s" repeatCount="indefinite"/></circle>
{mono(badge_text, 28, 18, 12, t["ok"], spacing=2)}</g>'''
    hop = f'values="0 0;3 -3;0 0;0 0" keyTimes="0;0.05;0.1;1" dur="5s" begin="{3 + i * 1.3:.1f}s" repeatCount="indefinite"'
    sheet = f"""<rect x="0.5" y="0.5" width="{width - 1}" height="{h - 1}" stroke="{t["faint"]}" stroke-width="1"/>
<g transform="translate({gx:.0f} {gy:.0f}) scale({gs})">{glyph(slug, t)}</g>
{mono(f"P.{i:02d}", pad, 50, 12, t["acc"], spacing=2)}{mono("— " + eyebrow, pad + mono_width("P.00 ", 12, 2), 50, 12, t["muted"], spacing=2)}
{copy}
{mono("› " + tech, pad, h - 34, 13, t["ink"], 300)}
<g transform="translate({width - pad - 34} 24)"><rect x="0.5" y="0.5" width="33" height="33" stroke="{t["faint"]}" stroke-width="1"/>
<path d="M11 23 L23 11 M14 11 H23 V20" stroke="{t["ink"]}" stroke-width="1.2" stroke-linecap="square"><animateTransform attributeName="transform" type="translate" {hop}/></path></g>
{badge}"""
    body = f"""{swipe(sheet, 0, 0, width, h, t["grid"], begin, dur=0.9)}
{drawn}"""
    return svg(round(width), h, body, f"{title}: {text}")


def circuit(theme):
    """Toolbox as a circuit: each category is a trace, each tool a chip with its logo; a pulse lights them up in turn."""
    t = THEMES[theme]
    size, sp, row_h, chip_h, x_node, top_y, icon = 12, 0.3, 80, 34, 224, 34, 14
    x_end = W - 8
    out = [f'<path class="dw" {delay(0.1)} pathLength="1" d="M{x_node} {top_y} V{top_y + (len(STACK) - 1) * row_h}" stroke="{t["faint"]}" stroke-width="1"/>']
    for r, (name, items) in enumerate(STACK):
        y = top_y + r * row_h
        dur = 6 + r * 0.9
        begin = 1.2 + r * 0.7
        widths = [mono_width(item, size, sp) + 26 + icon + 7 for item in items]
        span = x_end - 24 - (x_node + 24)
        gap = (span - sum(widths)) / (len(items) - 1)
        chips, x = [], x_node + 24
        for k, (item, cw) in enumerate(zip(items, widths)):
            p = (x + cw / 2 - x_node) / (x_end - x_node)
            keys = f"0;{max(p - 0.04, 0.001):.3f};{p:.3f};{min(p + 0.12, 0.999):.3f};1"
            flash = f'values="{{0}};{{0}};{t["acc"]};{{0}};{{0}}" keyTimes="{keys}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"'
            chips.append(f'<g class="f" {delay(0.4 + r * 0.12 + k * 0.05)}><rect x="{x:.1f}" y="{y - chip_h / 2}" width="{cw:.1f}" height="{chip_h}" fill="{t["bg"]}" stroke="{t["faint"]}" stroke-width="1">'
                         f'<animate attributeName="stroke" {flash.format(t["faint"])}/></rect>'
                         f'<path transform="translate({x + 13:.1f} {y - icon / 2:.1f}) scale({icon / 24:.4f})" d="{ICONS[item]}" fill="{t["ink"]}">'
                         f'<animate attributeName="fill" {flash.format(t["ink"])}/></path>'
                         f'{mono(item, x + 13 + icon + 7, y + 4.2, size, t["ink"], 300, spacing=sp)}</g>')
            x += cw + gap
        trace = f"M{x_node} {y} H{x_end}"
        out.append(f'''<path class="dw" {delay(0.2 + r * 0.12)} pathLength="1" d="{trace}" stroke="{t["faint"]}" stroke-width="1"/>
<circle class="f" {delay(0.3 + r * 0.12)} cx="{x_node}" cy="{y}" r="3.5" fill="{t["bg"]}" stroke="{t["acc"]}" stroke-width="1.2"/>
<rect class="f" {delay(0.3 + r * 0.12)} x="{x_end - 2.5}" y="{y - 2.5}" width="5" height="5" fill="{t["muted"]}"/>
{label(f"{r + 1:02d}", 0, y + 4.5, 13, t, 0.15 + r * 0.15, t["acc"], spacing=1.5)}{label(name.upper(), 34, y + 4.5, 13, t, 0.2 + r * 0.15, t["ink"], spacing=1.5)}
<g class="f" {delay(1)}><circle r="3" fill="{t["acc"]}"><animateMotion path="{trace}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/></circle></g>
{"".join(chips)}''')
    height = top_y + (len(STACK) - 1) * row_h + 38
    return svg(W, height, "\n".join(out), "Toolbox: " + "; ".join(f"{a}: {', '.join(b)}" for a, b in STACK))


def outro(theme):
    t = THEMES[theme]
    h = 280
    title = "To be continued"
    prompt = "> got a wild idea? let's build it"
    body = f"""{typed("$ echo $NEXT", W / 2, 40, 15, t["muted"], 0.2, per=0.07, weight=400, anchor="middle")}
{headline([("To be ", False, t["ink"]), ("continued", True, t["acc"])], W / 2, 142, 92, t, 1.3, per=0.07, anchor="middle")[0]}
{typed(prompt, W / 2, 204, 19, t["muted"], 2.6, per=0.04, weight=300, anchor="middle", cursor="blink")}
<g class="f" {delay(4.2)}><path d="M{W / 2 - 230} 248.5 H{W / 2 - 110} M{W / 2 + 110} 248.5 H{W / 2 + 230}" stroke="{t["faint"]}" stroke-width="1"/></g>
{label("EN · FR · AR — EOF", W / 2, 253, 12, t, 4.0, anchor="middle")}"""
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
                 "work-title": heading(theme, "02", "WORK", "Things I've ", "made", "BUILT END TO END"),
                 "stack-title": heading(theme, "03", "STACK", "Tools I ", "use", "ALWAYS GROWING"),
                 "stack": circuit(theme), "outro": outro(theme)}
        for i, (slug, eyebrow, title, text, tech, _, badge) in enumerate(FEATURED):
            files[f"card-{slug}"] = card(theme, slug, eyebrow, title, text, tech, W, i + 1, badge)
        for i, (slug, eyebrow, title, text, tech, _) in enumerate(WORK):
            files[f"card-{slug}"] = card(theme, slug, eyebrow, title, text, tech, small, i + 1 + len(FEATURED))
        for i, (slug, text, _, filled) in enumerate(LINKS):
            files[f"button-{slug}"], widths[slug] = button(theme, text, filled, i)
        for name, content in files.items():
            (ASSETS / f"{name}-{theme}.svg").write_text(content, encoding="utf-8")

    # GitHub caches images hard: change the query string only when the content changes
    v = f"{total}-t3"
    scale = 830 / W  # README column width in px over the SVG viewBox width
    buttons = "\n  ".join(f'<a href="{url}">{picture(f"button-{slug}", text, v, str(round(widths[slug] * scale)))}</a>'
                          for slug, text, url, _ in LINKS)
    pct = "49.6%"  # two cards plus the inline space between them fill the column
    featured = "\n".join(f'<a href="{f[5]}">{picture(f"card-{f[0]}", f"{f[2]}: {f[3]}", v)}</a>' for f in FEATURED)
    cards = [f'<a href="{w[5]}">{picture(f"card-{w[0]}", f"{w[2]}: {w[3]}", v, pct)}</a>' for w in WORK]
    readme = f"""{picture("top", f"Ons Kouki · {total} contributions", v)}

{picture("hero", f"Ons Kouki, {ROLE}. Idea to production: {', '.join(WORDS)}.", v)}

<p align="center">
  {buttons}
</p>

{picture("graph", "Contribution activity", v)}

{picture("work-title", "Things I've made. Built end to end.", v)}

{featured}
<p>
{cards[0]}
{cards[1]}
{cards[2]}
{cards[3]}
</p>

{picture("stack-title", "Tools I use. Always growing.", v)}

{picture("stack", "; ".join(f"{a}: {', '.join(b)}" for a, b in STACK), v)}

{picture("outro", "To be continued. Got a wild idea? Let's build it.", v)}
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(f"{total} contributions, {len(list(ASSETS.glob('*.svg')))} svgs")


if __name__ == "__main__":
    build()
