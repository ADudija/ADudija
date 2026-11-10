"""Build the terminal-style profile card and the link buttons.

Standard library only, so it runs as-is in GitHub Actions:
    GITHUB_TOKEN=... python tools/build_card.py
Writes dark_mode.svg, light_mode.svg and link_<name>_<theme>.svg.
Without a token the stats are fetched anonymously (fine for a few runs).
"""
import json
import os
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
USER = "ADudija"

# Edit these freely; the card is rebuilt from them on every run.
HEADER = "albi@dudija"
ABOUT = [
    ("Name", "Albi Dudija"),
    ("Role", "Founder & Software Engineer"),
    ("Company", "Freelancer"),
    ("Location", "Tiranë, Albania"),
    ("Experience", "10+ years"),
    ("Focus", "AI-powered products"),
    ("Builds", "Websites, web apps, SaaS"),
]
CONTACT = [
    ("Website", "albidudija.com"),
    ("X", "@albidudija"),
    ("GitHub", "@ADudija"),
]
LINKS = [
    ("website", "Website", "albidudija.com"),
    ("x", "X / Twitter", "@albidudija"),
    ("github", "GitHub", "@ADudija"),
]

THEMES = {
    "dark": {"bg": "#161b22", "fg": "#c9d1d9", "key": "#F76E0A",
             "value": "#a5d6ff", "dim": "#616e7f", "border": "#30363d"},
    "light": {"bg": "#f6f8fa", "fg": "#24292f", "key": "#c2410c",
              "value": "#0a3069", "dim": "#8c959f", "border": "#d0d7de"},
}

FONT = 12
LINE = 18
CHAR_W = FONT * 0.6
ART_FONT = 11
ART_LINE = 12.4
INFO_COLS = 52
# Some SVG renderers collapse plain spaces even with white-space:pre.
NBSP = "\u00a0"


def gh(path):
    req = urllib.request.Request("https://api.github.com" + path,
                                 headers={"Accept": "application/vnd.github+json",
                                          "User-Agent": "profile-card"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_stats():
    try:
        user = gh(f"/users/{USER}")
        repos = gh(f"/users/{USER}/repos?per_page=100&type=owner")
        commits = gh(f"/search/commits?q=author:{USER}&per_page=1")
    except Exception as exc:  # keep the last card rather than failing the run
        print("stats unavailable:", exc)
        return None
    return [
        ("Repos", f"{user['public_repos']:,}"),
        ("Stars", f"{sum(r['stargazers_count'] for r in repos):,}"),
        ("Followers", f"{user['followers']:,}"),
        ("Commits", f"{commits['total_count']:,}"),
    ]


def dotted(key, value, width=INFO_COLS):
    """One `Key: ....... value` row as (key, dots, value)."""
    dots = max(width - len(key) - len(value) - 3, 1)
    return key, "." * dots, value


def section(title, width=INFO_COLS):
    return ("section", f"- {title} " + "—" * max(width - len(title) - 3, 2))


def build_card(theme, art, stats):
    c = THEMES[theme]
    rows = [("title", HEADER), ("rule", "-" * len(HEADER))]
    rows += [("pair", dotted(k, v)) for k, v in ABOUT]
    rows += [("blank", ""), section("Contact")]
    rows += [("pair", dotted(k, v)) for k, v in CONTACT]
    if stats:
        rows += [("blank", ""), section("GitHub Stats")]
        rows += [("pair", dotted(k, v)) for k, v in stats]
    rows += [("blank", ""), ("prompt", "")]

    art_w = max(len(line) for line in art) * ART_FONT * 0.6
    info_x = 30 + art_w + 30
    width = round(info_x + INFO_COLS * CHAR_W + 30)
    height = round(max(len(art) * ART_LINE, len(rows) * LINE) + 60)
    art_top = (height - len(art) * ART_LINE) / 2 + ART_LINE * 0.8
    info_top = (height - len(rows) * LINE) / 2 + LINE * 0.8

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Menlo,Consolas,\'DejaVu Sans Mono\',monospace">',
        "<style>text,tspan{white-space:pre}"
        f".k{{fill:{c['key']}}}.v{{fill:{c['value']}}}.d{{fill:{c['dim']}}}"
        f".t{{fill:{c['key']};font-weight:bold}}"
        "@keyframes blink{50%{opacity:0}}.cur{animation:blink 1s step-end infinite}</style>",
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="15" '
        f'fill="{c["bg"]}" stroke="{c["border"]}"/>',
        f'<text fill="{c["fg"]}" font-size="{ART_FONT}">',
    ]
    for i, line in enumerate(art):
        line = escape(line).replace(" ", NBSP)
        out.append(f'<tspan x="30" y="{art_top + i * ART_LINE:.1f}">{line}</tspan>')
    out.append(f'</text><text fill="{c["fg"]}" font-size="{FONT}">')
    for i, (kind, val) in enumerate(rows):
        y = f'{info_top + i * LINE:.1f}'
        pos = f'x="{info_x:.1f}" y="{y}"'
        if kind == "title":
            out.append(f'<tspan {pos} class="t">{escape(val)}</tspan>')
        elif kind in ("rule", "section"):
            out.append(f'<tspan {pos} class="d">{escape(val)}</tspan>')
        elif kind == "pair":
            k, dots, v = val
            out.append(f'<tspan {pos} class="k">{escape(k)}</tspan>'
                       f'<tspan>:{NBSP}</tspan><tspan class="d">{dots}{NBSP}</tspan>'
                       f'<tspan class="v">{escape(v)}</tspan>')
        elif kind == "prompt":
            out.append(f'<tspan {pos} class="k">&gt; </tspan><tspan class="cur">█</tspan>')
    out.append("</text></svg>")
    return "\n".join(out) + "\n"


def build_link(theme, label, value):
    c = THEMES[theme]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="56" viewBox="0 0 300 56" '
        "font-family=\"Menlo,Consolas,'DejaVu Sans Mono',monospace\">"
        f'<rect x="4.5" y="4.5" width="291" height="47" rx="10" fill="{c["bg"]}" stroke="{c["border"]}"/>'
        f'<text x="22" y="33" font-size="14"><tspan fill="{c["key"]}">&gt; {escape(label)}</tspan>'
        f'<tspan fill="{c["dim"]}"> · </tspan><tspan fill="{c["value"]}">{escape(value)}</tspan></text>'
        "</svg>\n"
    )


def main():
    stats = fetch_stats()
    for theme in THEMES:
        art = (ROOT / "assets" / f"ascii-{theme}.txt").read_text().rstrip("\n").split("\n")
        card = ROOT / f"{theme}_mode.svg"
        if stats is None and card.exists():
            continue  # API hiccup: keep yesterday's numbers
        card.write_text(build_card(theme, art, stats))
        for name, label, value in LINKS:
            (ROOT / f"link_{name}_{theme}.svg").write_text(build_link(theme, label, value))


if __name__ == "__main__":
    main()
