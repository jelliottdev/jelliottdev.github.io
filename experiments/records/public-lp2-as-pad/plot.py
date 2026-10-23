"""Draw the five target maxima and the published advancement bar."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULT = HERE / "source/liber-primus/analysis/round16/F-01/results.json"
LABELS = {
    "T1_cicada_2012_2013": "2012–13 puzzle texts",
    "T2_lp1_solved": "Solved LP1 text",
    "T3_pgp_messages": "PGP message text",
    "T4_anend_hash": "AN END byte sequence",
    "T6_lp2_head_200": "LP2 opening",
}


def make() -> None:
    rows = json.loads(RESULT.read_text(encoding="utf-8"))["results"]
    best = {target: max(r["score"] for r in rows if r["target"] == target)
            for target in LABELS}
    left, width = 260, 500
    # Stronger scores are farther right; the fixed bar remains visible.
    scale = lambda s: left + (s + 8.5) / 3.5 * width
    bar_x = scale(-5.5)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" role="img" '
             f'aria-labelledby="title desc" viewBox="0 0 820 392">',
             '<title id="title">LP2 as a running key: best scores by target</title>',
             '<desc id="desc">All five best scores are below the advancement bar. '
             'The 2012 to 2013 texts rank highest at minus 7.032, while the bar is minus 5.5.</desc>',
             '<rect width="820" height="392" fill="white"/>',
             '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#25333e}'
             '.small{font-size:13px}.label{font-size:15px}.value{font-size:14px;font-weight:700}'
             '</style>',
             '<text x="24" y="35" font-size="20" font-weight="700">Best score for each target</text>',
             '<text x="24" y="60" class="small">Higher is stronger · five targets × eight key/sign combinations</text>',
             f'<line x1="{bar_x:.1f}" y1="85" x2="{bar_x:.1f}" y2="330" stroke="#71828d" stroke-width="2" stroke-dasharray="5 4"/>',
             f'<text x="{bar_x-7:.1f}" y="78" text-anchor="end" class="small">advancement bar −5.5</text>']
    for i, (target, score) in enumerate(best.items()):
        y = 110 + i * 48
        x = scale(score)
        parts.extend([f'<text x="24" y="{y+7}" class="label">{escape(LABELS[target])}</text>',
                      f'<line x1="{left}" y1="{y}" x2="{bar_x:.1f}" y2="{y}" stroke="#e1e7ea" stroke-width="12"/>',
                      f'<line x1="{left}" y1="{y}" x2="{x:.1f}" y2="{y}" stroke="#315f78" stroke-width="12"/>',
                      f'<circle cx="{x:.1f}" cy="{y}" r="6" fill="#315f78"/>',
                      f'<text x="{x+14:.1f}" y="{y+5}" class="value">{score:.3f}</text>'])
    parts.extend(['<text x="24" y="369" class="small">Comparison scores use the source’s English quadgram model; they do not prove a general impossibility.</text>', '</svg>'])
    (HERE / "scores.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")


if __name__ == "__main__":
    make()
