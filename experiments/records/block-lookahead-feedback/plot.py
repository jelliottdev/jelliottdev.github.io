"""Produce a compact schematic and observed IoC comparison."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
rows = [
    ("Raw LP2", data["raw_lp2"]["ioc"], "#748992"),
    ("Decode b = 5", data["block_cases"]["5"]["decoded_ioc"], "#315d77"),
    ("Decode b = 7", data["block_cases"]["7"]["decoded_ioc"], "#315d77"),
    ("Solved LP1 reading control", data["solved_lp1"]["ioc"], "#5e717b"),
]
esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
out = ['<svg xmlns="http://www.w3.org/2000/svg" width="760" height="370" viewBox="0 0 760 370" role="img" aria-labelledby="title desc">',
       '<title id="title">Block-lookahead rule and observed index of coincidence</title>',
       '<desc id="desc">The block-start rune depends on a future plaintext rune b positions away. Decoded LP2 IoC is about 0.035 for blocks of five and seven, near raw LP2 0.0345; solved LP1 control is 0.0611.</desc>',
       '<rect width="760" height="370" fill="#f6f7f8"/>',
       '<text x="22" y="34" font-family="system-ui,sans-serif" font-size="20" font-weight="650" fill="#26343b">A lookahead only at the block start</text>',
       '<text x="22" y="60" font-family="system-ui,sans-serif" font-size="14" fill="#52616a">Illustrated for b = 5; all arithmetic is modulo 29.</text>',
       '<line x1="75" y1="121" x2="580" y2="121" stroke="#cbd5da" stroke-width="2"/>']
for k in range(6):
    x = 80 + 100 * k
    out.append(f'<circle cx="{x}" cy="121" r="21" fill="{"#315d77" if k in (0,5) else "#dce5e9"}"/>')
    out.append(f'<text x="{x}" y="127" text-anchor="middle" font-family="system-ui,sans-serif" font-size="14" font-weight="600" fill="{"white" if k in (0,5) else "#26343b"}">{"P₀" if k==0 else "P₅" if k==5 else f"P{k}"}</text>')
out += ['<path d="M580 91 C520 49 160 49 80 91" fill="none" stroke="#315d77" stroke-width="2"/>',
        '<path d="M80 91 l-6 -9 m6 9 l10 -3" fill="none" stroke="#315d77" stroke-width="2"/>',
        '<text x="320" y="79" text-anchor="middle" font-family="system-ui,sans-serif" font-size="13" fill="#315d77">C₀ = P₀ + P₅</text>',
        '<text x="22" y="176" font-family="system-ui,sans-serif" font-size="17" font-weight="650" fill="#26343b">Decoded rune distribution stays close to flat</text>',
        '<line x1="225" y1="305" x2="625" y2="305" stroke="#9eafb7" stroke-width="1"/>']
for tick in (0.03,0.04,0.05,0.06):
    x = 225 + (tick-0.03)/0.035*400
    out += [f'<line x1="{x:.1f}" y1="194" x2="{x:.1f}" y2="305" stroke="#dbe3e7" stroke-width="1"/>',
            f'<text x="{x:.1f}" y="325" text-anchor="middle" font-family="system-ui,sans-serif" font-size="12" fill="#52616a">{tick:.2f}</text>']
for i,(label,value,color) in enumerate(rows):
    y=211+i*28
    x=225+(value-0.03)/0.035*400
    out += [f'<text x="22" y="{y+5}" font-family="system-ui,sans-serif" font-size="14" fill="#26343b">{esc(label)}</text>',
            f'<circle cx="{x:.1f}" cy="{y}" r="6" fill="{color}"/>',
            f'<text x="640" y="{y+5}" font-family="system-ui,sans-serif" font-size="13" fill="#26343b">{value:.4f}</text>']
out += ['<text x="22" y="352" font-family="system-ui,sans-serif" font-size="12" fill="#52616a">The LP1 and LP2 corpora differ; this is descriptive, not a language test.</text>', '</svg>']
fresh='\n'.join(out)+'\n'
path=HERE/'lookahead-feedback.svg'
if '--check' in sys.argv:
    assert path.read_text(encoding='utf-8')==fresh
    print('Figure matches results')
else:
    path.write_text(fresh,encoding='utf-8')
    print(f'Wrote {path}')
