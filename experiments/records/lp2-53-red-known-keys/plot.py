"""Draw the score-control comparison as a compact SVG."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULT = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
CTRL = json.loads((HERE / "controls.json").read_text(encoding="utf-8"))


def x(score):
    return 24 + (score + 7.2) / 3.4 * 272


def render():
    null = sorted(RESULT["null_maxima"])
    lo, med, hi = null[49], null[499], null[949]
    known = [row["source_score"] for row in CTRL["rows"]]
    best = RESULT["best_score"]
    threshold = RESULT["score_threshold"]
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 410" role="img" aria-labelledby="title desc">',
        '<title id="title">LP2-53 red passage: known-key score comparison</title>',
        '<desc id="desc">The best score from 42 known-key settings is near the median maximum from 999 shuffled red passages and below the fixed English-score threshold. Nine known readings score above the threshold.</desc>',
        '<style>text{font-family:Arial,sans-serif;fill:#24313b} .sm{font-size:15px} .label{font-size:16px;font-weight:600} .title{font-size:17px;font-weight:700} .guide{stroke:#d6dce0;stroke-width:1}</style>',
        '<rect width="320" height="410" fill="#fff"/>',
        '<text x="16" y="26" class="title">51 red runes · 42 settings</text>',
        '<text x="16" y="51" class="sm">Higher score means closer to</text>',
        '<text x="16" y="70" class="sm">the known English readings.</text>',
    ]
    for tick in [-7, -6, -5, -4]:
        px = x(tick)
        svg += [f'<line x1="{px:.1f}" y1="110" x2="{px:.1f}" y2="339" class="guide"/>',
                f'<text x="{px:.1f}" y="102" text-anchor="middle" class="sm">{tick:g}</text>']
    svg += [
        '<text x="16" y="143" class="label">Shuffled best scores</text>',
        f'<text x="16" y="163" class="sm">999 controls · {lo:.2f} to {hi:.2f}</text>',
        f'<line x1="{x(lo):.1f}" y1="183" x2="{x(hi):.1f}" y2="183" stroke="#8595a0" stroke-width="12" stroke-linecap="round"/>',
        f'<circle cx="{x(med):.1f}" cy="183" r="5" fill="#24313b"/>',
        '<text x="16" y="219" class="label">Best red decode</text>',
        f'<circle cx="{x(best):.1f}" cy="242" r="8" fill="#315c73"/>',
        f'<text x="{x(best)+13:.1f}" y="247" class="sm">{best:.2f}</text>',
        '<text x="16" y="280" class="label">Nine known readings</text>',
        f'<text x="16" y="303" class="sm">{min(known):.2f} to {max(known):.2f}</text>',
        f'<line x1="{x(min(known)):.1f}" y1="326" x2="{x(max(known)):.1f}" y2="326" stroke="#315c73" stroke-width="12" stroke-linecap="round"/>',
        *[f'<line x1="{x(threshold):.1f}" y1="{top}" x2="{x(threshold):.1f}" y2="{bottom}" stroke="#9a3f3f" stroke-width="2" stroke-dasharray="5 4"/>'
          for top, bottom in ((174, 199), (232, 255), (315, 339))],
        '<text x="16" y="370" class="sm">Dashed line: English cutoff −5.5</text>',
        '<text x="16" y="395" class="sm">Black dot: shuffled median</text>',
        '</svg>\n'
    ]
    return "".join(svg)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    path = HERE / "scores.svg"
    if args.check:
        assert path.read_text(encoding="utf-8") == render()
    else:
        path.write_text(render(), encoding="utf-8", newline="\n")
    print("Verified score figure" if args.check else "Wrote score figure")
