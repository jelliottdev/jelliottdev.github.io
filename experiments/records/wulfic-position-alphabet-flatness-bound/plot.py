"""Phone-readable visual of the source's two excluded-class boundaries."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render() -> str:
    r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert (r["source_pooled_excluded_v_max"], r["source_sectioned_excluded_v_max"]) == (168, 174)
    bars = (("One alphabet set", 168, 106), ("Fresh set per section", 174, 173))
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 280" role="img" aria-labelledby="title desc">',
        '<title id="title">Stage T excluded effective-class bounds</title>',
        '<desc id="desc">The source model excludes up to 168 effective key classes in the pooled test and up to 174 in the eight-section test. These are conditional bounds, not a count of solved settings.</desc>',
        '<rect width="340" height="280" fill="#f5f6f7"/>',
        '<text x="16" y="30" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="#20262b">Alphabet-class bound</text>',
        '<text x="16" y="54" font-family="Arial,sans-serif" font-size="14" fill="#4a545c">Original rule · lower-tail P ≤ 0.0001</text>',
    ]
    for label, value, y in bars:
        width = round(value * 275 / 200)
        out += [
            f'<text x="16" y="{y}" font-family="Arial,sans-serif" font-size="15" fill="#20262b">{label}</text>',
            f'<rect x="16" y="{y+11}" width="275" height="17" fill="#dce2e6"/>',
            f'<rect x="16" y="{y+11}" width="{width}" height="17" fill="#35627a"/>',
            f'<text x="296" y="{y+26}" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="#20262b">{value}</text>',
        ]
    out += [
        '<line x1="16" y1="226" x2="324" y2="226" stroke="#c6cdd2"/>',
        '<text x="16" y="249" font-family="Arial,sans-serif" font-size="13" fill="#4a545c">Only for independent random alphabets</text>',
        '<text x="16" y="267" font-family="Arial,sans-serif" font-size="13" fill="#4a545c">per key class; not a cipher identification.</text>',
        '</svg>',
    ]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    expected = render()
    path = HERE / "comparison.svg"
    if sys.argv[1:] == ["--check"]:
        assert path.read_text(encoding="utf-8") == expected
        print("Stage T figure: OK")
    elif not sys.argv[1:]:
        path.write_text(expected, encoding="utf-8", newline="\n")
    else:
        raise SystemExit("Usage: plot.py [--check]")
