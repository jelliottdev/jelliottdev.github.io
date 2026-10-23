"""Render phone-width score comparison for the frozen PGP-material grid."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render():
    d = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    rows = d["stream_maxima"]
    assert len(rows) == 4 and d["case_count"] == 119900
    labels = ("Primary packet", "Primary fingerprint", "Subkey packet", "Subkey fingerprint")
    bars = []
    left, span = 18, 304
    low, high = -7.1, -5.5
    for i, (label, row) in enumerate(zip(labels, rows)):
        y = 100 + 52 * i
        value = row["score"]
        width = max(0, min(span, span * (value - low) / (high - low)))
        bars.append(f'<text x="{left}" y="{y}" class="label">{label}</text>'
                    f'<rect x="{left}" y="{y + 7}" width="{span}" height="12" fill="#e9edef"/>'
                    f'<rect x="{left}" y="{y + 7}" width="{width:.2f}" height="12" fill="#49758b"/>'
                    f'<text x="322" y="{y}" text-anchor="end" class="small">{value:.2f}</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 356" role="img" aria-labelledby="title desc">
<title id="title">No PGP packet or fingerprint key reached the English gate</title>
<desc id="desc">Four groups of candidate repeating keys all scored below the predeclared minus 5.5 threshold. Of 199 full-search shuffled controls, 174 had a maximum at least as high as the observed best.</desc>
<style>.head{{font:700 17px Arial,sans-serif;fill:#172b36}}.label{{font:14px Arial,sans-serif;fill:#243c49}}.small{{font:13px Arial,sans-serif;fill:#435763}}</style>
<rect width="340" height="356" fill="#f8f9fa"/>
<text x="18" y="27" class="head">Four key materials, one rule</text>
<text x="18" y="47" class="small">Higher scores are more English-like</text>
<text x="18" y="76" class="small">−7.1</text><text x="322" y="76" text-anchor="end" class="small">−5.5 threshold</text>
{''.join(bars)}
<line x1="18" y1="294" x2="322" y2="294" stroke="#bdc8ce"/>
<text x="18" y="318" class="label">No output reached −5.5</text>
<text x="18" y="340" class="small">174 of 199 shuffled searches scored higher.</text>
</svg>'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    image = render()
    path = HERE / "scores.svg"
    if args.check:
        assert path.read_text(encoding="utf-8") == image
        print("PASS: score figure matches saved results")
    else:
        path.write_text(image, encoding="utf-8", newline="\n")
        print(path)
