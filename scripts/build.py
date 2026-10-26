"""Build the profile README and its animated SVGs (light + dark).

Usage: python scripts/build.py
Fetches the public contribution calendar, writes assets/*.svg and README.md.
"""
import datetime as dt
import re
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

USER = "OnsKoukiPro"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
RAW = f"https://raw.githubusercontent.com/{USER}/{USER}/main/assets"
W = 1200

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

THEMES = {
    "light": {"accent": "#6d28d9", "text": "#1f2328", "muted": "#656d76", "line": "#d0d7de",
              "dots": ["#ebedf0", "#ddd6fe", "#a78bfa", "#7c3aed", "#5b21b6"]},
    "dark": {"accent": "#a78bfa", "text": "#e6edf3", "muted": "#8b949e", "line": "#30363d",
             "dots": ["#161b22", "#2e1065", "#5b21b6", "#7c3aed", "#a78bfa"]},
}

INTRO = ("I'm Ons. A creative technologist who takes ideas from a napkin sketch "
         "to a running cluster. I dream it, design it, build it, teach it to think, "
         "and ship it.")

STORY = [
    ("01", "packets", "An RL agent that fights DDoS floods inside an SDN controller", "insat"),
    ("02", "traps", "A Kubernetes honeynet, then DevSecOps on a pandemic analytics platform", "2024"),
    ("03", "fibre", "Planning GPON, DWDM and 5G networks at Omantel", "2025"),
    ("04", "signals", "Acoustic-emission failure prediction with CNNs and RNNs", "2025"),
    ("05", "startup", "Founding AI/ML engineer at Clarity Chain, idea to live product", "2025"),
    ("06", "energy", "Platform services for battery storage at ACCURE, on EKS", "now"),
]

WORK = [
    ("claritychains", "ClarityChains", "LLM agents that read supplier offers and pick a winner",
     "react · django · langchain", "https://clarity-chains.vercel.app"),
    ("model", "claritychains-model", "Price forecasts and hedging for battery metals",
     "python · streamlit · scipy", f"https://github.com/{USER}/claritychains-model"),
    ("honeypot", "Honeypot-CK8s", "A honeynet in a vCluster. Attackers get in, I get dashboards",
     "k8s · fluentd · opensearch", f"https://github.com/{USER}/Honeypot-CK8s"),
    ("rl-ddos", "RL × SDN", "A network that learns when to block a flood (94.6%)",
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
    ("ml & data", ["pytorch", "tensorflow", "scikit-learn", "langchain", "pandas", "airflow"]),
    ("backend", ["python", "fastapi", "django", "node / nestjs", "spring", "postgres"]),
    ("cloud & security", ["aws · azure", "kubernetes", "terraform · pulumi", "argo cd · helm", "vault · keycloak"]),
    ("frontend", ["typescript", "react", "next.js", "angular", "tailwind"]),
]

BASE_CSS = """
.f { opacity: 0; animation: fade 1.4s ease-out forwards; }
@keyframes fade { to { opacity: 1; } }
"""


def arrow(t, size, begin):
    """A ↗ that sits right after the label and hops up-right every few seconds."""
    hop = 'values="{a};{b};{a};{a}" keyTimes="0;0.05;0.1;1" dur="5s" begin="%.1fs" repeatCount="indefinite"' % begin
    return (f'<tspan dx="6" font-size="{size}" font-weight="400" fill="{t["accent"]}">↗'
            f'<animate attributeName="dx" {hop.format(a=6, b=10)}/>'
            f'<animate attributeName="dy" {hop.format(a=-2, b=-6)}/></tspan>')


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
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" fill="none" role="img" aria-label="{escape(label)}">
<defs>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="300" y2="0">
    <stop offset="0" stop-color="{t['accent']}"/><stop offset="0.45" stop-color="{t['accent']}"/>
    <stop offset="0.5" stop-color="{t['text']}" stop-opacity="0.9"/>
    <stop offset="0.55" stop-color="{t['accent']}"/><stop offset="1" stop-color="{t['accent']}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-400 0;{width} 0;{width} 0" keyTimes="0;0.25;1" dur="12s" repeatCount="indefinite"/>
  </linearGradient>
</defs>
<style>{BASE_CSS}{css}</style>
{body}
</svg>
"""


def delay(s):
    return f'style="animation-delay:{s:.2f}s"'


def wrap(text, size, width):
    lines, line = [], ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if len(candidate) * size * 0.43 > width and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    return lines + [line]


def top(theme, total, since):
    t = THEMES[theme]
    body = f"""<text class="f" {delay(0.2)} x="0" y="28" font-family="{SANS}" font-size="22" font-weight="600" fill="{t['text']}">Ons Kouki</text>
<text class="f" {delay(0.5)} x="{W / 2}" y="28" text-anchor="middle" font-family="{SANS}" font-size="22" font-weight="600" fill="{t['muted']}"><tspan fill="url(#shine)">{total:,}</tspan> contributions since {since}</text>
<text class="f" {delay(0.8)} x="{W}" y="28" text-anchor="end" font-family="{MONO}" font-size="20" fill="{t['muted']}">readme.md</text>
<line class="f" {delay(0.8)} x1="0" y1="50" x2="{W}" y2="50" stroke="{t['line']}"/>"""
    return svg(W, 56, theme, body, f"Ons Kouki · {total} contributions since {since}")


def link(theme, label, i):
    t = THEMES[theme]
    width = len(label) * 13 + 40
    body = f"""<g class="f" {delay(1 + i * 0.4)}>
<text x="0" y="26" font-family="{SANS}" font-size="24" font-weight="600" fill="url(#shine)">{escape(label)}{arrow(t, 18, 2 + i * 1.7)}</text>
</g>"""
    return svg(width, 34, theme, body, label), width


def main(theme, calendars):
    t = THEMES[theme]
    size = 42
    lines = wrap(INTRO, size, W - 40)
    out, k = [], 0
    for li, line in enumerate(lines):
        spans = []
        for ch in line + " ":
            spans.append(f'<tspan class="f" {delay(1.2 + k * 0.018)}>{escape(ch)}</tspan>')
            k += 1
        out.append(f'<text x="0" y="{50 + li * 56}" font-family="{SANS}" font-size="{size}" font-weight="300" fill="{t["accent"]}" xml:space="preserve">{"".join(spans)}</text>')

    # contribution graph: one block per year, side by side
    gy = 50 + len(lines) * 56 + 30
    cell, gap, ygap = 6.2, 1.3, 18
    years = sorted(calendars)
    block = (W - ygap * (len(years) - 1)) / len(years)
    step = min(cell + gap, block / 53)
    start = 1.2 + k * 0.018
    for yi, year in enumerate(years):
        x0 = yi * (block + ygap)
        jan1 = dt.date(year, 1, 1)
        offset = (jan1.weekday() + 1) % 7  # Sunday-first rows, like GitHub
        rects = []
        for date, level in sorted(calendars[year].items()):
            idx = (date - jan1).days + offset
            col, row = divmod(idx, 7)
            rects.append(f'<rect class="f l{level}" {delay(start + yi * 0.6 + col * 0.03)} x="{x0 + col * step:.1f}" y="{gy + row * step:.1f}" width="{step - gap:.1f}" height="{step - gap:.1f}" rx="1.5"/>')
        out.append("".join(rects))
        out.append(f'<text class="f" {delay(start + yi * 0.6)} x="{x0}" y="{gy + 7 * step + 26:.0f}" font-family="{SANS}" font-size="18" font-weight="600" fill="{t["accent"]}">{year}</text>')
    height = gy + 7 * step + 36
    css = "".join(f".l{i}{{fill:{c};stroke:#000;stroke-opacity:0.05}}" for i, c in enumerate(t["dots"]))
    return svg(W, int(height), theme, "\n".join(out), INTRO, css)


def section(theme, title, i0=0):
    t = THEMES[theme]
    body = f"""<text class="f" {delay(0.3 + i0)} x="0" y="30" font-family="{MONO}" font-size="18" fill="{t['muted']}">{escape(title)}</text>
<line class="f" {delay(0.3 + i0)} x1="0" y1="46" x2="{W}" y2="46" stroke="{t['line']}"/>"""
    return svg(W, 52, theme, body, title)


def story(theme):
    t = THEMES[theme]
    rows = []
    for i, (num, title, text, when) in enumerate(STORY):
        y = 34 + i * 50
        rows.append(f"""<g class="f" {delay(0.6 + i * 0.25)}>
<text x="0" y="{y}" font-family="{MONO}" font-size="18" fill="{t['muted']}">{num}</text>
<text x="56" y="{y}" font-family="{SANS}" font-size="22" font-weight="600" fill="{t['accent']}">{title}</text>
<text x="200" y="{y}" font-family="{SANS}" font-size="22" fill="{t['text']}">{escape(text)}</text>
<text x="{W}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="18" fill="{t['accent'] if when == 'now' else t['muted']}">{when}</text>
</g>""")
    return svg(W, 34 + len(STORY) * 50 - 30, theme, "\n".join(rows), "The story so far: " + "; ".join(s[2] for s in STORY))


def work(theme, name, text, stack, i):
    t = THEMES[theme]
    body = f"""<g class="f" {delay(0.6 + i * 0.25)}>
<text x="0" y="32" font-family="{SANS}" font-size="22" font-weight="600" fill="url(#shine)">{escape(name)}{arrow(t, 16, 3 + i * 1.3)}</text>
<text x="300" y="32" font-family="{SANS}" font-size="22" fill="{t['text']}">{escape(text)}</text>
<text x="{W}" y="32" text-anchor="end" font-family="{MONO}" font-size="17" fill="{t['muted']}">{escape(stack)}</text>
<line x1="0" y1="50" x2="{W}" y2="50" stroke="{t['line']}"/>
</g>"""
    return svg(W, 52, theme, body, f"{name}: {text}")


def stack(theme):
    t = THEMES[theme]
    col = W / len(STACK)
    out = []
    for i, (title, items) in enumerate(STACK):
        x = i * col
        out.append(f'<g class="f" {delay(0.6 + i * 0.2)}><text x="{x}" y="30" font-family="{SANS}" font-size="20" font-weight="600" fill="{t["accent"]}">{escape(title)}</text>')
        for j, item in enumerate(items):
            out.append(f'<text x="{x}" y="{66 + j * 32}" font-family="{MONO}" font-size="19" fill="{t["text"]}">{escape(item)}</text>')
        out.append("</g>")
    height = 66 + max(len(items) for _, items in STACK) * 32 - 10
    return svg(W, height, theme, "\n".join(out), "Stack: " + "; ".join(f"{a}: {', '.join(b)}" for a, b in STACK))


def outro(theme):
    t = THEMES[theme]
    body = f"""<text class="f" {delay(0.5)} x="0" y="36" font-family="{SANS}" font-size="26" font-weight="300" fill="{t['accent']}">to be continued<tspan>▍<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" repeatCount="indefinite"/></tspan></text>
<text class="f" {delay(1)} x="{W}" y="36" text-anchor="end" font-family="{SANS}" font-size="20" fill="{t['muted']}">English · French · Arabic</text>"""
    return svg(W, 52, theme, body, "To be continued. Speaks English, French and Arabic.")


def picture(name, alt, width="100%", align=""):
    v = dt.date.today().isoformat()
    a = f' align="{align}"' if align else ""
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{RAW}/{name}-dark.svg?v={v}">'
            f'<img src="{RAW}/{name}-light.svg?v={v}" alt="{escape(alt)}" width="{width}"{a}></picture>')


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
        files = {"top": top(theme, total, this_year - 4), "main": main(theme, calendars),
                 "story-title": section(theme, "the story so far"), "story": story(theme),
                 "work-title": section(theme, "things i've made"),
                 "stack-title": section(theme, "toolbox"), "stack": stack(theme), "outro": outro(theme)}
        for i, (slug, label, _) in enumerate(LINKS):
            files[f"link-{slug}"], widths[slug] = link(theme, label, i)
        for i, (slug, name, text, tech, _) in enumerate(WORK):
            files[f"work-{slug}"] = work(theme, name, text, tech, i)
        for name, content in files.items():
            (ASSETS / f"{name}-{theme}.svg").write_text(content, encoding="utf-8")

    links = "\n".join(f'<a href="{url}">{picture(f"link-{slug}", label, str(round(widths[slug] * 0.7)))}</a>'
                      for slug, label, url in LINKS)
    work_rows = "\n".join(f'<a href="{url}">{picture(f"work-{slug}", f"{name}: {text}")}</a>'
                          for slug, name, text, _, url in WORK)
    readme = f"""{picture("top", f"Ons Kouki · {total} contributions")}

{links}

{picture("main", INTRO)}

{picture("story-title", "The story so far")}
{picture("story", "; ".join(f"{s[1]}: {s[2]}" for s in STORY))}

{picture("work-title", "Things I've made")}
{work_rows}

{picture("stack-title", "Toolbox")}
{picture("stack", "; ".join(f"{a}: {', '.join(b)}" for a, b in STACK))}

{picture("outro", "To be continued")}
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(f"{total} contributions, {len(list(ASSETS.glob('*.svg')))} svgs")


if __name__ == "__main__":
    build()
