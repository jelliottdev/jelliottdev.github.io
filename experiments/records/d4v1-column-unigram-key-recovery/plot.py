"""Small diagram showing which source-key outputs recovered one planted passage."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render():
    data = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    count = len(data["rows"])
    powered = data["powered_rows"]
    hits = data["english_line_hits_powered"]
    assert count == 165 and powered == 107 and hits == 0
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 226" role="img" aria-labelledby="title desc">
<title id="title">Fixed-period column solver: 165 outputs, 107 recovered the planted passage</title>
<desc id="desc">The original source key inference was applied to three fixed key lengths on 55 pages. One known reading, fitted to each page length, was recovered in 107 of 165 settings and not recovered in 58. None of the 107 corresponding LP2 outputs crossed the separately declared English threshold.</desc>
<rect width="340" height="226" fill="#f3f5f6"/>
<g font-family="Arial,sans-serif" fill="#263f54">
<text x="18" y="28" font-size="16" font-weight="700">One planted-text check</text>
<text x="18" y="55" font-size="13">55 pages × 3 fixed key lengths</text>
<rect x="18" y="65" width="304" height="18" rx="4" fill="#d1d8dd"/>
<text x="18" y="105" font-size="15" font-weight="700">{count} LP2 outputs scored</text>
<rect x="18" y="116" width="304" height="18" rx="4" fill="#d1d8dd"/>
<rect x="18" y="116" width="{304 * powered / count:.1f}" height="18" rx="4" fill="#597c91"/>
<text x="18" y="156" font-size="15" font-weight="700">{powered} recovered the planted text</text>
<text x="18" y="181" font-size="15" font-weight="700">{hits} of those crossed the English line</text>
<text x="18" y="208" font-size="13">58 did not recover this planted text</text>
</g></svg>
'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    file = HERE / "summary.svg"
    svg = render()
    if args.check:
        assert file.read_text(encoding="utf-8") == svg
        print("Figure matches complete results")
    else:
        file.write_text(svg, encoding="utf-8", newline="\n")
