"""Generate the Matrix-styled GitHub stats card (stats.svg).

usage: python stats.py <github_user> <output.svg>

Uses the GraphQL API when GITHUB_TOKEN is set (GitHub Actions) and falls back
to public endpoints otherwise, so it also runs locally without credentials.
"""
import datetime as dt
import html
import json
import os
import pathlib
import re
import sys
import urllib.request

API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN")


def get(url, accept="application/vnd.github+json"):
    headers = {"Accept": accept, "User-Agent": "readme-stats"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return r.read().decode("utf-8")


def years_since(created_at):
    return range(int(created_at[:4]), dt.datetime.now(dt.timezone.utc).year + 1)


def graphql(query, variables):
    req = urllib.request.Request(f"{API}/graphql", data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Authorization": f"Bearer {TOKEN}", "User-Agent": "readme-stats"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    if res.get("errors"):
        raise RuntimeError(res["errors"])
    return res["data"]["user"]


def collect_graphql(user):
    created = graphql("query($login: String!) { user(login: $login) { createdAt } }", {"login": user})["createdAt"]
    cals = " ".join(f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") '
                    "{ contributionCalendar { weeks { contributionDays { date contributionCount } } } }"
                    for y in years_since(created))
    query = """query($login: String!) { user(login: $login) {
      followers { totalCount }
      pullRequests { totalCount }
      issues { totalCount }
      repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
        totalCount
        nodes { stargazerCount languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
      }
      """ + cals + """
    } }"""
    u = graphql(query, {"login": user})
    langs = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    days = sorted({(d["date"], d["contributionCount"]) for k, v in u.items() if k.startswith("y")
                   for w in v["contributionCalendar"]["weeks"] for d in w["contributionDays"]})
    return {"repos": u["repositories"]["totalCount"],
            "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
            "followers": u["followers"]["totalCount"],
            "prs": u["pullRequests"]["totalCount"], "issues": u["issues"]["totalCount"],
            "langs": langs, "days": days, "total": sum(n for _, n in days), "since": created[:4]}


def collect_public(user):
    profile = json.loads(get(f"{API}/users/{user}"))
    repos = [r for r in json.loads(get(f"{API}/users/{user}/repos?per_page=100&type=owner")) if not r["fork"]]
    langs = {}
    for r in repos:
        for name, size in json.loads(get(r["languages_url"])).items():
            langs[name] = langs.get(name, 0) + size
    search = lambda kind: json.loads(get(f"{API}/search/issues?q=author:{user}+type:{kind}&per_page=1"))["total_count"]
    days = set()
    for y in years_since(profile["created_at"]):
        page = get(f"https://github.com/users/{user}/contributions?from={y}-01-01&to={y}-12-31", accept="text/html")
        dates = {cid: d for d, cid in re.findall(r'data-date="([\d-]+)" id="(contribution-day-component-[\d-]+)"', page)}
        for cid, text in re.findall(r'<tool-tip[^>]*for="(contribution-day-component-[\d-]+)"[^>]*>([^<]*)</tool-tip>', page):
            m = re.match(r"(\d+) contribution", text)
            if cid in dates:
                days.add((dates[cid], int(m.group(1)) if m else 0))
    days = sorted(days)
    return {"repos": len(repos), "stars": sum(r["stargazers_count"] for r in repos),
            "followers": profile["followers"], "prs": search("pr"), "issues": search("issue"),
            "langs": langs, "days": days, "total": sum(n for _, n in days), "since": profile["created_at"][:4]}


def streaks(days):
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    days = [d for d in days if d[0] <= today]
    longest = run = 0
    for _, n in days:
        run = run + 1 if n else 0
        longest = max(longest, run)
    current = 0
    for i, (date, n) in enumerate(reversed(days)):
        if n:
            current += 1
        elif i == 0 and date == today:
            continue  # today may simply not have contributions yet
        else:
            break
    return current, longest


def render(user, s):
    W, H = 830, 330
    cur, best = streaks(s["days"])
    synced = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total_bytes = sum(s["langs"].values()) or 1
    langs = sorted(s["langs"].items(), key=lambda kv: -kv[1])[:5]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="GitHub stats de {user}: {s["repos"]} repositórios, {s["stars"]} estrelas, {s["total"]} contribuições '
         f'desde {s["since"]}, sequência atual de {cur} dias, recorde de {best} dias.">',
         f"""<style>
  text {{ font-family: 'Courier New', Consolas, monospace; white-space: pre; }}
  .path {{ fill: #00C832; font-size: 13px; }}
  .sync {{ fill: #007A1F; font-size: 11px; letter-spacing: 1px; text-anchor: end; }}
  .hdr {{ fill: #007A1F; font-size: 11px; letter-spacing: 2px; }}
  .k {{ fill: #00A82B; font-size: 14px; }}
  .lead {{ fill: #004D14; font-size: 14px; }}
  .v {{ fill: #E6FFE6; font-size: 14px; font-weight: bold; text-anchor: end; }}
  .big {{ fill: #00FF41; font-size: 40px; font-weight: bold; text-anchor: middle; filter: url(#glow); }}
  .cap {{ fill: #00C832; font-size: 11px; letter-spacing: 1px; text-anchor: middle; }}
  .sub {{ fill: #007A1F; font-size: 11px; text-anchor: middle; }}
  .ln {{ fill: #E6FFE6; font-size: 13px; }}
  .pct {{ fill: #00C832; font-size: 12px; text-anchor: end; }}
  .cur {{ animation: blink 1s steps(1) infinite; }}
  .ring {{ animation: spin 6s linear infinite; transform-origin: 415px 128px; }}
  .bar {{ transform-box: fill-box; transform-origin: bottom; animation: grow .6s ease-out both; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  @keyframes grow {{ from {{ transform: scaleY(0); }} }}
</style>
<defs>
  <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur stdDeviation="2" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="#050805" stroke="#00FF41" stroke-opacity=".6"/>
<path d="M1 38 H{W-1}" stroke="#00FF41" stroke-opacity=".25" stroke-dasharray="4 4"/>
<circle cx="22" cy="20" r="5" fill="#00FF41" opacity=".9"/><circle cx="40" cy="20" r="5" fill="#00FF41" opacity=".5"/><circle cx="58" cy="20" r="5" fill="#00FF41" opacity=".2"/>
<text x="80" y="24" class="path">~/stats --user {html.escape(user)}</text>
<text x="{W-20}" y="24" class="sync">LAST SYNC {synced}</text>"""]

    # left: key/value list
    o.append('<text x="26" y="62" class="hdr">PERFIL</text>')
    rows = [("repositórios", s["repos"]), ("estrelas", s["stars"]), ("seguidores", s["followers"]),
            ("contribuições", s["total"]), ("pull requests", s["prs"]), ("issues", s["issues"])]
    for i, (k, v) in enumerate(rows):
        y = 88 + i * 24
        o.append(f'<text x="26" y="{y}" class="k">{k}</text>'
                 f'<text x="{26 + (len(k) + 1) * 8.4:.0f}" y="{y}" class="lead">{"." * max(2, 24 - len(k))}</text>'
                 f'<text x="300" y="{y}" class="v">{v}</text>')

    # middle: streak ring
    cx, cy, r = 415, 128, 54
    frac = cur / best if best else 0
    circ = 2 * 3.14159 * r
    o.append(f'<path d="M335 50 V220 M495 50 V220" stroke="#00FF41" stroke-opacity=".15"/>'
             f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#00FF41" stroke-opacity=".12" stroke-width="8"/>'
             f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#00FF41" stroke-width="8" stroke-linecap="round" '
             f'stroke-dasharray="{circ * frac:.1f} {circ:.1f}" transform="rotate(-90 {cx} {cy})" filter="url(#glow)"/>'
             f'<g class="ring"><circle cx="{cx}" cy="{cy}" r="{r + 12}" fill="none" stroke="#00FF41" stroke-opacity=".35" '
             f'stroke-dasharray="3 9"/></g>'
             f'<text x="{cx}" y="{cy + 14}" class="big">{cur}</text>'
             f'<text x="{cx}" y="{cy + r + 32}" class="cap">SEQUÊNCIA ATUAL</text>'
             f'<text x="{cx}" y="{cy + r + 48}" class="sub">recorde: {best} dia{"s" if best != 1 else ""}</text>')

    # right: languages
    o.append('<text x="520" y="62" class="hdr">LINGUAGENS</text>')
    shades = ["#00FF41", "#00D836", "#00B02B", "#008F23", "#006B1A"]
    for i, (name, size) in enumerate(langs):
        y = 88 + i * 28
        pct = size / total_bytes
        o.append(f'<text x="520" y="{y}" class="ln">{html.escape(name.lower())}</text>')
        blocks = 14
        lit = max(1, round(pct * blocks))
        for b in range(blocks):
            x = 620 + b * 10
            on = b < lit
            o.append(f'<rect x="{x}" y="{y - 11}" width="8" height="12" rx="1.5" fill="{shades[i] if on else "#00FF41"}" '
                     f'opacity="{1 if on else .1}"/>')
        o.append(f'<text x="{W-24}" y="{y}" class="pct">{pct * 100:.1f}%</text>')
    if not langs:
        o.append('<text x="520" y="88" class="k">sem dados ainda</text>')

    # bottom: weekly activity
    months = {}
    for date, n in s["days"]:
        months[date[:7]] = months.get(date[:7], 0) + n
    weeks = list(months.values())[-48:]
    top = max(weeks) if weeks and max(weeks) else 1
    o.append(f'<path d="M20 238 H{W-20}" stroke="#00FF41" stroke-opacity=".15"/>'
             f'<text x="26" y="258" class="hdr">ATIVIDADE MENSAL · DESDE {s["since"]}</text>'
             f'<text x="{W-24}" y="258" class="sync">{s["total"]} CONTRIBUIÇÕES</text>')
    base, maxh = 312, 40
    bw = min(28, (W - 60) / max(1, len(weeks)) - 3)
    x0 = (W - len(weeks) * (bw + 3)) / 2
    for i, n in enumerate(weeks):
        h = max(2, n / top * maxh)
        lvl = 0 if n == 0 else min(4, 1 + int(n / top * 3.99))
        color = ["#0F2A12", "#006B1A", "#00A82B", "#00D836", "#00FF41"][lvl]
        o.append(f'<rect class="bar" style="animation-delay:{i * 0.03:.2f}s" x="{x0 + i * (bw + 3):.1f}" y="{base - h:.1f}" '
                 f'width="{bw}" height="{h:.1f}" rx="2" fill="{color}"/>')
    o.append('</svg>')
    return "\n".join(o) + "\n"


def main():
    user, out = sys.argv[1], pathlib.Path(sys.argv[2])
    data = None
    if TOKEN:
        try:
            data = collect_graphql(user)
        except Exception as e:  # fall back to public endpoints rather than fail the job
            print(f"graphql failed, using public endpoints: {e}", file=sys.stderr)
    data = data or collect_public(user)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(user, data), encoding="utf-8")
    print(f"wrote {out}: repos={data['repos']} stars={data['stars']} total={data['total']} streak={streaks(data['days'])}")


if __name__ == "__main__":
    main()
