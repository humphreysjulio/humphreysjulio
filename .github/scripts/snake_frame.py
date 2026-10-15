"""Wrap the snk snake SVG in the profile's Matrix terminal window.

usage: python snake_frame.py <snake.svg> <output.svg>

The snake is inlined (not referenced) because GitHub renders README SVGs as
images, which cannot load other images.
"""
import pathlib
import re
import sys

W = 830
PAD = 20
BAR = 38
FOOT = 44


def main():
    src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    snake = src.read_text(encoding="utf-8")
    vb = re.search(r'viewBox="([^"]+)"', snake).group(1)
    vw, vh = (float(v) for v in vb.split()[2:])
    inner = re.search(r"<svg[^>]*>(.*)</svg>", snake, flags=re.S).group(1)
    inner = re.sub(r"<desc>.*?</desc>", "", inner, flags=re.S)

    sw = W - 2 * PAD
    sh = sw * vh / vw
    H = round(BAR + 14 + sh + FOOT)
    fy = H - 18
    legend = ["#0F2A12", "#003b00", "#006b1a", "#00a82b", "#00ff41"]
    squares = "".join(f'<rect x="{W - 150 + i * 16}" y="{fy - 10}" width="12" height="12" rx="2" fill="{c}"/>'
                      for i, c in enumerate(legend))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Cobrinha comendo o gráfico de contribuições do GitHub">
<style>
  .mx-t {{ font-family: 'Courier New', Consolas, monospace; white-space: pre; }}
  .mx-path {{ fill: #00C832; font-size: 13px; }}
  .mx-live {{ fill: #00FF41; font-size: 11px; font-weight: bold; letter-spacing: 2px; text-anchor: end; }}
  .mx-dim {{ fill: #007A1F; font-size: 11px; letter-spacing: 1px; }}
  .mx-rec {{ animation: mx-blink 1.2s steps(1) infinite; }}
  .mx-scan {{ animation: mx-scan 4s linear infinite; }}
  @keyframes mx-blink {{ 50% {{ opacity: .2; }} }}
  @keyframes mx-scan {{ from {{ transform: translateY(-30px); }} to {{ transform: translateY({H}px); }} }}
</style>
<defs>
  <linearGradient id="mx-sg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#00FF41" stop-opacity="0"/><stop offset="1" stop-color="#00FF41" stop-opacity=".07"/>
  </linearGradient>
  <clipPath id="mx-clip"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="10"/></clipPath>
</defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="#050805" stroke="#00FF41" stroke-opacity=".6"/>
<path d="M1 {BAR} H{W - 1}" stroke="#00FF41" stroke-opacity=".25" stroke-dasharray="4 4"/>
<circle cx="22" cy="20" r="5" fill="#00FF41" opacity=".9"/><circle cx="40" cy="20" r="5" fill="#00FF41" opacity=".5"/><circle cx="58" cy="20" r="5" fill="#00FF41" opacity=".2"/>
<text x="80" y="24" class="mx-t mx-path">~/activity.log — tail -f</text>
<circle class="mx-rec" cx="{W - 62}" cy="20" r="4" fill="#00FF41"/>
<text x="{W - 20}" y="24" class="mx-t mx-live">LIVE</text>
<svg x="{PAD}" y="{BAR + 14}" width="{sw}" height="{sh:.1f}" viewBox="{vb}">{inner}</svg>
<path d="M{PAD} {fy - 20} H{W - PAD}" stroke="#00FF41" stroke-opacity=".15"/>
<text x="{PAD + 6}" y="{fy}" class="mx-t mx-dim">CONTRIBUIÇÕES · ÚLTIMO ANO</text>
<text x="{W - 158}" y="{fy}" class="mx-t mx-dim" text-anchor="end">menos</text>
{squares}
<text x="{W - 64}" y="{fy}" class="mx-t mx-dim">mais</text>
<g clip-path="url(#mx-clip)"><rect class="mx-scan" width="{W}" height="30" fill="url(#mx-sg)"/></g>
</svg>
'''
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
