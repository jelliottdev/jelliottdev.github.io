"""Small mobile chart of the section-relative modulo-seven example."""
import json
from pathlib import Path

here = Path(__file__).resolve().parent
r = json.loads((here / "results.json").read_text(encoding="utf-8"))
actual = r["observed"]["7"]["counts"]
expected = r["expected_counts"]["7"]
bars = []
for i, (count, mean) in enumerate(zip(actual, expected)):
    x = 25 + 47 * i
    height = count * 7
    bars.append(f'<rect x="{x}" y="{184-height}" width="28" height="{height}" fill="#3b6476"/><text x="{x+14}" y="{178-height}" text-anchor="middle" font-size="12">{count}</text><text x="{x+14}" y="204" text-anchor="middle" font-size="12">{i}</text>')
avg = sum(expected) / len(expected)
yline = 184 - avg * 7
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 240" role="img" aria-labelledby="title desc"><title id="title">Doublet positions modulo seven</title><desc id="desc">The seven observed counts are {', '.join(map(str,actual))}. The expected count per remainder is near 12.3. The strongest of seven tested moduli is ordinary under controls.</desc><rect width="360" height="240" fill="#f4f6f7"/><g fill="#20333d" font-family="system-ui, sans-serif"><text x="14" y="28" font-size="17" font-weight="700">Where do doublets land?</text><text x="14" y="48" font-size="12">Section position, remainder after ÷ 7</text><line x1="16" x2="344" y1="{yline:.1f}" y2="{yline:.1f}" stroke="#8b6a54" stroke-width="1.5" stroke-dasharray="4 3"/>{''.join(bars)}<text x="14" y="229" font-size="12">Dashed line: expected ≈ {avg:.1f} in each group</text></g></svg>'''
(here / "residues.svg").write_text(svg + "\n", encoding="utf-8", newline="\n")
