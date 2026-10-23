"""Small responsive comparison of the source's known-key baseline cells."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "decoder-baseline.svg"


def render() -> str:
    data = json.loads((HERE / "out_base.json").read_text(encoding="utf-8"))
    rows = {(r["L"], r["label"], r["mode"]): r for r in data["summary"]}
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 350" role="img" aria-labelledby="title desc">',
             '<title id="title">Correct-key recovery under two decoding rules</title>',
             '<desc id="desc">At 240 and 400 runes with suppression 0.83, the matching decoder recovers 100 percent; the pair-skip decoder recovers 37.9 and 41.2 percent.</desc>',
             '<rect width="340" height="350" fill="#f5f6f7"/>',
             '<g font-family="Arial, sans-serif" fill="#24323b">',
             '<text x="16" y="28" font-size="17" font-weight="700">The wrong skip rule loses text</text>',
             '<text x="16" y="50" font-size="13">Known key · synthetic ciphertext · 7 seeds each</text>']
    for L, y in ((240, 90), (400, 213)):
        parts.append(f'<text x="16" y="{y}" font-size="15" font-weight="700">{L}-rune plants</text>')
        for mode, label, dy, color in (("repo_ms3", "Matching decoder", 25, "#2c607a"),
                                       ("pair_ms8", "Pair-skip decoder", 70, "#8a5962")):
            rec = rows[(L, "keyskip supp=0.83", mode)]["median_recovery"]
            by = y + dy
            parts.append(f'<text x="16" y="{by}" font-size="13">{label}</text>')
            parts.append(f'<rect x="16" y="{by+9}" width="230" height="13" fill="#dce1e4"/>')
            parts.append(f'<rect x="16" y="{by+9}" width="{230*rec:.1f}" height="13" fill="{color}"/>')
            parts.append(f'<text x="254" y="{by+21}" font-size="14" font-weight="700">{100*rec:.1f}%</text>')
    parts.append('<text x="16" y="332" font-size="13">Recovery is exact rune agreement, not score.</text></g></svg>')
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    svg = render()
    if args.check:
        assert OUT.read_text(encoding="utf-8") == svg
    else:
        OUT.write_text(svg, encoding="utf-8", newline="\n")
