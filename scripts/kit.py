# SVG toolkit for the profile cards: fonts (measured + subset + embedded), themes, and drawing helpers.
# Every card is a self-contained SVG: GitHub shows README images through a proxy that blocks external fonts,
# so each file carries only the glyphs it uses, as base64 woff2.
import base64, io, os
from html import escape
from fontTools.ttLib import TTFont
from fontTools import subset as ft_subset

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")

# family alias -> file
FONTS = {
    "D8": "Bricolage-800.woff2",      # display, heavy
    "D6": "Bricolage-600.woff2",      # display, body
    "M4": "JetBrainsMono-400.woff2",  # mono
    "M7": "JetBrainsMono-700.woff2",  # mono, bold
}

_loaded = {}


def _font(alias):
    if alias not in _loaded:
        f = TTFont(os.path.join(FONT_DIR, FONTS[alias]))
        _loaded[alias] = (f, f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)
    return _loaded[alias]


def measure(text, alias, size):
    """Advance width of text in px (no kerning; close enough for layout)."""
    _, cmap, hmtx, upm = _font(alias)
    w = 0
    for ch in text:
        g = cmap.get(ord(ch)) or cmap.get(ord("?"))
        w += hmtx[g][0]
    return w * size / upm


def fit(text, alias, size, max_w):
    """Trim text with an ellipsis so it fits max_w."""
    if measure(text, alias, size) <= max_w:
        return text
    while text and measure(text + "…", alias, size) > max_w:
        text = text[:-1]
    return text.rstrip() + "…"


def wrap(text, alias, size, max_w, max_lines=99):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if measure(t, alias, size) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = fit(lines[-1] + " …", alias, size, max_w)
    return lines


def _subset_b64(alias, chars):
    f = TTFont(os.path.join(FONT_DIR, FONTS[alias]))
    opts = ft_subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga"]
    opts.name_IDs = []
    opts.notdef_outline = True
    s = ft_subset.Subsetter(opts)
    s.populate(text="".join(sorted(chars)) + " ")
    s.subset(f)
    buf = io.BytesIO()
    f.flavor = "woff2"
    f.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


# ------------------------------------------------------------------ themes
THEMES = {
    "light": {
        "name": "light",
        "bg": "#f3f0fb", "panel": "#ebe6f8", "card": "#ffffff", "text": "#16132b", "muted": "#5b5677",
        "line": "#16132b", "grid": "#d9d2ef",
        "violet": "#e3d9ff", "lime": "#e4f8b4", "cyan": "#cbf1f8", "coral": "#ffd8d2", "amber": "#ffe7ad", "blue": "#d6e4ff",
        "pop": "#7c3aed", "on_pop": "#ffffff", "hl": "#c6f432", "on_hl": "#16132b", "go": "#4d7c0f",
        "screen": "#14122b", "on_screen": "#ecebff", "on_screen_muted": "#a9a5cf", "prompt": "#c6f432",
        "heat": ["#e6e1f3", "#d4f58e", "#a3e635", "#65a30d", "#3f6212"],
        "chart": "#7c3aed", "chart_fill": "#7c3aed",
    },
    "dark": {
        "name": "dark",
        "bg": "#0c0e1b", "panel": "#12152a", "card": "#181c34", "text": "#f2f0ff", "muted": "#aaa7cb",
        "line": "#02030a", "grid": "#1d2140",
        "violet": "#3a2a78", "lime": "#334a0f", "cyan": "#0f4652", "coral": "#6a2530", "amber": "#5c420e", "blue": "#1d3768",
        "pop": "#a78bfa", "on_pop": "#0c0e1b", "hl": "#c6f432", "on_hl": "#0c0e1b", "go": "#c6f432",
        "screen": "#090a14", "on_screen": "#ecebff", "on_screen_muted": "#9794bf", "prompt": "#c6f432",
        "heat": ["#1f2340", "#36500f", "#5a8a17", "#8fd32a", "#c6f432"],
        "chart": "#c6f432", "chart_fill": "#c6f432",
    },
}


# ------------------------------------------------------------------ document
class Doc:
    """Collects SVG elements and the characters drawn in each font, then emits a standalone SVG."""

    def __init__(self, w, h, theme, title=""):
        self.w, self.h, self.t, self.title = w, h, theme, title
        self.parts, self.defs, self.chars = [], [], {k: set() for k in FONTS}

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, font="D6", size=16, fill=None, anchor="start", extra=""):
        s = str(s)
        missing = [c for c in s if ord(c) not in _font(font)[1] and c != " "]
        if missing:
            raise ValueError(f"font {font} has no glyph for {missing!r} in {s!r}")
        self.chars[font].update(s)
        fill = fill or self.t["text"]
        a = "" if anchor == "start" else f' text-anchor="{anchor}"'
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" class="{font}" font-size="{size}" fill="{fill}"{a}{extra}>{escape(s)}</text>')

    def render(self):
        faces = []
        for alias, chars in self.chars.items():
            if chars:
                faces.append(f"@font-face{{font-family:{alias};src:url(data:font/woff2;base64,{_subset_b64(alias, chars)}) format('woff2')}}"
                             f".{alias}{{font-family:{alias},ui-monospace,sans-serif}}")
        style = "<style>" + "".join(faces) + "text{white-space:pre}</style>"
        title = f"<title>{escape(self.title)}</title>" if self.title else ""
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img">'
                f"{title}{style}{defs}{''.join(self.parts)}</svg>")


# ------------------------------------------------------------------ shapes
def panel(d, x=0, y=0, w=None, h=None, r=22):
    """The outer frame every card sits in, so it reads well on GitHub's own light or dark page."""
    w, h = w or d.w, h or d.h
    d.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{d.t["panel"]}"/>')


def sticker(d, x, y, w, h, fill, r=14, sh=5, sw=2.5):
    """Card with a hard offset shadow and an ink border: the core look."""
    t = d.t
    d.add(f'<rect x="{x + sh}" y="{y + sh}" width="{w}" height="{h}" rx="{r}" fill="{t["line"]}"/>')
    d.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{t["line"]}" stroke-width="{sw}"/>')


def chip(d, x, y, label, fill, font="M7", size=12, color=None, pad=9, h=24, sh=2.5):
    """A small rounded label. Returns its width so callers can lay chips out in a row."""
    w = measure(label, font, size) + pad * 2
    t = d.t
    d.add(f'<rect x="{x + sh:.1f}" y="{y + sh:.1f}" width="{w:.1f}" height="{h}" rx="7" fill="{t["line"]}"/>')
    d.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="7" fill="{fill}" stroke="{t["line"]}" stroke-width="2"/>')
    d.text(x + pad, y + h / 2 + size * 0.36, label, font, size, color or t["text"])
    return w


def chips(d, x, y, labels, max_w, gap=8, row_h=34, **kw):
    """Lay chips left to right, wrapping. labels: [(text, fill)]. Returns the y below the last row."""
    cx, cy = x, y
    for label, fill in labels:
        w = measure(label, kw.get("font", "M7"), kw.get("size", 12)) + kw.get("pad", 9) * 2
        if cx > x and cx + w > x + max_w:
            cx, cy = x, cy + row_h
        cx += chip(d, cx, cy, label, fill, **kw) + gap
    return cy + kw.get("h", 24)


def dot_grid(d, x, y, w, h, step=22, r=1.2):
    pid = f"dots{len(d.defs)}"
    d.defs.append(f'<pattern id="{pid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
                  f'<circle cx="{step / 2}" cy="{step / 2}" r="{r}" fill="{d.t["grid"]}"/></pattern>')
    d.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{pid})"/>')


def fmt(n):
    return f"{n:,}"
