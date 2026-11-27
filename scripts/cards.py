# Every card on the profile. Each function takes (theme, data, phone) and returns SVG text.
# Desktop cards are drawn 1000 wide; phone cards 600 wide so the text stays readable on a narrow screen.
from datetime import date, timedelta
from kit import Doc, panel, sticker, chip, chips, dot_grid, measure, fit, wrap, fmt

DESK, PHONE = 1000, 600

# ------------------------------------------------------------------ icons (24-unit box, stroked)
ICONS = {
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2.5"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "flame": '<path d="M12 3c1 4 6 6 6 11a6 6 0 0 1-12 0c0-3 2-4.5 3-6.5 1 2 2 3 3 3 0-3-1-5 0-7.5z"/>',
    "trophy": '<path d="M8 4h8v5a4 4 0 0 1-8 0zM8 6H5a3 3 0 0 0 3.5 4M16 6h3a3 3 0 0 1-3.5 4M12 13v4M8.5 20.5h7M10 17h4v3.5h-4z"/>',
    "sigma": '<path d="M17 5H7l6 7-6 7h10"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "star": '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
    "linkedin": '<rect x="3" y="3" width="18" height="18" rx="3.5"/><path d="M8 10.5V17M8 7.2v.1M12 17v-6.5M12 13.5a3 3 0 0 1 6 0V17"/>',
    "mail": '<rect x="3" y="5.5" width="18" height="13" rx="2.5"/><path d="M3.5 7.5l8.5 6 8.5-6"/>',
    "doc": '<path d="M6 3h8l4 4v14H6zM14 3v4h4M9 12h6M9 16h6"/>',
    "house": '<path d="M3 11l9-7 9 7M5.5 9.5V20h13V9.5M10 20v-6h4v6"/>',
    "nodes": '<circle cx="6" cy="6" r="2.6"/><circle cx="18" cy="6" r="2.6"/><circle cx="12" cy="18" r="2.6"/><path d="M8.6 6h6.8M7.3 8.3l3.4 7.4M16.7 8.3l-3.4 7.4"/>',
    "store": '<path d="M4 9l1.5-5h13L20 9M4 9h16v1.5a2.7 2.7 0 0 1-5.3 0 2.7 2.7 0 0 1-5.4 0 2.7 2.7 0 0 1-5.3 0zM5.5 13v7h13v-7M10 20v-4h4v4"/>',
    "pin": '<path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "leaf": '<path d="M5 19C5 10 10 5 20 4c0 9-5 15-13 15zM5 19l8-8"/>',
    "wave": '<path d="M3 12h1.5M7 8.5v7M11 5v14M15 8v8M19 10.5v3M21 12h.5"/>',
    "chart": '<path d="M4 20V4M4 20h16M8 16v-4M12 16V8M16 16v-6"/>',
    "check": '<rect x="3" y="3" width="18" height="18" rx="4"/><path d="M7.5 12.5l3 3 6-7"/>',
    "food": '<path d="M4 13h16a8 8 0 0 1-16 0zM2.5 13h19M9 9c0-2 2-2 2-4M13 9c0-2 2-2 2-4"/>',
    "arrow": '<path d="M8 16L16 8M9 8h7v7"/>',
}


def icon(d, name, x, y, s, color, sw=2.2):
    k = s / 24
    d.add(f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.3f})" fill="none" stroke="{color}" '
          f'stroke-width="{sw / k:.2f}" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>')


def shade(hexc, f):
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if f < 0:
        r, g, b = (int(c * (1 + f)) for c in (r, g, b))
    else:
        r, g, b = (int(c + (255 - c) * f) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def day_label(iso):
    dd = date.fromisoformat(iso)
    return f"{dd.day} {dd.strftime('%b')}"


def ago(iso, today):
    n = (today - date.fromisoformat(iso)).days
    return "today" if n <= 0 else "yesterday" if n == 1 else f"{n} days ago" if n < 45 else f"on {day_label(iso)}"


def finish(d, h):
    d.h = h
    d.parts.insert(0, f'<rect width="{d.w}" height="{h}" rx="22" fill="{d.t["panel"]}"/>')
    return d.render()


# ------------------------------------------------------------------ hero
def iso_blocks(d, ox, oy, s):
    """A small isometric build: blocks stacked like a floor plan becoming a building."""
    t = d.t
    dx, dy = s * 0.866, s * 0.5
    hl = t["hl"]
    blocks = [  # (i, j, k, top colour key)
        (0, 0, 0, "violet"), (1, 0, 0, "cyan"), (2, 0, 0, "violet"), (0, 1, 0, "lime"), (1, 1, 0, "amber"),
        (2, 1, 0, "cyan"), (0, 2, 0, "coral"), (1, 2, 0, "violet"),
        (0, 0, 1, "cyan"), (1, 0, 1, "lime"), (0, 1, 1, "violet"), (0, 0, 2, "hl"),
    ]
    blocks.sort(key=lambda b: (b[2], b[0] + b[1]))
    for i, j, k, key in blocks:
        cx, cy = ox + (i - j) * dx, oy + (i + j) * dy - k * s
        top = hl if key == "hl" else t[key]
        left, right = shade(top, -0.22), shade(top, -0.38)
        T, R, B, L = (cx, cy), (cx + dx, cy + dy), (cx, cy + 2 * dy), (cx - dx, cy + dy)
        pts = lambda *p: " ".join(f"{a:.1f},{b:.1f}" for a, b in p)
        st = f'stroke="{t["line"]}" stroke-width="2" stroke-linejoin="round"'
        d.add(f'<polygon points="{pts(L, B, (B[0], B[1] + s), (L[0], L[1] + s))}" fill="{left}" {st}/>')
        d.add(f'<polygon points="{pts(B, R, (R[0], R[1] + s), (B[0], B[1] + s))}" fill="{right}" {st}/>')
        d.add(f'<polygon points="{pts(T, R, B, L)}" fill="{top}" {st}/>')


def hero(t, P, S, phone=False):
    W = PHONE if phone else DESK
    d = Doc(W, 0, t, f"Hi, I'm {P['name']}. {P['tagline']}")
    pad = 26
    inner_w = W - 2 * pad - 6
    sticker(d, pad, pad, inner_w, 0, t["card"])  # placeholder, replaced below
    card_i = len(d.parts) - 2
    dot_grid(d, pad + 3, pad + 3, inner_w - 6, 10)
    grid_i = len(d.parts) - 1

    # monogram tile
    m = 104 if not phone else 92
    mx, my = pad + 28, pad + 30
    sticker(d, mx, my, m, m, t["hl"], r=22, sh=6, sw=3)
    d.text(mx + m / 2, my + m * 0.68, "UQ", "D8", m * 0.48, t["on_hl"], "middle")

    # title with a highlighter stroke behind the name
    size = 54 if not phone else 46
    tx = mx + m + 30
    ty = my + (44 if not phone else 40)
    hi = "Hi, I'm "
    hw = measure(hi, "D8", size)
    nw = measure(P["name"], "D8", size)
    bx, by, bw, bh = tx + hw - 10, ty - size * 0.80, nw + 20, size * 0.98
    rot = f'transform="rotate(-2.5 {bx + bw / 2:.1f} {by + bh / 2:.1f})"'
    d.add(f'<rect x="{bx + 4:.1f}" y="{by + 4:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="10" fill="{t["line"]}" {rot}/>')
    d.add(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="10" fill="{t["hl"]}" stroke="{t["line"]}" stroke-width="2.5" {rot}/>')
    d.text(tx, ty, hi, "D8", size, t["text"])
    d.text(tx + hw, ty, P["name"], "D8", size, t["on_hl"])

    if not phone:
        tag_w = 430
        lines = wrap(P["tagline"], "D6", 19, tag_w)
        y = ty + 36
        for ln in lines:
            d.text(tx, y, ln, "D6", 19, t["muted"])
            y += 27
        y = chips(d, tx, y - 6, [(f, t[k]) for f, k in zip(P["focus"], ["violet", "cyan", "lime", "coral"])], 560, size=12.5)
        H = max(max(y, my + m) + 44, pad + 262)
        # illustration
        iso_blocks(d, W - pad - 130, pad + 112, 36)
        # role sticker, slapped across the bottom-right edge of the card
        label = P["role"]
        lw = measure(label, "M7", 13) + 28
        lx, ly = W - pad - 233 - lw, H - 44
        cx = lx + lw / 2
        d.add(f'<g transform="rotate(4 {cx:.0f} {ly + 17})">')
        sticker(d, lx, ly, lw, 34, t["pop"], r=9, sh=4, sw=2.5)
        d.text(lx + 14, ly + 22, label, "M7", 13, t["on_pop"])
        d.add("</g>")
    else:
        y = my + m + 44
        x = mx
        for ln in wrap(P["tagline"], "D6", 22, inner_w - 56):
            d.text(x, y, ln, "D6", 22, t["muted"])
            y += 31
        y = chips(d, x, y - 6, [(f, t[k]) for f, k in zip(P["focus"], ["violet", "cyan", "lime", "coral"])], inner_w - 56, size=14, h=28, row_h=38)
        y += 22
        label = P["role"]
        lw = chip(d, x, y, label, t["pop"], size=14, color=t["on_pop"], h=30)
        H = y + 30 + 34
    # resize the card and grid now that the height is known
    ch = H - pad - 10
    d.parts[card_i] = f'<rect x="{pad + 5}" y="{pad + 5}" width="{inner_w}" height="{ch}" rx="14" fill="{t["line"]}"/>'
    d.parts[card_i + 1] = f'<rect x="{pad}" y="{pad}" width="{inner_w}" height="{ch}" rx="14" fill="{t["card"]}" stroke="{t["line"]}" stroke-width="2.5"/>'
    d.parts[grid_i] = d.parts[grid_i].replace('height="10"', f'height="{ch - 6}"')
    return finish(d, H + 4)


# ------------------------------------------------------------------ link badges
def badge(t, link):
    size = 15
    w = int(measure(link["label"], "D8", size) + 62)
    d = Doc(w + 6, 50, t, link["label"])
    sticker(d, 1, 1, w - 2, 42, t["card"], r=12, sh=4, sw=2.5)
    icon(d, link["icon"], 14, 10, 24, t["pop"] if link["id"] != "cv" else t["text"])
    d.text(46, 28, link["label"], "D8", size, t["text"])
    return d.render()


# ------------------------------------------------------------------ GitHub numbers
def stats(t, P, S, today, phone=False):
    W = PHONE if phone else DESK
    C = S["contrib"]
    d = Doc(W, 0, t, "")
    pad = 26
    d.text(pad + 4, pad + 30, "On GitHub", "D8", 30, t["text"])
    note = f"redrawn daily · {day_label(today.isoformat())} {today.year}"
    if not phone:
        d.text(W - pad - 4, pad + 26, note, "M4", 13, t["muted"], "end")
    since = int(P["since"][:4])
    repos = (S.get("user") or {}).get("public_repos", len(S.get("repos", {})))
    tiles = [
        (fmt(C["last_year"]), "contributions in", "the last year", "violet", "calendar"),
        (f"{C['current_streak']} day" + ("" if C["current_streak"] == 1 else "s"), "current streak", "and counting" if C["current_streak"] else "starts tomorrow", "lime", "flame"),
        (f"{C['longest_streak']} days", "longest streak", "ever", "amber", "trophy"),
        (fmt(C["all_time"]), "contributions", f"since {since}", "cyan", "sigma"),
    ]
    cols = 2 if phone else 4
    gap = 18
    tw = (W - 2 * pad - (cols - 1) * gap - 6) / cols
    th = 128 if not phone else 136
    y0 = pad + (54 if not phone else 50)
    for n, (big, l1, l2, tint, ic) in enumerate(tiles):
        x = pad + (n % cols) * (tw + gap)
        y = y0 + (n // cols) * (th + gap)
        sticker(d, x, y, tw, th, t[tint])
        icon(d, ic, x + tw - 40, y + 16, 24, t["text"])
        bs = 40 if not phone else 42
        d.text(x + 18, y + 62, fit(big, "D8", bs, tw - 70), "D8", bs, t["text"])
        ls = 13.5 if not phone else 16
        d.text(x + 18, y + 90, l1, "M4", ls, t["text"])
        d.text(x + 18, y + 90 + ls * 1.35, l2, "M4", ls, t["text"])
    y = y0 + ((len(tiles) - 1) // cols + 1) * (th + gap) + 4

    # year by year
    years = sorted(C["year_totals"].items())
    bh = 230 if not phone else 260
    bw = W - 2 * pad - 6
    sticker(d, pad, y, bw, bh, t["card"])
    icon(d, "chart", pad + 18, y + 18, 24, t["pop"])
    d.text(pad + 52, y + 37, "Year by year", "D8", 21 if not phone else 24, t["text"])
    if not phone:
        d.text(pad + bw - 18, y + 36, f"{repos} public repos · {len(years)} years on GitHub", "M4", 13, t["muted"], "end")
    top = max(v for _, v in years) or 1
    n = len(years)
    gx0, gx1 = pad + 30, pad + bw - 30
    slot = (gx1 - gx0) / n
    bar_w = min(64, slot * 0.62)
    base = y + bh - 38
    max_h = bh - 120
    for i, (yr, v) in enumerate(years):
        cx = gx0 + slot * (i + 0.5)
        h = max(4, max_h * v / top) if v else 3
        last = i == n - 1
        fill = t["hl"] if last else t["violet"]
        d.add(f'<rect x="{cx - bar_w / 2 + 3:.1f}" y="{base - h + 3:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="6" fill="{t["line"]}"/>')
        d.add(f'<rect x="{cx - bar_w / 2:.1f}" y="{base - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="6" fill="{fill}" stroke="{t["line"]}" stroke-width="2"/>')
        vs = 14 if not phone else 15
        d.text(cx, base - h - 10, fmt(v), "M7", vs, t["text"], "middle")
        d.text(cx, base + 24, yr if not phone else "'" + yr[2:], "M4", 13 if not phone else 15, t["muted"], "middle")
    d.add(f'<path d="M{gx0 - 8} {base + 1}H{gx1 + 8}" stroke="{t["line"]}" stroke-width="2.5" stroke-linecap="round"/>')
    H = y + bh + 30
    if phone:
        d.text(pad + 4, H + 4, note, "M4", 15, t["muted"])
        H += 22
    return finish(d, H)


# ------------------------------------------------------------------ heatmap
def levels(counts):
    nz = sorted(c for c in counts if c)
    if not nz:
        return lambda c: 0
    q = [nz[int(len(nz) * f)] for f in (0.25, 0.5, 0.75)]
    return lambda c: 0 if not c else 1 if c <= q[0] else 2 if c <= q[1] else 3 if c <= q[2] else 4


def heatmap(t, P, S, today, phone=False):
    W = PHONE if phone else DESK
    C = S["contrib"]
    win = C["window"]
    days = sorted(win.items())
    # align to weeks starting Sunday, like GitHub
    first = date.fromisoformat(days[0][0])
    first -= timedelta(days=(first.weekday() + 1) % 7)
    weeks = []
    cur = first
    while cur <= today:
        weeks.append([(cur + timedelta(days=k)) for k in range(7)])
        cur += timedelta(days=7)
    if phone:
        weeks = weeks[-26:]
    shown = [win.get(x.isoformat(), 0) for w in weeks for x in w if x <= today]
    lv = levels([c for _, c in days])
    d = Doc(W, 0, t, "")
    pad = 26
    cw = W - 2 * pad - 6
    total = sum(shown)
    label_w = 34 if not phone else 0
    pitch = (cw - 40 - label_w) / len(weeks)
    cell = pitch * 0.8
    gx = pad + 20 + label_w
    gy = pad + 92
    ch = gy - pad + 7 * pitch + 78
    sticker(d, pad, pad, cw, ch, t["card"])
    big = fmt(C["last_year"] if not phone else total)
    bs = 30
    d.text(pad + 20, pad + 44, big, "D8", bs, t["text"])
    d.text(pad + 20 + measure(big, "D8", bs) + 10, pad + 44,
           "contributions in the last year" if not phone else "in the last 6 months", "M4", 15 if not phone else 17, t["text"])
    # months
    last_m = None
    for i, w in enumerate(weeks):
        m = w[0].month
        if m != last_m and w[0].day <= 7 + (0 if i else 7):
            if not (i > len(weeks) - 2):
                d.text(gx + i * pitch, gy - 12, w[0].strftime("%b"), "M4", 12.5 if not phone else 14, t["muted"])
            last_m = m
        elif last_m is None:
            last_m = m
    if not phone:
        for r, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
            d.text(pad + 18, gy + r * pitch + cell * 0.8, lab, "M4", 11.5, t["muted"])
    for i, w in enumerate(weeks):
        for r, day in enumerate(w):
            if day > today:
                continue
            c = win.get(day.isoformat(), 0)
            l = lv(c)
            stroke = f' stroke="{t["line"]}" stroke-width="1.3"' if l else ""
            d.add(f'<rect x="{gx + i * pitch:.1f}" y="{gy + r * pitch:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="{cell * 0.22:.1f}" fill="{t["heat"][l]}"{stroke}/>')
    fy = gy + 7 * pitch + 34
    active = sum(1 for c in shown if c)
    busy = max(((c, x) for x, c in days), default=(0, None))
    fs = 13 if not phone else 15
    left = f"{active} active days" + (f" · busiest: {busy[0]} on {day_label(busy[1])}" if busy[0] and not phone else "")
    d.text(pad + 20, fy, left, "M4", fs, t["muted"])
    lx = pad + cw - 20 - (5 * 18) - measure("More", "M4", fs) - 8
    d.text(lx - 8, fy, "Less", "M4", fs, t["muted"], "end")
    for k in range(5):
        stroke = f' stroke="{t["line"]}" stroke-width="1.3"' if k else ""
        d.add(f'<rect x="{lx + k * 18:.1f}" y="{fy - 12}" width="14" height="14" rx="3" fill="{t["heat"][k]}"{stroke}/>')
    d.text(lx + 5 * 18 + 4, fy, "More", "M4", fs, t["muted"])
    return finish(d, pad + ch + 30)


# ------------------------------------------------------------------ weekly line
def weekly(t, P, S, today, phone=False):
    W = PHONE if phone else DESK
    C = S["contrib"]
    nweeks = 16 if not phone else 10
    end = today
    starts = [end - timedelta(days=7 * (nweeks - k) - 1) for k in range(nweeks)]
    vals = []
    for s0 in starts:
        vals.append(sum(C["days"].get((s0 + timedelta(days=k)).isoformat(), 0) for k in range(7)))
    d = Doc(W, 0, t, "")
    pad = 26
    cw = W - 2 * pad - 6
    ch = 320 if not phone else 350
    sticker(d, pad, pad, cw, ch, t["card"])
    total = sum(vals)
    big = fmt(total)
    d.text(pad + 20, pad + 44, big, "D8", 30, t["text"])
    d.text(pad + 20 + measure(big, "D8", 30) + 10, pad + 44, f"contributions in the last {nweeks} weeks", "M4", 15 if not phone else 16, t["text"])
    top = max(vals) or 1
    step = 5 if top <= 25 else 10 if top <= 60 else 25 if top <= 150 else 50 if top <= 300 else 100
    ymax = ((top + step - 1) // step) * step
    x0, x1 = pad + 58, pad + cw - 26
    y0, y1 = pad + 104, pad + ch - 58
    fs = 12.5 if not phone else 14
    v = 0
    while v <= ymax:
        yy = y1 - (y1 - y0) * v / ymax
        d.add(f'<path d="M{x0} {yy:.1f}H{x1}" stroke="{t["grid"]}" stroke-width="1.5" stroke-dasharray="{"0" if v == 0 else "5 6"}"/>')
        d.text(x0 - 12, yy + 4.5, str(v), "M4", fs, t["muted"], "end")
        v += step * (2 if ymax / step > 6 else 1)
    pts = [(x0 + (x1 - x0) * i / (nweeks - 1), y1 - (y1 - y0) * val / ymax) for i, val in enumerate(vals)]
    # smooth path (Catmull-Rom -> Bezier), clamped so the curve never dips below zero
    def path(ps):
        s = f"M{ps[0][0]:.1f} {ps[0][1]:.1f}"
        for i in range(len(ps) - 1):
            p0 = ps[max(i - 1, 0)]; p1 = ps[i]; p2 = ps[i + 1]; p3 = ps[min(i + 2, len(ps) - 1)]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, min(y1, p1[1] + (p2[1] - p0[1]) / 6))
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, min(y1, p2[1] - (p3[1] - p1[1]) / 6))
            s += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
        return s
    line = path(pts)
    gid = "areafill"
    d.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["chart_fill"]}" stop-opacity="0.38"/>'
                  f'<stop offset="1" stop-color="{t["chart_fill"]}" stop-opacity="0.02"/></linearGradient>')
    d.add(f'<path d="{line} L{x1:.1f} {y1} L{x0:.1f} {y1} Z" fill="url(#{gid})"/>')
    d.add(f'<path d="{line}" fill="none" stroke="{t["line"]}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
    d.add(f'<path d="{line}" fill="none" stroke="{t["chart"]}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>')
    best = max(range(nweeks), key=lambda i: vals[i])
    for i, (px, py) in enumerate(pts):
        r = 6.5 if i == best else 4.5
        d.add(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="{t["hl"] if i == best else t["card"]}" stroke="{t["line"]}" stroke-width="2"/>')
    if vals[best]:
        bx, by = pts[best]
        lab = f"{vals[best]} that week"
        lw = measure(lab, "M7", fs) + 16
        lx = min(max(bx - lw / 2, x0), x1 - lw)
        d.add(f'<rect x="{lx:.1f}" y="{by - 38:.1f}" width="{lw:.1f}" height="24" rx="6" fill="{t["pop"]}" stroke="{t["line"]}" stroke-width="2"/>')
        d.text(lx + 8, by - 21.5, lab, "M7", fs, t["on_pop"])
    every = 2 if not phone else 3
    for i, s0 in enumerate(starts):
        if (nweeks - 1 - i) % every == 0:
            d.text(pts[i][0], y1 + 26, day_label(s0.isoformat()), "M4", fs, t["muted"], "middle")
    d.text(pad + cw - 20, pad + 44, "per week", "M4", 13 if not phone else 14, t["muted"], "end")
    return finish(d, pad + ch + 30)


# ------------------------------------------------------------------ whoami terminal
def whoami(t, P, S, today, phone=False):
    W = PHONE if phone else DESK
    Wd = P["whoami"]
    d = Doc(W, 0, t, "")
    pad = 26
    cw = W - 2 * pad - 6
    fs = 16 if not phone else 17
    lh = fs * 1.62
    x = pad + 28
    maxw = cw - 56
    lines = []  # (kind, text)
    lines.append(("cmd", "whoami"))
    who = Wd["who"]
    if phone:
        lines.append(("hi", who[0]))
        lines.append(("plain", " · ".join(who[1:])))
    else:
        lines.append(("who", who))
    for ln in wrap(Wd["about"], "M4", fs, maxw):
        lines.append(("plain", ln))
    lines.append(("gap", ""))
    lines.append(("cmd", "cat now.txt"))
    for item in Wd["now"]:
        for k, ln in enumerate(wrap(item, "M4", fs, maxw - 34)):
            lines.append(("now" if k == 0 else "cont", ln))
    repos = S.get("repos") or {}
    if repos:
        name, r = max(repos.items(), key=lambda kv: kv[1]["pushed"])
        if name != P["user"]:
            lines.append(("gap", ""))
            lines.append(("cmd", "git log -1 --all"))
            lines.append(("plain", fit(f"pushed to {name} {ago(r['pushed'], today)}", "M4", fs, maxw)))
    lines.append(("cursor", ""))
    ch = 44 + 34 + sum(lh if k != "gap" else lh * 0.45 for k, _ in lines) - lh * 0.55
    sticker(d, pad, pad, cw, ch, t["screen"])
    d.add(f'<path d="M{pad + 2} {pad + 44}H{pad + cw - 2}" stroke="{t["line"]}" stroke-width="2.5"/>')
    for k, col in enumerate(("#ff6b6b", "#fbbf24", "#a3e635")):
        d.add(f'<circle cx="{pad + 24 + k * 20}" cy="{pad + 22}" r="6" fill="{col}" stroke="{t["line"]}" stroke-width="1.5"/>')
    d.text(pad + cw / 2, pad + 27, f"{Wd['host']}: ~", "M4", 13.5, t["on_screen_muted"], "middle")
    y = pad + 44 + 34
    for kind, text in lines:
        if kind == "cmd":
            d.text(x, y, "$", "M7", fs, t["prompt"])
            d.text(x + measure("$ ", "M4", fs), y, text, "M7", fs, t["on_screen"])
        elif kind == "who":
            cx = x
            for k, part in enumerate(text):
                if k:
                    d.text(cx, y, "  ·  ", "M4", fs, t["on_screen_muted"])
                    cx += measure("  ·  ", "M4", fs)
                d.text(cx, y, part, "M7" if k == 0 else "M4", fs, t["prompt"] if k == 0 else t["on_screen"])
                cx += measure(part, "M4", fs)
        elif kind == "hi":
            d.text(x, y, text, "M7", fs, t["prompt"])
        elif kind == "plain":
            d.text(x, y, text, "M4", fs, t["on_screen"])
        elif kind == "now":
            d.text(x, y, "->", "M7", fs, t["prompt"])
            d.text(x + 34, y, text, "M4", fs, t["on_screen"])
        elif kind == "cont":
            d.text(x + 34, y, text, "M4", fs, t["on_screen"])
        elif kind == "cursor":
            d.text(x, y, "$", "M7", fs, t["prompt"])
            d.add(f'<rect x="{x + measure("$ ", "M4", fs):.1f}" y="{y - fs * 0.82:.1f}" width="{fs * 0.6:.1f}" height="{fs * 1.02:.1f}" fill="{t["on_screen"]}">'
                  f'<animate attributeName="opacity" values="1;1;0;0" dur="1.1s" repeatCount="indefinite"/></rect>')
        y += lh if kind != "gap" else lh * 0.45
    return finish(d, pad + ch + 30)


# ------------------------------------------------------------------ section label
def label(t, text, note, phone=False):
    W = PHONE if phone else DESK
    d = Doc(W, 0, t, text)
    size = 26 if not phone else 30
    lw = measure(text, "D8", size) + 36
    lh = size + 22
    d.add(f'<g transform="rotate(-2 {14 + lw / 2:.0f} {16 + lh / 2:.0f})">')
    sticker(d, 14, 16, lw, lh, t["hl"], r=12, sh=5, sw=2.5)
    d.text(14 + 18, 16 + lh / 2 + size * 0.35, text, "D8", size, t["on_hl"])
    d.add("</g>")
    if note:
        chip(d, 14 + lw + 22, 16 + lh / 2 - 13, note, t["card"], font="M4", size=13 if not phone else 15, h=28 if not phone else 30)
    d.h = 16 + lh + 18
    return d.render()


# ------------------------------------------------------------------ stack
def stack(t, P, S, phone=False):
    W = PHONE if phone else DESK
    d = Doc(W, 0, t, "")
    pad = 26
    cw = W - 2 * pad - 6
    parts_at = len(d.parts)
    y = pad + 28
    col = 170 if not phone else 0
    fs = 13 if not phone else 15
    for g in P["stack"]:
        if phone:
            d.text(pad + 22, y + 18, g["group"], "D8", 21, t["text"])
            y += 30
            y = chips(d, pad + 22, y, [(i, t[g["tint"]]) for i in g["items"]], cw - 44, size=fs, h=30, row_h=40) + 22
        else:
            d.add(f'<rect x="{pad + 22}" y="{y + 4}" width="12" height="12" rx="3" fill="{t[g["tint"]]}" stroke="{t["line"]}" stroke-width="2"/>')
            d.text(pad + 44, y + 16, g["group"], "D8", 18, t["text"])
            y = chips(d, pad + 22 + col, y - 2, [(i, t[g["tint"]]) for i in g["items"]], cw - col - 44, size=fs, h=26, row_h=36) + 20
    ch = y - pad + 8
    sh = [f'<rect x="{pad + 5}" y="{pad + 5}" width="{cw}" height="{ch}" rx="14" fill="{t["line"]}"/>',
          f'<rect x="{pad}" y="{pad}" width="{cw}" height="{ch}" rx="14" fill="{t["card"]}" stroke="{t["line"]}" stroke-width="2.5"/>']
    d.parts[parts_at:parts_at] = sh
    return finish(d, pad + ch + 30)


# ------------------------------------------------------------------ career
def career(t, P, S, phone=False):
    W = PHONE if phone else DESK
    d = Doc(W, 0, t, "")
    pad = 26
    cw = W - 2 * pad - 6
    at = len(d.parts)
    x = pad + 30
    tx = x + 34
    y = pad + 40
    fs = 15.5 if not phone else 17
    dots = []
    for k, job in enumerate(P["career"]):
        dots.append(y - 7)
        d.text(tx, y, job["role"], "D8", 22 if not phone else 23, t["text"])
        if not phone:
            d.text(pad + cw - 24, y - 2, f"{job['when']}  ·  {job['where']}", "M4", 13.5, t["muted"], "end")
            y += 26
            d.text(tx, y, job["org"], "M7", 14, t["pop"])
        else:
            y += 28
            d.text(tx, y, f"{job['org']} · {job['when']}", "M7", 15, t["pop"])
        y += 28
        for ln in wrap(job["win"], "D6", fs, cw - (tx - pad) - 30):
            d.text(tx, y, ln, "D6", fs, t["muted"])
            y += fs * 1.45
        y += 26
    d.add(f'<path d="M{x} {dots[0]}V{dots[-1]}" stroke="{t["line"]}" stroke-width="2.5" stroke-dasharray="2 7" stroke-linecap="round"/>')
    for k, dy in enumerate(dots):
        d.add(f'<circle cx="{x}" cy="{dy}" r="9" fill="{t["hl"] if k == 0 else t["violet"]}" stroke="{t["line"]}" stroke-width="2.5"/>')
    ch = y - pad - 8
    d.parts[at:at] = [f'<rect x="{pad + 5}" y="{pad + 5}" width="{cw}" height="{ch}" rx="14" fill="{t["line"]}"/>',
                      f'<rect x="{pad}" y="{pad}" width="{cw}" height="{ch}" rx="14" fill="{t["card"]}" stroke="{t["line"]}" stroke-width="2.5"/>']
    return finish(d, pad + ch + 30)


# ------------------------------------------------------------------ project card
STATUS = {"live": "hl"}


def project_facts(p, S, today):
    if p.get("fact"):
        return list(p["fact"])
    r = (S.get("repos") or {}).get(p.get("repo") or "", {})
    out = []
    if r.get("language"):
        out.append(r["language"])
    if r.get("pushed"):
        out.append(f"updated {day_label(r['pushed'])}")
    if r.get("stars"):
        out.append(f"{r['stars']} star" + ("" if r["stars"] == 1 else "s"))
    if r.get("homepage"):
        out.append("live demo")
    return out


def project(t, p, S, today, phone=False):
    W, H = (490, 300) if not phone else (330, 345)
    d = Doc(W, H, t, "")
    x, y, cw, ch = 10, 10, W - 26, H - 26
    d.add(f'<rect width="{W}" height="{H}" rx="20" fill="{t["panel"]}"/>')
    sticker(d, x, y, cw, ch, t["card"])
    # tinted header band
    d.add(f'<path d="M{x + 1.5} {y + 14}a12.5 12.5 0 0 1 12.5-12.5H{x + cw - 14}a12.5 12.5 0 0 1 12.5 12.5V{y + 88}H{x + 1.5}z" fill="{t[p["tint"]]}"/>')
    d.add(f'<path d="M{x + 1} {y + 88}H{x + cw - 1}" stroke="{t["line"]}" stroke-width="2.5"/>')
    s = 58 if not phone else 54
    sticker(d, x + 20, y + 16, s, s, t["card"], r=14, sh=4, sw=2.5)
    icon(d, p["icon"], x + 20 + s * 0.2, y + 16 + s * 0.2, s * 0.6, t["text"], 2.4)
    nx = x + 20 + s + 18
    ns = 28 if not phone else 23
    d.text(nx, y + 46, fit(p["name"], "D8", ns, cw - (nx - x) - 60), "D8", ns, t["text"])
    st = p["status"]
    live = st == "live"
    chip(d, nx, y + 56, st, t["hl"] if live else t["card"], size=11.5 if not phone else 13, h=22 if not phone else 24,
         color=t["on_hl"] if live else t["text"])
    if p.get("url"):  # corner arrow only on cards that link somewhere
        ax, ay = x + cw - 44, y + 18
        sticker(d, ax, ay, 28, 28, t["pop"], r=7, sh=3, sw=2)
        icon(d, "arrow", ax + 2, ay + 2, 24, t["on_pop"], 2.6)
    fs = 17 if not phone else 19
    yy = y + 124
    for ln in wrap(p["line"], "D6", fs, cw - 40, 3 if not phone else 5):
        d.text(x + 20, yy, ln, "D6", fs, t["text"])
        yy += fs * 1.38
    if not phone:
        chips(d, x + 20, y + ch - 78, [(c, t["panel"]) for c in p["chips"]], cw - 40, size=11.5, h=23, font="M7")
    facts = project_facts(p, S, today)
    d.text(x + 20, y + ch - 20, fit("  ·  ".join(facts), "M4", 13 if not phone else 15, cw - 40), "M4", 13 if not phone else 15, t["muted"])
    return d.render()
