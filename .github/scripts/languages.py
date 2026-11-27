"""Generate the arsenal card (languages.svg) — the <summary> of the stack in the README.

Fixed size no matter how many tools are listed in arsenal.json:
  * one counter per category,
  * every tool scrolling by in an endless ticker,
  * a bar with the real language usage across the user's public repositories
    (average of each repo's language split, so one big repo does not dominate),
  * the "ABRIR O ARSENAL" call to action.

usage: python languages.py <github_user> <output.svg>

Reuses the data helpers from stats.py: GraphQL when GITHUB_TOKEN is set,
public endpoints otherwise.
"""
import html
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import stats  # noqa: E402

DATA = json.loads((pathlib.Path(__file__).parent / "arsenal.json").read_text(encoding="utf-8"))
W, H = 800, 262
GREEN, RED = "#00FF41", "#FF1A3C"
SHADES = ["#00FF41", "#00C832", "#00962A", "#006B1A"]
TOP = 3
UBX, UBW = 140, 360       # usage bar x / width
TICK_STEP, TICK_T = 78, 40  # ticker spacing / tile size


def collect(user):
    """Return a list of per-repo {language: bytes} dicts (public, non-fork, with code)."""
    if stats.TOKEN:
        try:
            q = """query($login: String!) { user(login: $login) {
              repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
                nodes { languages(first: 10) { edges { size node { name } } } } } } }"""
            nodes = stats.graphql(q, {"login": user})["repositories"]["nodes"]
            per = [{e["node"]["name"]: e["size"] for e in n["languages"]["edges"]} for n in nodes]
            return [p for p in per if p]
        except Exception as e:  # fall back to public endpoints rather than fail the job
            print(f"graphql failed, using public endpoints: {e}", file=sys.stderr)
    repos = [r for r in json.loads(stats.get(f"{stats.API}/users/{user}/repos?per_page=100&type=owner")) if not r["fork"]]
    per = [json.loads(stats.get(r["languages_url"])) for r in repos]
    return [p for p in per if p]


def shares(per_repo):
    """Average language share across repos -> [(name, share, repos_with_it)] sorted desc."""
    acc, seen = {}, {}
    for langs in per_repo:
        tot = sum(langs.values())
        for n, v in langs.items():
            acc[n] = acc.get(n, 0) + v / tot
            seen[n] = seen.get(n, 0) + 1
    k = len(per_repo) or 1
    return sorted(((n, a / k, seen[n]) for n, a in acc.items()), key=lambda t: -t[1])


def render(per_repo):
    esc = html.escape
    cats = DATA["categories"]
    icons = DATA["icons"]
    tools = [t for c in cats for t in c["tools"]]
    n = len(tools)
    top = shares(per_repo)[:TOP]
    usage = " · ".join(f"{name.lower()} {sh * 100:.0f}%" for name, sh, _ in top)

    # ticker: repeat the tool list until it covers the visible width twice, then loop by one list length
    loop_w = n * TICK_STEP
    copies = max(2, math.ceil((W - 40) / max(loop_w, 1)) + 1)
    dur = max(n * 1.6, 8)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="Arsenal com {n} ferramentas — ' + esc("; ".join(f'{c["name"]}: {", ".join(t["name"] for t in c["tools"])}' for c in cats))
         + f'. Uso no GitHub (média de {len(per_repo)} projetos): {esc(usage)}. Clique para abrir o arsenal.">',
         f"""<style>
  text {{ font-family: 'Courier New', Consolas, monospace; white-space: pre; }}
  .path {{ fill: #00C832; font-size: 13px; }}
  .cnt {{ fill: #007A1F; font-size: 12px; letter-spacing: 1px; text-anchor: end; }}
  .num {{ fill: {GREEN}; font-size: 30px; font-weight: bold; filter: url(#glow); }}
  .cn {{ fill: #E6FFE6; font-size: 13px; font-weight: bold; }}
  .cs {{ fill: #007A1F; font-size: 10px; letter-spacing: 1px; }}
  .lbl {{ fill: #00A82B; font-size: 10px; text-anchor: middle; }}
  .ul {{ fill: #007A1F; font-size: 10px; letter-spacing: 2px; }}
  .uv {{ fill: #00C832; font-size: 11px; }}
  .uvb {{ fill: {GREEN}; font-weight: bold; }}
  .cta {{ fill: {GREEN}; font-size: 15px; font-weight: bold; letter-spacing: 2px; filter: url(#glow); }}
  .ready {{ fill: #007A1F; font-size: 12px; letter-spacing: 1px; text-anchor: end; }}
  .rdot {{ fill: {RED}; animation: blink 1s steps(1) infinite; }}
  .cur {{ animation: blink 1s steps(1) infinite; }}
  .arrow {{ animation: nudge 1.4s ease-in-out infinite; }}
  .box {{ animation: pulse 3s ease-in-out infinite; }}
  .tick {{ animation: tick {dur:.1f}s linear infinite; }}
  .scan {{ animation: scan 3.5s linear infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  @keyframes nudge {{ 0%, 100% {{ transform: translateX(0); }} 50% {{ transform: translateX(5px); }} }}
  @keyframes pulse {{ 0%, 100% {{ stroke-opacity: .3; }} 50% {{ stroke-opacity: .85; }} }}
  @keyframes tick {{ from {{ transform: translateX(0); }} to {{ transform: translateX(-{loop_w}px); }} }}
  @keyframes scan {{ from {{ transform: translateY(-40px); }} to {{ transform: translateY({H}px); }} }}
</style>
<defs>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="1.6" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <linearGradient id="fl" x1="0" x2="1"><stop offset="0" stop-color="#050805"/><stop offset="1" stop-color="#050805" stop-opacity="0"/></linearGradient>
  <linearGradient id="fr" x1="1" x2="0"><stop offset="0" stop-color="#050805"/><stop offset="1" stop-color="#050805" stop-opacity="0"/></linearGradient>
  <linearGradient id="tg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{GREEN}" stop-opacity=".09"/><stop offset="1" stop-color="{GREEN}" stop-opacity=".01"/>
  </linearGradient>
  <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{GREEN}" stop-opacity="0"/><stop offset="1" stop-color="{GREEN}" stop-opacity=".08"/>
  </linearGradient>
  <clipPath id="c"><rect x="1" y="1" width="{W-2}" height="{H-8}" rx="10"/></clipPath>
  <clipPath id="tk"><rect x="20" y="104" width="{W-40}" height="68"/></clipPath>
  <clipPath id="ub"><rect x="{UBX}" y="182" width="0" height="8" rx="2">
    <animate attributeName="width" from="0" to="{UBW}" begin=".4s" dur="1.2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .7 .3 1"/></rect></clipPath>
</defs>""",
         f'<rect x=".5" y=".5" width="{W-1}" height="{H-7}" rx="10" fill="#050805" stroke="{GREEN}" stroke-opacity=".6"/>',
         f'<path d="M1 38 H{W-1}" stroke="{GREEN}" stroke-opacity=".25" stroke-dasharray="4 4"/>',
         f'<circle cx="22" cy="20" r="5" fill="{RED}" opacity=".9"/><circle cx="40" cy="20" r="5" fill="{GREEN}" opacity=".5"/>'
         f'<circle cx="58" cy="20" r="5" fill="{GREEN}" opacity=".2"/>',
         '<text x="80" y="24" class="path">~/stack/arsenal</text>',
         f'<text x="{W-20}" y="24" class="cnt">{n} FERRAMENTAS · {len(cats)} CATEGORIAS</text>']

    # one counter per category
    gap = 14
    bw = (W - 40 - gap * (len(cats) - 1)) / max(len(cats), 1)
    for i, c in enumerate(cats):
        x = 20 + i * (bw + gap)
        o.append(f'<rect class="box" style="animation-delay:{i * .6:.1f}s" x="{x:.1f}" y="48" width="{bw:.1f}" height="46" rx="8" '
                 f'fill="url(#tg)" stroke="{GREEN}"/>')
        o.append(f'<path d="M{x + 6:.1f} 60V54h6M{x + bw - 12:.1f} 54h6v6M{x + 6:.1f} 82v6h6M{x + bw - 12:.1f} 88h6v-6" '
                 f'stroke="{GREEN}" stroke-width="1.5" fill="none"/>')
        o.append(f'<text x="{x + 18:.1f}" y="82" class="num">{len(c["tools"]):02d}</text>')
        o.append(f'<text x="{x + 70:.1f}" y="69" class="cn">{esc(c["name"])}/</text>')
        o.append(f'<text x="{x + 70:.1f}" y="84" class="cs">{len(c["tools"])} módulo{"s" if len(c["tools"]) != 1 else ""}</text>')

    # endless ticker with every tool
    o.append(f'<path d="M20 104 H{W-20} M20 172 H{W-20}" stroke="{GREEN}" stroke-opacity=".12" stroke-dasharray="2 4"/>')
    o.append('<g clip-path="url(#tk)"><g class="tick">')
    for r in range(copies):
        for i, t in enumerate(tools):
            x = 20 + (r * n + i) * TICK_STEP + (TICK_STEP - TICK_T) / 2
            cx = x + TICK_T / 2
            o.append(f'<rect x="{x:.1f}" y="110" width="{TICK_T}" height="{TICK_T}" rx="8" fill="{GREEN}" fill-opacity=".05" stroke="{GREEN}" stroke-opacity=".35"/>'
                     f'<g filter="url(#glow)" transform="translate({cx - 12:.1f} 118)"><path d="{icons[t["icon"]]}" fill="{GREEN}"/></g>'
                     f'<text x="{cx:.1f}" y="164" class="lbl">{esc(t["name"])}</text>')
    o.append('</g></g>')
    o.append(f'<rect x="20" y="104" width="70" height="68" fill="url(#fl)"/><rect x="{W-90}" y="104" width="70" height="68" fill="url(#fr)"/>')

    # real usage bar (GitHub, average per project)
    o.append('<text x="20" y="190" class="ul">USO NO GITHUB</text>')
    o.append(f'<rect x="{UBX}" y="182" width="{UBW}" height="8" rx="2" fill="{GREEN}" fill-opacity=".08"/>')
    o.append('<g clip-path="url(#ub)">')
    x = float(UBX)
    tot = sum(sh for _, sh, _ in top) or 1
    for i, (name, sh, _) in enumerate(top):
        wv = UBW * sh / tot
        o.append(f'<rect x="{x:.1f}" y="182" width="{max(wv - 2, 1):.1f}" height="8" fill="{RED if i == 0 else SHADES[min(i, len(SHADES) - 1)]}"/>')
        x += wv
    o.append('</g>')
    parts = [f'{esc(name.lower())} <tspan class="uvb">{sh * 100:.0f}%</tspan>' for name, sh, _ in top]
    o.append(f'<text x="{UBX + UBW + 14}" y="190" class="uv">{" · ".join(parts) if parts else "sem dados ainda"}</text>')

    # call to action
    fy = H - 52
    o.append(f'<path d="M20 {fy} H{W-20}" stroke="{GREEN}" stroke-opacity=".15"/>')
    o.append(f'<g class="arrow"><path d="M24 {fy + 11} l8 6 -8 6z" fill="{GREEN}"/></g>')
    o.append(f'<text x="42" y="{fy + 23}" class="cta">ABRIR O ARSENAL</text>')
    o.append(f'<rect class="cur" x="{42 + 15 * 11 + 4}" y="{fy + 10}" width="8" height="15" fill="{GREEN}"/>')
    o.append(f'<text x="{W-20}" y="{fy + 22}" class="ready">SYS.READY <tspan class="rdot">●</tspan></text>')
    o.append(f'<g clip-path="url(#c)"><rect class="scan" width="{W}" height="40" fill="url(#sg)"/></g>')
    o.append('</svg>')
    return "\n".join(o) + "\n"


def main():
    user, out = sys.argv[1], pathlib.Path(sys.argv[2])
    per_repo = collect(user)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(per_repo), encoding="utf-8")
    print(f"wrote {out}: {len(per_repo)} repos with code, "
          + ", ".join(f"{name} {sh * 100:.1f}% ({c} repos)" for name, sh, c in shares(per_repo)[:TOP]))


if __name__ == "__main__":
    main()
