"""Render directly observed wrong-key scores crossing the source's reading line."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source" / "liber-primus" / "analysis" / "round19" / "I1"
OUT = HERE / "decoder-null-bars.svg"
MODES = (
    ("Drift 0", "drift_l0"),
    ("Drift 2", "drift_l2"),
    ("Drift 4", "drift_l4"),
    ("Drift 12", "drift_l12"),
    ("Repository", "repo_ms3"),
)


def render() -> str:
    rows = []
    for name in ("out_fp_deep.json", "out_fp_deep2.json", "out_fp_curve.json"):
        rows.extend(json.loads((SOURCE / name).read_text(encoding="utf-8"))["rows"])
    counts = defaultdict(lambda: [0, 0])
    for row in rows:
        if row["null"] == "real":
            bucket = counts[row["mode"]]
            bucket[0] += 1
            bucket[1] += row["score"] > -5.5
    assert all(mode in counts for _, mode in MODES)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 319" role="img" aria-labelledby="title desc" font-family="Arial, sans-serif">',
        '<title id="title">Wrong keys crossing a fixed reading line</title>',
        '<desc id="desc">Real-ciphertext wrong-key scores above minus 5.5: drift zero 500 of 500, drift two 461 of 500, drift four 230 of 2000, drift twelve zero of 2000, and repository mode zero of 2000. A crossing is not a reading.</desc>',
        '<rect width="320" height="319" fill="#fff"/>',
        '<text x="12" y="24" font-size="16" font-weight="700" fill="#222">Wrong keys above −5.5</text>',
        '<text x="12" y="46" font-size="13" fill="#4d565c">Same score line, different decoders</text>',
    ]
    for i, (label, mode) in enumerate(MODES):
        total, over = counts[mode]
        percent = over / total
        y = 72 + i * 44
        lines.extend([
            f'<text x="12" y="{y+13}" font-size="14" fill="#24323a">{label}</text>',
            f'<rect x="104" y="{y}" width="128" height="17" fill="#e5eaed"/>',
            f'<rect x="104" y="{y}" width="{128*percent:.2f}" height="17" fill="#245b78"/>',
            f'<text x="240" y="{y+14}" font-size="13" fill="#24323a">{over}/{total}</text>',
        ])
    lines.extend([
        '<text x="12" y="297" font-size="13" fill="#4d565c">Crossing this line is not a decipherment.</text>',
        '</svg>',
    ])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    svg = render()
    if args.check:
        assert OUT.read_text(encoding="utf-8") == svg
    else:
        OUT.write_text(svg, encoding="utf-8", newline="\n")
    print("PASS: responsive score figure", hashlib.sha256(svg.encode()).hexdigest())
