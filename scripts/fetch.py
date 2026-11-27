# Reads every number the profile shows. All sources are public; GITHUB_TOKEN (if set) only lifts the REST rate limit.
import json, os, re, urllib.error, urllib.request
from datetime import date, timedelta
from html.parser import HTMLParser

UA = "usmanqasim-profile-build (github.com/UsmanQasim/UsmanQasim)"


class SourceError(Exception):
    pass


def get(url, token=None):
    headers = {"User-Agent": UA}
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
            return r.read().decode("utf8")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise SourceError(f"{url}: {e}")


# ------------------------------------------------------------------ contribution calendar
class _Calendar(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cells, self.tips, self.heading = [], {}, []
        self._tip_for, self._tip, self._in_h = None, [], False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "td" and a.get("data-date"):
            self.cells.append((a["data-date"], a.get("id"), int(a.get("data-level") or 0)))
        elif tag == "tool-tip" and a.get("for"):
            self._tip_for, self._tip = a["for"], []
        elif tag == "h2" and a.get("id") == "js-contribution-activity-description":
            self._in_h = True

    def handle_data(self, data):
        if self._tip_for is not None:
            self._tip.append(data)
        if self._in_h:
            self.heading.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self._tip_for is not None:
            self.tips[self._tip_for] = " ".join("".join(self._tip).split())
            self._tip_for = None
        elif tag == "h2":
            self._in_h = False


def parse_calendar(html):
    """Public contributions page -> (heading total, {iso date: count}) with every day of the window."""
    p = _Calendar()
    p.feed(html)
    m = re.search(r"([\d,]+)\s+contributions?", " ".join("".join(p.heading).split()))
    if not p.cells or not m:
        raise SourceError("contribution calendar not found (GitHub may have changed the page)")
    days = {}
    for d, cid, _ in p.cells:
        t = re.match(r"(No|[\d,]+) contributions? on", p.tips.get(cid, ""))
        if not t:
            raise SourceError(f"no count for {d}")
        days[d] = 0 if t.group(1) == "No" else int(t.group(1).replace(",", ""))
    return int(m.group(1).replace(",", "")), dict(sorted(days.items()))


def streaks(days, today):
    """days: {iso: count}. Today with nothing yet does not break the current streak."""
    active = {d for d, c in days.items() if c}
    best = run = 0
    prev = None
    for d in sorted(active):
        dd = date.fromisoformat(d)
        run = run + 1 if prev and dd - prev == timedelta(days=1) else 1
        best, prev = max(best, run), dd
    cur, day = 0, today
    if today.isoformat() not in active:
        day = today - timedelta(days=1)
    while day.isoformat() in active:
        cur, day = cur + 1, day - timedelta(days=1)
    return cur, best


def fetch_contrib(user, since_year, today, cached_years):
    base = f"https://github.com/users/{user}/contributions"
    last_total, last_days = parse_calendar(get(base))
    years, all_days = {}, {}
    for y in range(since_year, today.year + 1):
        key = str(y)
        if y < today.year and key in cached_years:
            years[key] = cached_years[key]
        else:
            total, days = parse_calendar(get(f"{base}?from={y}-01-01&to={y}-12-31"))
            years[key] = {"total": total, "days": {d: c for d, c in days.items() if c and d.startswith(key)}}
        all_days.update(years[key]["days"])
    for d, c in last_days.items():          # the rolling window is the freshest read of recent days
        if c:
            all_days[d] = c
        else:
            all_days.pop(d, None)
    all_days = {d: c for d, c in all_days.items() if d <= today.isoformat()}
    cur, best = streaks(all_days, today)
    return {
        "last_year": last_total,
        "window": last_days,                 # every day of the rolling year, zeros included
        "days": all_days,                    # nonzero days, all time
        "year_totals": {k: v["total"] for k, v in years.items()},
        "all_time": sum(v["total"] for v in years.values()),
        "current_streak": cur,
        "longest_streak": best,
    }, years


def fetch_repos(user, token):
    repos = json.loads(get(f"https://api.github.com/users/{user}/repos?per_page=100&type=owner", token))
    if not isinstance(repos, list):
        raise SourceError("unexpected repos response")
    out = {}
    for r in repos:
        if r.get("fork"):
            continue
        out[r["name"]] = {
            "stars": r["stargazers_count"], "forks": r["forks_count"], "language": r["language"],
            "pushed": r["pushed_at"][:10], "homepage": r.get("homepage") or "", "description": r.get("description") or "",
        }
    return out


def fetch_user(user, token):
    u = json.loads(get(f"https://api.github.com/users/{user}", token))
    return {"followers": u["followers"], "public_repos": u["public_repos"], "created": u["created_at"][:10]}


def collect(profile, today, state):
    """Refresh what can be refreshed; keep the saved copy of anything that fails. Returns (state, errors)."""
    token = os.environ.get("GITHUB_TOKEN")
    user = profile["user"]
    errors = []
    state = dict(state or {})
    try:
        state["user"] = fetch_user(user, token)
    except (SourceError, KeyError, ValueError) as e:
        errors.append(f"user: {e}")
    try:
        state["repos"] = fetch_repos(user, token)
    except (SourceError, KeyError, ValueError) as e:
        errors.append(f"repos: {e}")
    since = int((state.get("user") or {}).get("created", profile["since"])[:4])
    try:
        state["contrib"], state["years_cache"] = fetch_contrib(user, since, today, state.get("years_cache", {}))
        state["contrib_read"] = today.isoformat()
    except SourceError as e:
        errors.append(f"contributions: {e}")
    return state, errors
