"""Compact mobile figure for the bounded positional totient screen."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render():
    data = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    controls = [x["direct_score"] for x in data["controls"]["rows"]]
    observed = data["best"]["score"]
    null = sorted(data["null_maxima"])
    threshold = -5.5
    left, right = -7.5, -3.5
    x = lambda value: 34 + (value - left) / (right - left) * 272
    rows = [
        ("Known readings · 9", min(controls), max(controls), "#315f79", 58),
        ("Best LP2 output", observed, observed, "#263f54", 122),
        ("Shuffle maxima · 199", null[0], null[-1], "#8b989f", 186),
    ]
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 266" role="img" aria-labelledby="title desc">',
         '<title id="title">Positional totient whole-page scores</title>',
         '<desc id="desc">Nine known readings clear the English score line; the strongest of 5,500 LP2 outputs is below it and typical of complete-search shuffles.</desc>',
         '<rect width="340" height="266" fill="#f3f5f6"/>',
         '<g font-family="Arial,sans-serif" fill="#263f54">',
         '<text x="18" y="26" font-size="16" font-weight="700">Known text vs LP2</text>',
         '<text x="18" y="45" font-size="13">Higher score is more English-like</text>']
    for label, lo, hi, color, y in rows:
        s.append(f'<text x="18" y="{y}" font-size="13" font-weight="600">{label}</text>')
        s.append(f'<line x1="{x(lo):.1f}" y1="{y+21}" x2="{x(hi):.1f}" y2="{y+21}" stroke="{color}" stroke-width="8" stroke-linecap="round"/>')
        s.append(f'<circle cx="{x(hi):.1f}" cy="{y+21}" r="6" fill="{color}"/>')
    s.append(f'<line x1="{x(threshold):.1f}" y1="46" x2="{x(threshold):.1f}" y2="219" stroke="#526b7c" stroke-dasharray="5 4"/>')
    s.append(f'<text x="{x(threshold)-54:.1f}" y="236" font-size="13">English line −5.5</text>')
    s.append('<text x="18" y="256" font-size="13">LP2 best: −6.60 · shuffle tail: 88 / 200</text></g></svg>')
    return '\n'.join(s) + '\n'


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = HERE / "summary.svg"
    svg = render()
    if args.check:
        assert path.read_text(encoding="utf-8") == svg
        print("Figure matches results")
    else:
        path.write_text(svg, encoding="utf-8", newline="\n")
