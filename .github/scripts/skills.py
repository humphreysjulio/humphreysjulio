"""Generate the arsenal window (skills.svg): every tool from arsenal.json as a card,
grouped by category. The window grows with the number of tools.

usage: python skills.py <output.svg>
"""
import html
import json
import pathlib
import sys

DATA = json.loads((pathlib.Path(__file__).parent / "arsenal.json").read_text(encoding="utf-8"))
GREEN, RED = "#00FF41", "#FF1A3C"
W = 830
TW, TH, GAP, X0, PER_ROW = 185, 91, 16.67, 20, 4
LABEL, ROW = 26, 91 + 16


def render():
    cats = DATA["categories"]
    icons = DATA["icons"]
    n = sum(len(c["tools"]) for c in cats)
    heights = [LABEL + ((len(c["tools"]) + PER_ROW - 1) // PER_ROW) * ROW for c in cats]
    H = 54 + sum(heights) + 4
    esc = html.escape
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="~/arsenal — ' + esc("; ".join(f'{c["name"]}: {", ".join(t["name"] for t in c["tools"])}' for c in cats)) + '">',
         f"""<style>
  text {{ font-family: 'Courier New', Consolas, monospace; white-space: pre; }}
  .path {{ fill: #00C832; font-size: 13px; }}
  .cnt {{ fill: {RED}; font-size: 12px; letter-spacing: 1px; text-anchor: end; }}
  .cat {{ fill: {GREEN}; font-size: 13px; font-weight: bold; }}
  .tree {{ fill: {RED}; font-size: 13px; }}
  .mods {{ fill: #007A1F; font-size: 11px; letter-spacing: 1px; }}
  .name {{ fill: #E6FFE6; font-size: 15px; font-weight: bold; }}
  .tag {{ fill: #00A82B; font-size: 10px; letter-spacing: 1px; }}
  .desc {{ fill: #00C832; font-size: 11px; }}
  .st {{ fill: {GREEN}; font-size: 11px; font-weight: bold; letter-spacing: 1px; }}
  .tile {{ animation: pulse 3s ease-in-out infinite; }}
  .ico {{ filter: url(#glow); }}
  .cur {{ animation: blink 1s steps(1) infinite; }}
  .scan {{ animation: scan 5s linear infinite; }}
  @keyframes pulse {{ 0%, 100% {{ stroke-opacity: .25; }} 50% {{ stroke-opacity: .9; }} }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  @keyframes scan {{ from {{ transform: translateY(-40px); }} to {{ transform: translateY({H}px); }} }}
</style>
<defs>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="1.6" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{GREEN}" stop-opacity="0"/><stop offset="1" stop-color="{GREEN}" stop-opacity=".10"/>
  </linearGradient>
  <linearGradient id="tg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{GREEN}" stop-opacity=".09"/><stop offset="1" stop-color="{GREEN}" stop-opacity=".01"/>
  </linearGradient>
  <clipPath id="c"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10"/></clipPath>
</defs>""",
         f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="#050805" stroke="{GREEN}" stroke-opacity=".6"/>',
         f'<path d="M1 40 H{W-1}" stroke="{GREEN}" stroke-opacity=".25" stroke-dasharray="4 4"/>',
         f'<circle cx="22" cy="21" r="5" fill="{RED}" opacity=".9"/><circle cx="40" cy="21" r="5" fill="{GREEN}" opacity=".5"/>'
         f'<circle cx="58" cy="21" r="5" fill="{GREEN}" opacity=".2"/>',
         '<text x="80" y="25" class="path">~/arsenal</text>',
         f'<rect class="cur" x="{80 + 9 * 7.8 + 3:.1f}" y="13" width="7" height="14" fill="{GREEN}"/>',
         f'<text x="{W-20}" y="25" class="cnt">[{n} MODS LOADED]</text>']
    y = 54
    k = 0
    for ci, c in enumerate(cats):
        tools = c["tools"]
        last = ci == len(cats) - 1
        o.append(f'<text x="20" y="{y + 14}"><tspan class="tree">{"└──" if last else "├──"} </tspan>'
                 f'<tspan class="cat">{esc(c["name"])}/</tspan></text>')
        lx = 20 + (4 + len(c["name"]) + 1) * 7.8 + 12
        o.append(f'<text x="{lx:.1f}" y="{y + 14}" class="mods">{len(tools)} módulo{"s" if len(tools) != 1 else ""}</text>')
        for i, t in enumerate(tools):
            x = X0 + (i % PER_ROW) * (TW + GAP)
            ty = y + LABEL + (i // PER_ROW) * ROW
            delay = (k % 4) * 0.6
            k += 1
            o.append(f'<g transform="translate({x:.1f} {ty})">'
                     f'<rect class="tile" style="animation-delay:{delay:.1f}s" x=".5" y=".5" width="{TW - 1}" height="{TH}" rx="8" fill="url(#tg)" stroke="{GREEN}"/>'
                     f'<path d="M8 18V8h10M{TW - 18} 8h10v10M8 74v10h10M{TW - 18} 84h10v-10" stroke="{GREEN}" stroke-width="2" fill="none"/>'
                     f'<g class="ico" transform="translate(18 18) scale(1.2)"><path d="{icons[t["icon"]]}" fill="{GREEN}"/></g>'
                     f'<text x="58" y="33" class="name">{esc(t["name"])}</text>'
                     f'<text x="58" y="48" class="tag">{esc(t["tag"])}</text>'
                     f'<text x="18" y="74" class="desc">{esc(t["desc"])}</text>'
                     f'<circle cx="{TW - 20}" cy="70" r="3" fill="{GREEN}"><animate attributeName="opacity" values="1;.2;1" dur="1.6s" '
                     f'begin="{delay:.1f}s" repeatCount="indefinite"/></circle>'
                     f'<text x="{TW - 28}" y="74" class="st" text-anchor="end">OK</text></g>')
        y += heights[ci]
    o.append(f'<g clip-path="url(#c)"><rect class="scan" x="0" y="0" width="{W}" height="40" fill="url(#sg)"/></g>')
    o.append('</svg>')
    return "\n".join(o) + "\n"


if __name__ == "__main__":
    out = pathlib.Path(sys.argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(), encoding="utf-8")
    print(f"wrote {out}")
