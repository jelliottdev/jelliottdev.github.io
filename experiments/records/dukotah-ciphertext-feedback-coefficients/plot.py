"""Draw the coefficient-feedback plant and three LP2 page scores."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def figure():
    r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    d = json.loads((HERE / "diagnostic-results.json").read_text(encoding="utf-8"))
    pages = r["page_winners"]
    x = lambda s: 22 + (s + 7.5) / 3.5 * 278
    gate = -5.2
    lines = []
    for idx, row in enumerate(pages):
        y = 183 + idx * 33
        lines.append(f'<text x="18" y="{y}" font-size="14" fill="#24353e">LP2-{row["source_page"]:02d}</text>')
        lines.append(f'<circle cx="{x(row["rescored_exact"]):.1f}" cy="{y+13}" r="6" fill="#6a8490"/>')
        lines.append(f'<text x="{x(row["rescored_exact"])+12:.1f}" y="{y+18}" font-size="13" fill="#24353e">{row["score_rounded"]:.2f}</text>')
    plants = d["cases"]
    assert len(plants) == 2
    pscore = plants[0]["true"]["score"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 310" role="img" aria-labelledby="title desc" style="font-family:Arial,sans-serif">
<title id="title">Feedback model scores on planted and LP2 text</title>
<desc id="desc">Two known-key plants score about minus 4.13 and pass the source's minus 5.2 signal bar. Three LP2 pages score about minus 6.9 and do not pass.</desc>
<rect width="320" height="310" fill="#f4f6f7"/>
<text x="18" y="28" font-size="17" font-weight="700" fill="#202b32">A plant passes; three pages do not</text>
<text x="18" y="49" font-size="13" fill="#45545d">Higher English score is better</text>
<line x1="{x(gate):.1f}" x2="{x(gate):.1f}" y1="70" y2="275" stroke="#9e5963" stroke-width="2" stroke-dasharray="4 4"/>
<text x="{x(gate)-5:.1f}" y="83" text-anchor="end" font-size="13" fill="#8a3d48">Signal bar −5.2</text>
<text x="18" y="109" font-size="14" fill="#24353e">Known plant, seed 0</text>
<circle cx="{x(pscore):.1f}" cy="122" r="7" fill="#1d5d79"/>
<text x="{x(pscore)-9:.1f}" y="146" text-anchor="end" font-size="13" fill="#1d5d79">{pscore:.2f}</text>
<text x="18" y="165" font-size="13" fill="#45545d">Seed 1 plant also scores {plants[1]["true"]["score"]:.2f}</text>
{''.join(lines)}
<text x="18" y="291" font-size="13" fill="#45545d">Each page searched 20,288 combinations.</text>
</svg>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = HERE / "coefficient-feedback.svg"
    data = figure()
    if args.check:
        assert path.read_text(encoding="utf-8") == data
        print("PASS: SVG matches source replay")
    else:
        path.write_text(data, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
