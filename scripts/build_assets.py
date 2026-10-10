#!/usr/bin/env python3
"""Generate the animated SVG cards used by README.md.

Everything shown on the profile lives in the PROFILE DATA block below.
Edit it, then rebuild every card in assets/:

    pip install fonttools brotli
    python3 scripts/build_assets.py

Fonts (Space Grotesk, JetBrains Mono, SIL OFL) are subset and embedded so the
cards look identical in every browser. Brand icons come from Simple Icons (CC0).
"""

import base64
import html
import io
import json
import math
import random
import re
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
ICONS = json.loads((HERE / "icons.json").read_text())

# ───────────────────────────── PROFILE DATA ──────────────────────────────

NAME = "Himanshu Jasoriya"
ROLES = ["AI Engineer", "Founder", "8× Hackathon Winner"]
TAGLINES = [
    "building AI that sees, reasons & ships.",
    "computer vision · LLMs · RAG · agentic AI",
    "from research paper to real product.",
    "now: Neuronest — AI + VR for mental health",
]
STATUS = "open to collabs, hackathon teams & hard problems"

# (place, event, organiser, tier)
HACKATHONS = [
    (1, "Geospatial Intelligence Hackathon 2026", "Open national hackathon", "NATIONAL"),
    (1, "HACKSTORM 2025", "National-level hackathon", "NATIONAL"),
    (1, "IdeaThon 2025", "ACEIT, Jaipur", "INSTITUTE"),
    (2, "HackStorm", "Arya College of Engineering & IT, Jaipur", "INSTITUTE"),
    (2, "DevSummit Hackathon", "Jagannath University", "UNIVERSITY"),
    (2, "Genisys 1.0", "MNIT Jaipur", "INSTITUTE"),
    (3, "HackJKLU 5.0", "JKLU, Jaipur", "OPEN"),
    (3, "AceHack Hackathon", "Open hackathon", "OPEN"),
]
SPOTLIGHT = {"rank": 10, "field": 28_000, "event": "India Innovates", "venue": "Bharat Mandapam, New Delhi"}

ABOUT_CODE = '''\
# himanshu.py — the human behind the commits

class HimanshuJasoriya(AIEngineer, Founder):
    """Turns research-grade AI into products people actually use."""

    def __init__(self):
        self.education = "B.Tech · Artificial Intelligence & Data Science"
        self.focus     = ["Computer Vision", "LLMs", "RAG", "Agentic AI"]
        self.building  = "Neuronest — AI + VR mental-health therapy"
        self.exploring = ["AI Agents", "LoRA / QLoRA", "Scalable GenAI"]
        self.record    = {"podiums": 8, "india_innovates": "Top 10 / 28,000"}
        self.beyond    = ["Public Speaking", "Investor Pitching", "Team Building"]

    def mission(self) -> str:
        return "AI that is technically strong, commercially viable & socially impactful."'''

# (title, one-liner, [icon keys from icons.json or plain labels])
STACK = [
    ("Languages", "the foundations I think in", ["python", "cpp", "typescript", "javascript", "SQL"]),
    ("AI · ML · Vision", "models that see, classify & predict",
     ["pytorch", "tensorflow", "sklearn", "opencv", "ultralytics:YOLOv8", "mediapipe", "numpy", "pandas"]),
    ("LLMs · GenAI", "RAG pipelines, agents & fine-tuning",
     ["huggingface", "langchain", "ollama", "streamlit", "gradio", "jupyter"]),
    ("Full Stack", "turning models into real products",
     ["react", "nextjs", "nodejs", "express", "mongodb", "postgresql"]),
    ("Ship · Infra", "containerise, version, test, deploy",
     ["docker", "git", "github", "linux", "firebase", "postman"]),
]
LEVELLING_UP = ["AI Agents", "LoRA / QLoRA", "Multimodal AI", "Scalable GenAI Systems"]

PLAYBOOK = [
    ("Find the pain", "Mental health, floods, accessibility, energy, hospitals. Real problem first, model second."),
    ("Go deep", "Papers, data and first principles. Pick the architecture the problem deserves."),
    ("Prototype fast", "Whiteboard to working demo inside a single hackathon sprint."),
    ("Ship it", "Full-stack, containerised and deployable. Not just a notebook."),
    ("Pitch & scale", "Win over judges, investors and users, then build the team."),
]
BEYOND = ["Public Speaking", "Investor Pitching", "Team Building", "Product Strategy", "Startup Ecosystems"]

SECTIONS = {
    "about": ("01", "About Me", "// the human behind the commits"),
    "stack": ("02", "Tech Stack", "// the tools I build with, layer by layer"),
    "trophies": ("03", "Hackathon Record", "// 8 podiums, built under pressure"),
    "playbook": ("04", "How I Build", "// from a real problem to a product people use"),
    "pulse": ("05", "GitHub Pulse", "// live activity, refreshed every 12 hours"),
}

FOOTER_TITLE = "Let's build something that matters."
FOOTER_SUB = "Open to collaborations · hackathon teams · hard problems"
EMAIL = "hjasoriya007@gmail.com"

# ───────────────────────────── DESIGN TOKENS ─────────────────────────────

BG0, BG1, CARD, CARD2, LINE = "#050911", "#0a1628", "#0b1424", "#0f1b30", "#1b2a44"
CYAN, VIOLET, GREEN = "#00d4ff", "#8b5cf6", "#22c55e"
TEXT, MUTED, DIM = "#e6edf6", "#8b9bb4", "#56657f"
MEDALS = {
    1: ("#fde68a", "#f59e0b", "#b45309", "Champion"),
    2: ("#f1f5f9", "#94a3b8", "#475569", "Runner-up"),
    3: ("#fed7aa", "#d97706", "#7c2d12", "Third place"),
}
TIERS = {"NATIONAL": CYAN, "INSTITUTE": "#a78bfa", "UNIVERSITY": "#2dd4bf", "OPEN": "#4ade80"}

FONT_FILES = {
    "sg5": ("SG", 500, "normal", "space-grotesk-latin-500-normal.woff2"),
    "sg7": ("SG", 700, "normal", "space-grotesk-latin-700-normal.woff2"),
    "jb4": ("JB", 400, "normal", "jetbrains-mono-latin-400-normal.woff2"),
    "jb7": ("JB", 700, "normal", "jetbrains-mono-latin-700-normal.woff2"),
    "jbi": ("JB", 400, "italic", "jetbrains-mono-latin-400-italic.woff2"),
}
FALLBACK = {"SG": "'Segoe UI',Helvetica,Arial,sans-serif", "JB": "'SFMono-Regular',Consolas,'Liberation Mono',monospace"}


class Font:
    def __init__(self, path):
        self.path = path
        self.tt = TTFont(path)
        self.cmap = self.tt.getBestCmap()
        self.hmtx = self.tt["hmtx"]
        self.upm = self.tt["head"].unitsPerEm

    def width(self, text, size, spacing=0.0):
        adv = sum(self.hmtx[self.cmap[ord(c)]][0] if ord(c) in self.cmap else self.upm * 0.6 for c in text)
        return adv * size / self.upm + spacing * len(text)


FONTS = {k: Font(HERE / "fonts" / v[3]) for k, v in FONT_FILES.items()}


def tw(text, cls, size, spacing=0.0):
    return FONTS[cls].width(text, size, spacing)


def esc(s):
    return html.escape(s, quote=True)


def subset_b64(font, chars):
    missing = sorted(c for c in chars if ord(c) not in font.cmap and not c.isspace())
    if missing:
        print(f"  ! {font.path.name} has no glyph for {''.join(missing)!r} (system fallback used)")
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.hinting = False
    opts.desubroutinize = True
    tt = TTFont(font.path)
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(chars)) + " ")
    sub.subset(tt)
    buf = io.BytesIO()
    tt.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


BASE_CSS = """
@media (prefers-reduced-motion: reduce){*{animation:none!important}}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes fadein{from{opacity:0}to{opacity:1}}
@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}
@keyframes pulse{0%,100%{opacity:.15}50%{opacity:.9}}
.rise{animation:rise .7s cubic-bezier(.2,.7,.2,1) both}
.fade{animation:fadein .8s ease both}
"""


def write_svg(name, w, h, body, css="", title=""):
    """Wrap body in an <svg>, embed only the font faces it uses, save to assets/."""
    chars = set(html.unescape("".join(re.findall(r">([^<]+)<", body))))
    faces, rules = [], []
    for cls, (family, weight, style, _) in FONT_FILES.items():
        if not re.search(rf'class="[^"]*\b{cls}\b', body):
            continue
        data = subset_b64(FONTS[cls], chars)
        faces.append(f"@font-face{{font-family:{family};font-weight:{weight};font-style:{style};"
                     f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")
        rules.append(f".{cls}{{font-family:{family},{FALLBACK[family]};font-weight:{weight};font-style:{style}}}")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
           f'fill="none" role="img" aria-label="{esc(title)}">\n<title>{esc(title)}</title>\n'
           f"<style>{''.join(faces)}{''.join(rules)}{BASE_CSS}{css}</style>\n{body}\n</svg>\n")
    (ASSETS / name).write_text(svg)
    print(f"  {name:<24} {len(svg) / 1024:6.1f} KB")


def text(x, y, s, cls, size, fill, anchor="start", extra=""):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" font-size="{size}" fill="{fill}"{a} {extra}>{esc(s)}</text>'


def icon(key, x, y, size, color=None):
    ic = ICONS[key]
    fill = color or readable(ic["hex"])
    return (f'<path transform="translate({x:.1f} {y:.1f}) scale({size / 24:.4f})" '
            f'd="{ic["path"]}" fill="{fill}"/>')


def readable(hex_):
    """Brand colour, unless it is too dark to see on the navy cards."""
    r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return TEXT if lum < 0.28 else f"#{hex_}"


def panel(w, h, rx=18, gid="pstroke"):
    """Shared navy panel background with a cyan→violet hairline border."""
    return (f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{CYAN}" stop-opacity=".55"/>'
            f'<stop offset=".5" stop-color="{VIOLET}" stop-opacity=".35"/>'
            f'<stop offset="1" stop-color="{CYAN}" stop-opacity=".12"/></linearGradient>'
            f'<linearGradient id="pbg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG1}"/>'
            f'<stop offset="1" stop-color="{BG0}"/></linearGradient></defs>'
            f'<rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="{rx}" fill="url(#pbg)" '
            f'stroke="url(#{gid})" stroke-width="1.5"/>')


# ──────────────────────────────── HERO ───────────────────────────────────

def build_hero():
    W, H = 1000, 404
    rnd = random.Random(7)
    golds = sum(1 for h in HACKATHONS if h[0] == 1)
    stats = [
        (f"{len(HACKATHONS):02d}", "hackathon podiums"),
        (f"{golds:02d}", "first-place finishes"),
        (f"Top {SPOTLIGHT['rank']}", f"of {SPOTLIGHT['field']:,} · {SPOTLIGHT['event']}"),
        ("01", "startup in motion"),
    ]
    b = []
    b.append(f'''<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#060b17"/><stop offset="1" stop-color="{BG1}"/></linearGradient>
<radialGradient id="gc" cx=".78" cy=".4" r=".42"><stop offset="0" stop-color="{CYAN}" stop-opacity=".17"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
<radialGradient id="gv" cx=".05" cy="1" r=".55"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".2"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>
<pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" stroke="#13243c" stroke-width="1"/></pattern>
<radialGradient id="fg" cx=".6" cy=".35" r=".75"><stop offset="0" stop-color="#fff" stop-opacity=".8"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<mask id="fade"><rect width="{W}" height="{H}" fill="url(#fg)"/></mask>
<clipPath id="card"><rect width="{W}" height="{H}" rx="20"/></clipPath>
<linearGradient id="name" x1="48" x2="570" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#ffffff"/><stop offset=".55" stop-color="#c8f4ff"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>
<linearGradient id="shine" x1="-260" x2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
<animateTransform attributeName="gradientTransform" type="translate" values="0 0;0 0;900 0" keyTimes="0;.6;1" dur="7s" repeatCount="indefinite"/></linearGradient>
<linearGradient id="num" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>
<linearGradient id="hstroke" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity=".75"/><stop offset=".5" stop-color="{VIOLET}" stop-opacity=".45"/><stop offset="1" stop-color="{CYAN}" stop-opacity=".15"/></linearGradient>
</defs>
<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#fade)"/>
<rect width="{W}" height="{H}" fill="url(#gc)"/>
<rect width="{W}" height="{H}" fill="url(#gv)"/>''')

    # twinkling particles
    for i in range(34):
        x, y = rnd.uniform(20, W - 20), rnd.uniform(16, 300)
        b.append(f'<circle class="tw" cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(.6, 1.5):.1f}" fill="#9fe8ff" '
                 f'style="animation-delay:-{rnd.uniform(0, 5):.2f}s;animation-duration:{rnd.uniform(3, 6):.1f}s"/>')

    # neural network: inputs on the left, outcomes on the right
    xs, counts, cy, gap = [652, 737, 822, 907], [4, 6, 6, 3], 158, 38
    nodes = [[(x, cy + (i - (n - 1) / 2) * gap) for i in range(n)] for x, n in zip(xs, counts)]
    edges = []
    for a, c in zip(nodes, nodes[1:]):
        for p in a:
            for q in c:
                edges.append(f'M{p[0]} {p[1]:.0f}L{q[0]} {q[1]:.0f}')
    b.append(f'<path d="{"".join(edges)}" stroke="#1a3a5c" stroke-width="1" opacity=".75"/>')
    for k in range(12):
        pts = [layer[rnd.randrange(len(layer))] for layer in nodes]
        d = "M" + "L".join(f"{x} {y:.0f}" for x, y in pts)
        col = CYAN if k % 3 else "#b69cff"
        delay = -k * 0.53
        b.append(f'<path class="sig glow" d="{d}" pathLength="100" stroke="{col}" style="animation-delay:{delay:.2f}s"/>'
                 f'<path class="sig" d="{d}" pathLength="100" stroke="{col}" style="animation-delay:{delay:.2f}s"/>')
    for li, layer in enumerate(nodes):
        for ni, (x, y) in enumerate(layer):
            out = li == len(nodes) - 1
            col = VIOLET if out else CYAN
            b.append(f'<circle class="halo" cx="{x}" cy="{y:.0f}" r="11" fill="{col}" '
                     f'style="animation-delay:-{rnd.uniform(0, 3):.2f}s"/>'
                     f'<circle cx="{x}" cy="{y:.0f}" r="5.5" fill="{BG1}" stroke="{col}" stroke-width="1.6"/>')
    for (x, y), lab in zip(nodes[0], ["pixels", "text", "signals", "ideas"]):
        b.append(text(x - 16, y + 4.5, lab, "jb4", 13, DIM, "end"))
    for (x, y), lab in zip(nodes[-1], ["products", "startups", "impact"]):
        b.append(text(x + 16, y + 4.5, lab, "jb4", 13, "#c4b5fd"))

    # left column
    b.append(f'<text x="48" y="84" class="jb4 rise" font-size="16" fill="{CYAN}"><tspan fill="{DIM}">$</tspan> whoami</text>')
    b.append(text(48, 148, NAME, "sg7 rise", 56, "url(#name)", extra='style="animation-delay:.1s"'))
    b.append(text(48, 148, NAME, "sg7", 56, "url(#shine)", extra='opacity=".55"'))
    x = 49
    parts = []
    for i, r in enumerate(ROLES):
        if i:
            parts.append(f'<tspan fill="{CYAN}">  ·  </tspan>')
        parts.append(f"<tspan>{esc(r)}</tspan>")
    b.append(f'<text x="{x}" y="188" class="sg5 rise" font-size="20" fill="#cbd5e1" xml:space="preserve" '
             f'style="white-space:pre;animation-delay:.2s">{"".join(parts)}</text>')

    # typing taglines (SMIL, char by char)
    b.append(type_cycle(TAGLINES, x0=48, y=230, size=16))

    # status pill
    sw = tw(STATUS, "sg5", 14) + 50
    b.append(f'<g class="rise" style="animation-delay:.35s"><rect x="48" y="252" width="{sw:.0f}" height="30" rx="15" '
             f'fill="{GREEN}" fill-opacity=".08" stroke="{GREEN}" stroke-opacity=".4"/>'
             f'<circle class="ping" cx="68" cy="267" r="7" fill="{GREEN}"/><circle cx="68" cy="267" r="4" fill="{GREEN}"/>'
             + text(84, 272, STATUS, "sg5", 14, "#86efac") + "</g>")

    # stat strip
    sx, sy, swid, sh = 24, 312, W - 48, 68
    b.append(f'<rect x="{sx}" y="{sy}" width="{swid}" height="{sh}" rx="14" fill="#ffffff" fill-opacity=".025" stroke="#1c2d48"/>')
    cw = swid / len(stats)
    for i, (num, lab) in enumerate(stats):
        cx = sx + cw * i + cw / 2
        if i:
            b.append(f'<path d="M{sx + cw * i:.0f} {sy + 16}V{sy + sh - 16}" stroke="#1c2d48"/>')
        b.append(f'<g class="rise" style="animation-delay:{.45 + i * .12:.2f}s">'
                 + text(cx, sy + 36, num, "sg7", 28, "url(#num)", "middle")
                 + text(cx, sy + 56, lab, "sg5", 13.5, MUTED, "middle") + "</g>")
    b.append("</g>")
    b.append(f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="19.5" stroke="url(#hstroke)" stroke-width="1.5"/>')

    css = """
@keyframes tw{0%,100%{opacity:.1}50%{opacity:.8}}
.tw{animation:tw 4s ease-in-out infinite}
@keyframes flow{from{stroke-dashoffset:12}to{stroke-dashoffset:-100}}
.sig{fill:none;stroke-width:2.2;stroke-linecap:round;stroke-dasharray:12 200;animation:flow 3.4s linear infinite}
.glow{stroke-width:7;opacity:.22}
@keyframes halo{0%,100%{opacity:0}50%{opacity:.28}}
.halo{animation:halo 3s ease-in-out infinite}
@keyframes ping{0%{opacity:.6;transform:scale(.6)}100%{opacity:0;transform:scale(2.2)}}
.ping{transform-box:fill-box;transform-origin:center;animation:ping 1.8s ease-out infinite}
.cur{animation:blink 1s step-end infinite}
"""
    write_svg("hero.svg", W, H, "\n".join(b), css, f"{NAME} — {' · '.join(ROLES)}")


def type_cycle(lines, x0, y, size, slot=4.6, cps=26):
    """Taglines typed and erased one after another, forever (SMIL, discrete steps)."""
    cw = tw("M", "jb4", size)
    prefix = "> "
    tx = x0 + cw * len(prefix)
    total = slot * len(lines)
    out = [f'<text x="{x0}" y="{y}" class="jb7" font-size="{size}" fill="{VIOLET}">{esc(prefix.strip())}</text>']
    for i, line in enumerate(lines):
        n = len(line)
        start = i * slot + 0.15
        t_type = n / cps
        t_erase_start = (i + 1) * slot - 0.75
        assert start + t_type < t_erase_start, "tagline too long for its slot"
        pts = [(0.0, 0, i == 0)]
        pts += [(start + c / cps, c, True) for c in range(1, n + 1)]
        pts += [(t_erase_start + (n - c) * 0.45 / n, c, True) for c in range(n - 1, -1, -1)]
        pts.append((t_erase_start + 0.55, 0, False))
        kt = ";".join(f"{t / total:.4f}" for t, _, _ in pts)
        wv = ";".join(f"{c * cw:.1f}" for _, c, _ in pts)
        xv = ";".join(f"{tx + c * cw:.1f}" for _, c, _ in pts)
        vis = ";".join("1" if v else "0" for _, _, v in pts)
        default_w = n * cw if i == 0 else 0
        anim = f'keyTimes="{kt}" dur="{total}s" calcMode="discrete" repeatCount="indefinite"'
        out.append(f'<clipPath id="tl{i}"><rect x="{tx}" y="{y - size}" width="{default_w:.1f}" height="{size * 1.5}">'
                   f'<animate attributeName="width" values="{wv}" {anim}/></rect></clipPath>')
        out.append(f'<text x="{tx}" y="{y}" class="jb4" font-size="{size}" fill="{CYAN}" clip-path="url(#tl{i})" '
                   f'xml:space="preserve" style="white-space:pre">{esc(line)}</text>')
        # blink lives on the wrapper: a CSS animation would override the SMIL opacity
        out.append(f'<g class="cur"><rect x="{tx + (n * cw if i == 0 else 0):.1f}" y="{y - size + 2}" width="{cw * 0.62:.1f}" '
                   f'height="{size + 2}" fill="{CYAN}" opacity="{1 if i == 0 else 0}">'
                   f'<animate attributeName="x" values="{xv}" {anim}/>'
                   f'<animate attributeName="opacity" values="{vis}" {anim}/></rect></g>')
    return "\n".join(out)


# ─────────────────────────── SECTION HEADERS ─────────────────────────────

def build_section(key):
    """Transparent header whose colours read well on GitHub light *and* dark."""
    num, title, sub = SECTIONS[key]
    W, H = 1000, 84
    tx = 74
    end = tx + tw(title, "sg7", 30) + 22
    body = f'''<defs><linearGradient id="t" x1="{tx}" x2="{end}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#0891b2"/><stop offset="1" stop-color="#8b5cf6"/></linearGradient>
<linearGradient id="ln" x1="{end}" x2="{W}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#0ea5e9"/><stop offset=".55" stop-color="#8b5cf6" stop-opacity=".55"/><stop offset="1" stop-color="#8b5cf6" stop-opacity="0"/></linearGradient></defs>
<text x="2" y="56" class="jb7" font-size="38" fill="none" stroke="url(#t)" stroke-width="1.3">{num}</text>
{text(tx, 48, title, "sg7", 30, "url(#t)")}
{text(tx + 1, 72, sub, "jb4", 14, "#6e7781")}
<path d="M{end:.0f} 38H{W}" stroke="url(#ln)" stroke-width="1.5"/>
<circle class="dot" cx="{end:.0f}" cy="38" r="3.5" fill="#0ea5e9"/>
<circle cx="{end:.0f}" cy="38" r="3" fill="#0ea5e9"/>'''
    css = f"""
@keyframes run{{0%{{transform:translateX(0);opacity:0}}10%{{opacity:1}}85%{{opacity:1}}100%{{transform:translateX({W - end - 40:.0f}px);opacity:0}}}}
.dot{{animation:run 4.5s cubic-bezier(.6,0,.4,1) infinite}}
"""
    write_svg(f"section-{key}.svg", W, H, body, css, f"{num} · {title}")


# ──────────────────────────────── ABOUT ──────────────────────────────────

PY_TOKEN = re.compile(r'(?P<com>#.*$)|(?P<doc>""".*?""")|(?P<str>"[^"]*")|(?P<num>\b\d[\d,]*\b)'
                      r'|(?P<word>[A-Za-z_]\w*)|(?P<op>->|[^\w\s])|(?P<ws>\s+)')
SYNTAX = {"com": ("#5c7090", True), "doc": ("#6f86a8", True), "str": ("#c3e88d", False), "num": ("#f78c6c", False),
          "kw": ("#c792ea", False), "self": ("#f07178", True), "cls": ("#ffcb6b", False), "fn": ("#82aaff", False),
          "attr": ("#7fdbff", False), "var": ("#e2e8f0", False), "op": ("#89ddff", False)}


def highlight(line):
    toks, prev = [], ""
    for m in PY_TOKEN.finditer(line):
        kind, t = m.lastgroup, m.group()
        if kind == "word":
            if t == "self":
                kind = "self"
            elif t in {"class", "def", "return", "import", "from"}:
                kind = "kw"
            elif prev == "def":
                kind = "fn"
            elif prev == ".":
                kind = "attr"
            elif t[0].isupper() or t in {"str", "int", "list", "dict"}:
                kind = "cls"
            else:
                kind = "var"
        toks.append((kind, t))
        if kind != "ws":
            prev = t
    return toks


def build_about():
    lines = ABOUT_CODE.split("\n")
    W, size, lh = 1000, 15, 25
    cw = tw("M", "jb4", size)
    top, gutter_x, code_x = 66, 52, 72
    H = top + len(lines) * lh + 18 + 30
    b = [panel(W, H, 16)]
    # title bar
    b.append(f'<path d="M1.5 44V17A15.5 15.5 0 0 1 17 1.5H{W - 17}A15.5 15.5 0 0 1 {W - 1.5} 17V44Z" fill="#081120"/>'
             f'<path d="M1.5 44H{W - 1.5}" stroke="{LINE}"/>')
    for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        b.append(f'<circle cx="{26 + i * 20}" cy="23" r="6" fill="{c}"/>')
    b.append(f'<path d="M100 44V16a6 6 0 0 1 6-6h150a6 6 0 0 1 6 6V44Z" fill="{BG1}"/><path d="M106 10h150" stroke="{CYAN}" stroke-width="2"/>')
    b.append(icon("python", 114, 19, 14))
    b.append(text(136, 31, "himanshu.py", "jb4", 13.5, TEXT))
    b.append(text(W - 24, 31, "~/ItzHimanshu007", "jb4", 13, DIM, "end"))

    t, starts = 0.5, []
    for i, line in enumerate(lines):
        y = top + i * lh + 17
        starts.append(t)
        b.append(text(gutter_x, y, str(i + 1), "jb4", 13, "#334760", "end"))
        if not line.strip():
            t += 0.08
            continue
        dur = max(0.15, len(line.strip()) * 0.008)
        w = len(line) * cw + 4
        b.append(f'<clipPath id="c{i}"><rect x="{code_x - 2}" y="{y - 17}" width="{w:.0f}" height="{lh}">'
                 f'<animate attributeName="width" values="0;0;{w:.0f}" keyTimes="0;{t / (t + dur):.4f};1" '
                 f'dur="{t + dur:.2f}s" fill="freeze"/></rect></clipPath>')
        spans = []
        for kind, tok in highlight(line):
            if kind == "ws":
                spans.append(esc(tok))
                continue
            col, ital = SYNTAX[kind]
            cls = ' class="jbi"' if ital else ""
            spans.append(f'<tspan fill="{col}"{cls}>{esc(tok)}</tspan>')
        b.append(f'<text x="{code_x}" y="{y}" class="jb4" font-size="{size}" clip-path="url(#c{i})" '
                 f'xml:space="preserve" style="white-space:pre">{"".join(spans)}</text>')
        t += dur + 0.06
    done = t
    # active-line highlight follows the typing, then rests on the last line
    ys = ";".join(f"{top + i * lh}" for i in range(len(lines)))
    kts = ";".join(["0"] + [f"{s / done:.4f}" for s in starts[1:]])
    b.insert(1, f'<rect x="1.5" y="{top + (len(lines) - 1) * lh}" width="{W - 3}" height="{lh}" fill="{CYAN}" fill-opacity=".05">'
                f'<animate attributeName="y" values="{ys}" keyTimes="{kts}" dur="{done:.2f}s" calcMode="discrete" fill="freeze"/></rect>')
    last_y = top + (len(lines) - 1) * lh
    b.append(f'<g class="cur"><rect x="{code_x + len(lines[-1]) * cw + 3:.1f}" y="{last_y + 4}" width="{cw * 0.6:.1f}" '
             f'height="18" fill="{CYAN}" opacity="0"><set attributeName="opacity" to="1" begin="{done:.2f}s"/></rect></g>')
    # status bar
    sy = H - 30
    b.append(f'<path d="M1.5 {sy}H{W - 1.5}V{H - 17}A15.5 15.5 0 0 1 {W - 17} {H - 1.5}H17A15.5 15.5 0 0 1 1.5 {H - 17}Z" fill="#081120"/>'
             f'<path d="M1.5 {sy}H{W - 1.5}" stroke="{LINE}"/>')
    b.append(f'<circle cx="24" cy="{sy + 15}" r="4" fill="{GREEN}"/>')
    b.append(text(36, sy + 19.5, "main   Python   UTF-8", "jb4", 12, MUTED, extra='xml:space="preserve" style="white-space:pre"'))
    b.append(text(W - 22, sy + 19.5, f"Ln {len(lines)}, Col 1   0 problems   100% shipped", "jb4", 12, MUTED, "end",
                  extra='xml:space="preserve" style="white-space:pre"'))
    write_svg("about.svg", W, H, "\n".join(b), ".cur{animation:blink 1s step-end infinite}",
              "himanshu.py — AI Engineer & Founder profile as code")


# ──────────────────────────────── STACK ──────────────────────────────────

def chip(item, x, y, h=34):
    """Brand chip: icon + label. Returns (svg, width)."""
    if ":" in item or item in ICONS:
        key, _, label = item.partition(":")
        ic = ICONS[key]
        label = label or ic["title"]
        col = readable(ic["hex"])
        w = 40 + tw(label, "sg5", 15) + 14
        svg = (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{h}" rx="9" fill="{CARD2}" stroke="{col}" stroke-opacity=".38"/>'
               + icon(key, x + 12, y + 8, 18, col) + text(x + 40, y + 22.5, label, "sg5", 15, "#dbe4f0"))
    else:
        label = item
        w = 40 + tw(label, "sg5", 15) + 14
        svg = (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{h}" rx="9" fill="{CARD2}" stroke="{CYAN}" stroke-opacity=".38"/>'
               + f'<g stroke="{CYAN}" stroke-width="1.6"><ellipse cx="{x + 21}" cy="{y + 11}" rx="7.5" ry="3"/>'
               f'<path d="M{x + 13.5} {y + 11}v12c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3V{y + 11}M{x + 13.5} {y + 17}c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3"/></g>'
               + text(x + 40, y + 22.5, label, "sg5", 15, "#dbe4f0"))
    return svg, round(w)


def flow(items, x0, y0, width, gap=8, h=34, make=chip):
    """Lay chips out left-to-right, wrapping. Returns (svgs, height)."""
    out, x, y = [], x0, y0
    for it in items:
        svg, w = make(it, 0, 0, h)
        if x + w > x0 + width and x > x0:
            x, y = x0, y + h + gap
        out.append((it, x, y))
        x += w + gap
    return [make(it, x, y, h)[0] for it, x, y in out], y + h - y0


def build_stack():
    W, pad, gap, cols = 1000, 22, 14, 2
    cwid = (W - 2 * pad - gap) / cols
    cards = [(f"{i + 1:02d}", t, d, items, False) for i, (t, d, items) in enumerate(STACK)]
    cards.append(("++", "Levelling up", "what I'm going deeper on right now", LEVELLING_UP, True))
    built = []
    for num, title, desc, items, learning in cards:
        if learning:
            chips, ch = flow(items, 0, 0, cwid - 40, make=learn_chip)
        else:
            chips, ch = flow(items, 0, 0, cwid - 40)
        built.append((num, title, desc, chips, ch, learning))
    b, y, k = [], pad, 0
    rows = [built[i:i + cols] for i in range(0, len(built), cols)]
    body = []
    for row in rows:
        rh = max(78 + c[4] + 20 for c in row)
        for ci, (num, title, desc, chips, ch, learning) in enumerate(row):
            x = pad + ci * (cwid + gap)
            stroke = f'stroke="{VIOLET}" stroke-opacity=".55" stroke-dasharray="5 5"' if learning else f'stroke="{LINE}"'
            body.append(f'<g class="rise" style="animation-delay:{k * .1:.1f}s">'
                        f'<rect x="{x:.0f}" y="{y}" width="{cwid:.0f}" height="{rh}" rx="14" fill="{CARD}" {stroke}/>'
                        + text(x + 20, y + 34, num, "jb7", 13, VIOLET if learning else CYAN)
                        + text(x + 48, y + 35, title, "sg7", 19, TEXT)
                        + text(x + 20, y + 58, desc, "sg5", 14, MUTED)
                        + f'<g transform="translate({x + 20:.0f} {y + 74})">{"".join(chips)}</g></g>')
            k += 1
        y += rh + gap
    H = y - gap + pad
    b.append(panel(W, H))
    b.extend(body)
    css = """
@keyframes load{from{transform:translateX(-100%)}to{transform:translateX(100%)}}
.load{animation:load 2.4s ease-in-out infinite}
"""
    write_svg("stack.svg", W, H, "\n".join(b), css, "Tech stack: " + ", ".join(t for t, _, _ in STACK))


def learn_chip(label, x, y, h=34):
    w = 34 + tw(label, "sg5", 15) + 14
    cid = re.sub(r"\W", "", label)
    return (f'<clipPath id="lc{cid}"><rect x="{x}" y="{y}" width="{w:.0f}" height="{h}" rx="9"/></clipPath>'
            f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{h}" rx="9" fill="{VIOLET}" fill-opacity=".1" stroke="{VIOLET}" stroke-opacity=".5"/>'
            f'<g clip-path="url(#lc{cid})"><rect class="load" x="{x}" y="{y + h - 3}" width="{w:.0f}" height="3" fill="{VIOLET}" '
            f'style="animation-delay:-{(len(label) % 5) * .4:.1f}s"/></g>'
            f'<path d="M{x + 13} {y + 12}l6 5-6 5" stroke="#c4b5fd" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            + text(x + 30, y + 22.5, label, "sg5", 15, "#ddd6fe")), round(w)


# ─────────────────────────────── TROPHIES ────────────────────────────────

def medal(cx, cy, place, r=20):
    hi, mid, lo, _ = MEDALS[place]
    gid = f"m{place}"
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r - 4}" stroke="{lo}" stroke-opacity=".55" stroke-width="1.2"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#sh{place})"/>'
            + text(cx, cy + 6.5, str(place), "sg7", r * 0.95, lo, "middle"))


def medal_defs():
    out = []
    for p, (hi, mid, lo, _) in MEDALS.items():
        out.append(f'<linearGradient id="m{p}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{hi}"/>'
                   f'<stop offset=".55" stop-color="{mid}"/><stop offset="1" stop-color="{lo}"/></linearGradient>'
                   f'<linearGradient id="sh{p}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                   f'<stop offset=".45" stop-color="#fff" stop-opacity="0"><animate attributeName="offset" values="-.3;-.3;1.1" keyTimes="0;.7;1" dur="5s" begin="{p * .6}s" repeatCount="indefinite"/></stop>'
                   f'<stop offset=".5" stop-color="#fff" stop-opacity=".75"><animate attributeName="offset" values="-.25;-.25;1.15" keyTimes="0;.7;1" dur="5s" begin="{p * .6}s" repeatCount="indefinite"/></stop>'
                   f'<stop offset=".55" stop-color="#fff" stop-opacity="0"><animate attributeName="offset" values="-.2;-.2;1.2" keyTimes="0;.7;1" dur="5s" begin="{p * .6}s" repeatCount="indefinite"/></stop>'
                   f'</linearGradient>')
    return "".join(out)


def build_trophies():
    W, pad, gap = 1000, 22, 12
    counts = {p: sum(1 for h in HACKATHONS if h[0] == p) for p in MEDALS}
    b = []
    body = [f"<defs>{medal_defs()}"
            f'<linearGradient id="hot" x1="0" x2="1"><stop offset="0" stop-color="#fbbf24"/><stop offset="1" stop-color="#f43f5e"/></linearGradient>'
            f'<linearGradient id="funnel" x1="0" x2="1"><stop offset="0" stop-color="#334760" stop-opacity=".9"/><stop offset="1" stop-color="#fbbf24"/></linearGradient>'
            f'<linearGradient id="hotbg" x1="0" x2="1"><stop offset="0" stop-color="#f59e0b" stop-opacity=".14"/><stop offset="1" stop-color="#f43f5e" stop-opacity=".04"/></linearGradient>'
            f"</defs>"]
    # counters
    y = pad
    cw = (W - 2 * pad - 3 * gap) / 4
    counters = [(None, str(len(HACKATHONS)), "podium finishes")] + [(p, str(counts[p]), MEDALS[p][3]) for p in MEDALS]
    for i, (p, n, lab) in enumerate(counters):
        x = pad + i * (cw + gap)
        inner = (f'<rect x="{x:.0f}" y="{y}" width="{cw:.0f}" height="76" rx="14" fill="{CARD}" stroke="{LINE}"/>')
        if p is None:
            inner += (f'<path d="M{x + 30:.0f} {y + 24}h24v10a12 12 0 0 1-24 0Z M{x + 30:.0f} {y + 28}h-6a6 6 0 0 0 6 8 M{x + 54:.0f} {y + 28}h6a6 6 0 0 1-6 8 '
                      f'M{x + 42:.0f} {y + 46}v6 M{x + 35:.0f} {y + 54}h14" stroke="{CYAN}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>')
        else:
            inner += medal(x + 42, y + 38, p, 17)
        inner += text(x + 76, y + 44, n, "sg7", 32, TEXT) + text(x + 76 + tw(n, "sg7", 32) + 10, y + 43, lab, "sg5", 14.5, MUTED)
        body.append(f'<g class="rise" style="animation-delay:{i * .08:.2f}s">{inner}</g>')
    y += 76 + 18
    # entries, two columns
    ew, eh = (W - 2 * pad - gap) / 2, 70
    for i, (p, name, org, tier) in enumerate(HACKATHONS):
        col, row = i % 2, i // 2
        x, yy = pad + col * (ew + gap), y + row * (eh + 10)
        tc = TIERS[tier]
        name_size = 17 if tw(name, "sg7", 17) < ew - 90 else 16
        ow = tw(org, "sg5", 13.5)
        pw = tw(tier, "jb7", 10.5, 1.2) + 16
        body.append(f'<g class="rise" style="animation-delay:{.3 + i * .07:.2f}s">'
                    f'<rect x="{x:.0f}" y="{yy}" width="{ew:.0f}" height="{eh}" rx="14" fill="{CARD}" stroke="{LINE}"/>'
                    f'<rect x="{x:.0f}" y="{yy + 18}" width="3" height="{eh - 36}" rx="1.5" fill="{MEDALS[p][1]}"/>'
                    + medal(x + 42, yy + eh / 2, p)
                    + text(x + 76, yy + 30, name, "sg7", name_size, "#f1f5f9")
                    + text(x + 76, yy + 52, org, "sg5", 13.5, MUTED)
                    + f'<rect x="{x + 76 + ow + 10:.0f}" y="{yy + 40}" width="{pw:.0f}" height="17" rx="8.5" fill="{tc}" fill-opacity=".12" stroke="{tc}" stroke-opacity=".45"/>'
                    + text(x + 76 + ow + 10 + pw / 2, yy + 52.5, tier, "jb7", 10.5, tc, "middle", 'letter-spacing="1.2"')
                    + "</g>")
    rows = (len(HACKATHONS) + 1) // 2
    y += rows * (eh + 10) + 8
    # spotlight
    s = SPOTLIGHT
    pct = s["rank"] / s["field"] * 100
    sh = 96
    sx = pad
    sw = W - 2 * pad
    big = f"Top {s['rank']}"
    bw = tw(big, "sg7", 44)
    body.append(f'<g class="rise" style="animation-delay:.9s">'
                f'<rect x="{sx}" y="{y}" width="{sw}" height="{sh}" rx="16" fill="url(#hotbg)" stroke="url(#hot)" stroke-opacity=".7"/>'
                f'<rect class="breathe" x="{sx}" y="{y}" width="{sw}" height="{sh}" rx="16" stroke="url(#hot)" stroke-width="2"/>'
                + text(sx + 28, y + 61, big, "sg7", 44, "url(#hot)")
                + text(sx + 28 + bw + 12, y + 47, f"out of {s['field']:,}", "sg7", 18, "#fde68a")
                + text(sx + 28 + bw + 12, y + 69, f"top {pct:.2f}%", "jb4", 13, "#fca5a5")
                + text(sx + 330, y + 42, s["event"], "sg7", 22, TEXT)
                + text(sx + 330, y + 67, s["venue"], "sg5", 14.5, MUTED))
    # funnel: the whole field narrowing down to the final ten
    fx, fy, fw, fh = sx + sw - 270, y + 22, 210, 52
    mid = fy + fh / 2
    body.append(f'<path d="M{fx} {fy}C{fx + fw * .55} {fy} {fx + fw * .6} {mid - 4} {fx + fw} {mid - 3}V{mid + 3}'
                f'C{fx + fw * .6} {mid + 4} {fx + fw * .55} {fy + fh} {fx} {fy + fh}Z" fill="url(#funnel)"/>'
                f'<circle class="star" cx="{fx + fw + 9}" cy="{mid}" r="9" fill="#fbbf24" fill-opacity=".3"/>'
                f'<circle cx="{fx + fw + 9}" cy="{mid}" r="4.5" fill="#fbbf24"/>'
                + text(fx + 10, mid + 4.5, f"{s['field']:,}", "jb7", 13, "#cbd5e1")
                + text(fx + fw + 24, mid + 5, str(s["rank"]), "jb7", 14, "#fde68a") + "</g>")
    y += sh + pad
    H = y
    b.append(panel(W, H))
    b.extend(body)
    css = """
@keyframes breathe{0%,100%{opacity:.15}50%{opacity:.85}}
.breathe{animation:breathe 3.2s ease-in-out infinite}
@keyframes star{0%,100%{opacity:1}50%{opacity:.35}}
.star{animation:star 1.6s ease-in-out infinite}
"""
    alt = "; ".join(f"{['', '1st', '2nd', '3rd'][p]} {n} ({o})" for p, n, o, _ in HACKATHONS)
    write_svg("trophies.svg", W, H, "\n".join(b), css, f"Hackathon record: {alt}; Top {s['rank']} of {s['field']:,} at {s['event']}")


# ─────────────────────────────── PLAYBOOK ────────────────────────────────

def wrap(s, cls, size, width):
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if tw(trial, cls, size) > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def build_playbook():
    W, n = 1000, len(PLAYBOOK)
    step = (W - 80) / n
    xs = [40 + step * i + step / 2 for i in range(n)]
    cy = 70
    b = []
    body = [f'<defs><linearGradient id="rail" x1="{xs[0]}" x2="{xs[-1]}" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>'
            f'<radialGradient id="orb"><stop offset="0" stop-color="#fff"/><stop offset=".35" stop-color="{CYAN}"/>'
            f'<stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient></defs>']
    body.append(f'<path d="M{xs[0]} {cy}H{xs[-1]}" stroke="url(#rail)" stroke-opacity=".35" stroke-width="2"/>')
    body.append(f'<path class="rail" d="M{xs[0]} {cy}H{xs[-1]}" stroke="url(#rail)" stroke-width="2"/>')
    cycle = 7.5
    body.append(f'<circle r="9" fill="url(#orb)"><animateMotion path="M{xs[0]} {cy}H{xs[-1]}" dur="{cycle}s" '
                f'keyPoints="0;1;1" keyTimes="0;.8;1" calcMode="linear" repeatCount="indefinite"/></circle>')
    max_lines = 0
    for i, ((title, desc), x) in enumerate(zip(PLAYBOOK, xs)):
        col = CYAN if i < n - 1 else VIOLET
        lit = (i / (n - 1)) * 0.8 * cycle
        body.append(f'<circle cx="{x:.0f}" cy="{cy}" r="30" fill="{BG1}" stroke="{col}" stroke-opacity=".35" stroke-width="1.5"/>'
                    f'<circle class="lit" cx="{x:.0f}" cy="{cy}" r="30" fill="{col}" fill-opacity=".14" stroke="{col}" stroke-width="2" '
                    f'style="animation-delay:{lit - cycle:.2f}s"/>'
                    + text(x, cy + 7, f"{i + 1:02d}", "jb7", 19, col, "middle"))
        body.append(text(x, cy + 64, title, "sg7", 18, TEXT, "middle"))
        lines = wrap(desc, "sg5", 14, step - 30)
        max_lines = max(max_lines, len(lines))
        for j, ln in enumerate(lines):
            body.append(text(x, cy + 90 + j * 20, ln, "sg5", 14, MUTED, "middle"))
    y = cy + 90 + max_lines * 20 + 14
    body.append(f'<path d="M30 {y}H{W - 30}" stroke="{LINE}" stroke-dasharray="3 5"/>')
    y += 22
    label = "BEYOND THE CODE"
    lw = tw(label, "jb7", 12, 2)
    widths = [tw(t, "sg5", 14.5) + 28 for t in BEYOND]
    total = lw + 18 + sum(widths) + 10 * (len(widths) - 1)
    x = (W - total) / 2
    body.append(text(x, y + 21, label, "jb7", 12, CYAN, extra='letter-spacing="2"'))
    x += lw + 18
    for t, w in zip(BEYOND, widths):
        body.append(f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="31" rx="15.5" fill="{CARD2}" stroke="{LINE}"/>'
                    + text(x + w / 2, y + 20.5, t, "sg5", 14.5, "#dbe4f0", "middle"))
        x += w + 10
    H = y + 31 + 24
    b.append(panel(W, H))
    b.extend(body)
    css = f"""
@keyframes lit{{0%,6%{{opacity:1}}24%,100%{{opacity:0}}}}
.lit{{animation:lit {cycle}s linear infinite}}
@keyframes dash{{to{{stroke-dashoffset:-40}}}}
.rail{{stroke-dasharray:4 16;animation:dash 1.2s linear infinite}}
"""
    write_svg("playbook.svg", W, H, "\n".join(b), css, "How I build: " + " → ".join(t for t, _ in PLAYBOOK))


# ──────────────────────────── FOOTER & BUTTONS ───────────────────────────

def build_footer():
    W, H = 1000, 230
    tw_title = tw(FOOTER_TITLE, "sg7", 36)
    b = [f'''<defs><clipPath id="fc"><rect width="{W}" height="{H}" rx="20"/></clipPath>
<linearGradient id="ft" x1="{(W - tw_title) / 2:.0f}" x2="{(W + tw_title) / 2:.0f}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#fff"/><stop offset=".5" stop-color="#a5f3fc"/><stop offset="1" stop-color="#c4b5fd"/></linearGradient>
<linearGradient id="w1" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity=".2"/><stop offset="1" stop-color="{VIOLET}" stop-opacity=".22"/></linearGradient>
<linearGradient id="w2" x1="0" x2="1"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".16"/><stop offset="1" stop-color="{CYAN}" stop-opacity=".12"/></linearGradient>
<linearGradient id="w3" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset=".5" stop-color="{CYAN}" stop-opacity=".8"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></linearGradient></defs>''',
         panel(W, H, 20, "fstroke"),
         '<g clip-path="url(#fc)">']
    for gid, amp, base, dur, line in (("w2", 14, 186, 9, False), ("w1", 10, 198, 6, False), ("w3", 8, 190, 7, True)):
        def wave(ph):
            pts = " ".join(f"{x},{base + amp * math.sin((x / W) * 6.283 * 1.5 + ph):.1f}" for x in range(0, W + 1, 25))
            return f"M0,{pts.split(' ', 1)[0].split(',')[1]} L{pts}" if line else f"M0,{H} L{pts} L{W},{H} Z"
        paint = f'stroke="url(#{gid})" stroke-width="1.5"' if line else f'fill="url(#{gid})"'
        b.append(f'<path d="{wave(0)}" {paint}><animate attributeName="d" dur="{dur}s" repeatCount="indefinite" '
                 f'values="{wave(0)};{wave(3.14)};{wave(0)}"/></path>')
    b.append("</g>")
    b.append(text(W / 2, 84, FOOTER_TITLE, "sg7 rise", 36, "url(#ft)", "middle"))
    b.append(text(W / 2, 118, FOOTER_SUB, "sg5 rise", 16, MUTED, "middle", 'style="animation-delay:.15s"'))
    b.append(f'<text x="{W / 2}" y="152" class="jb4 rise" font-size="15" fill="{CYAN}" text-anchor="middle" style="animation-delay:.3s">'
             f'<tspan fill="{DIM}">&gt; </tspan>{esc(EMAIL)}</text>')
    write_svg("footer.svg", W, H, "\n".join(b), "", FOOTER_TITLE)


def build_button(name, label, glyph, accent):
    h = 46
    w = 58 + tw(label, "sg7", 16) + 22
    body = (f'<defs><linearGradient id="bs" x1="0" x2="1"><stop offset="0" stop-color="{accent}"/>'
            f'<stop offset="1" stop-color="{VIOLET}"/></linearGradient></defs>'
            f'<rect x="1" y="1" width="{w - 2:.0f}" height="{h - 2}" rx="{(h - 2) / 2}" fill="{BG1}" stroke="url(#bs)" stroke-width="1.5"/>'
            f'<rect class="glow" x="1" y="1" width="{w - 2:.0f}" height="{h - 2}" rx="{(h - 2) / 2}" fill="url(#bs)"/>'
            f'{glyph}' + text(50, 29, label, "sg7", 16, TEXT))
    write_svg(name, round(w), h, body, "@keyframes g{0%,100%{opacity:.05}50%{opacity:.16}}.glow{animation:g 3s ease-in-out infinite}", label)


def build_buttons():
    linkedin = ('<rect x="18" y="12" width="22" height="22" rx="5" fill="#0a66c2"/>'
                '<path d="M23 20.5v8M23 16.6v.1M27 28.5v-5a3 3 0 0 1 6 0v5M27 20.5v8" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>')
    mail = icon("gmail", 17, 11, 24)
    build_button("btn-linkedin.svg", "Connect on LinkedIn", linkedin, "#0a66c2")
    build_button("btn-email.svg", EMAIL, mail, "#ea4335")


def sync_readme_table():
    """Keep the plain-text hackathon table in README.md in step with HACKATHONS."""
    readme = HERE.parent / "README.md"
    start, end = "<!-- hackathons:start -->", "<!-- hackathons:end -->"
    src = readme.read_text()
    if start not in src:
        return
    medal_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}
    rows = ["| | Competition | Organiser | Level |", "|:-:|:--|:--|:-:|"]
    rows += [f"| {medal_emoji[p]} | **{n}** | {o} | {t.title()} |" for p, n, o, t in HACKATHONS]
    s = SPOTLIGHT
    rows.append(f"| 🏁 | **{s['event']}** | {s['venue']} | Top {s['rank']} of {s['field']:,} |")
    before, rest = src.split(start, 1)
    after = rest.split(end, 1)[1]
    readme.write_text(f"{before}{start}\n\n" + "\n".join(rows) + f"\n\n{end}{after}")
    print("  README.md hackathon table synced")


def main():
    ASSETS.mkdir(exist_ok=True)
    print("building assets/")
    build_hero()
    for key in SECTIONS:
        build_section(key)
    build_about()
    build_stack()
    build_trophies()
    build_playbook()
    build_footer()
    build_buttons()
    sync_readme_table()


if __name__ == "__main__":
    main()
