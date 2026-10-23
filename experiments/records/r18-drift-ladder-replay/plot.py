"""Render a compact, readable comparison of the planted and real ladder scores."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def make():
    control = json.loads((HERE / "replayed-b4_control.json").read_text(encoding="utf-8"))
    ladder = json.loads((HERE / "replayed-b4_ladder.json").read_text(encoding="utf-8"))
    best = max((r["best"] for r in ladder["rows"]), key=lambda x: x[0])
    corrected = max((x for r in ladder["rows"] for x in r["top8"] if x[4] == "corrected"),
                    key=lambda x: x[0])
    x = lambda score: 128 + (score + 8) * 37
    rows = []
    for i, r in enumerate(control["results"]):
        pg = r["page"] + (1 if r["page"] >= 50 else 0)
        yy = 111 + i * 65
        rows.append(f'<text x="16" y="{yy}" font-size="13" fill="#26333c">LP2-{pg:02}</text>')
        rows.append(f'<line x1="128" y1="{yy-4}" x2="302" y2="{yy-4}" stroke="#d8e0e5"/>')
        for score, color, label, dy in (
            (r["score_at_true_offset"], "#216f88", "correct", -17),
            (r["score_at_uncorrected_start"], "#a15c4f", "uncorrected", 13),
        ):
            rows.append(f'<circle cx="{x(score):.1f}" cy="{yy-4}" r="5" fill="{color}"/>')
            rows.append(f'<text x="{x(score):.1f}" y="{yy+dy}" text-anchor="middle" font-size="13" fill="{color}">{score:.2f}</text>')
    best_page = best[1] + (1 if best[1] >= 50 else 0)
    corrected_page = corrected[1] + (1 if corrected[1] >= 50 else 0)
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 490" role="img" aria-labelledby="title desc" font-family="Arial,sans-serif">',
        '<title id="title">Planted-key recovery and real LP2 offset search</title>',
        '<desc id="desc">A planted correct key ranks first at the drift-corrected offset on three pages. The real-data search has no candidate above the declared minus 5.5 score bar.</desc>',
        '<rect width="320" height="490" fill="#f7f8fa"/>',
        '<text x="16" y="27" font-family="Arial,sans-serif" font-size="17" font-weight="700" fill="#26333c">Correcting the key position</text>',
        '<text x="16" y="51" font-family="Arial,sans-serif" font-size="13" fill="#54636d">Higher reading score is better</text>',
        '<text x="16" y="83" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="#26333c">Planted key · same 100 runes</text>',
        *rows,
        '<circle cx="21" cy="310" r="5" fill="#216f88"/>',
        '<text x="34" y="315" font-family="Arial,sans-serif" font-size="13" fill="#26333c">drift-corrected</text>',
        '<circle cx="177" cy="310" r="5" fill="#a15c4f"/>',
        '<text x="190" y="315" font-family="Arial,sans-serif" font-size="13" fill="#26333c">uncorrected</text>',
        '<line x1="16" y1="331" x2="304" y2="331" stroke="#cbd5db"/>',
        '<text x="16" y="355" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="#26333c">Real LP2 · 230 mined keys</text>',
        f'<text x="16" y="382" font-family="Arial,sans-serif" font-size="13" fill="#26333c">Best corrected: {corrected[0]:.2f} · LP2-{corrected_page:02}</text>',
        f'<text x="16" y="407" font-family="Arial,sans-serif" font-size="13" fill="#26333c">Best overall: {best[0]:.2f} · LP2-{best_page:02}</text>',
        '<text x="16" y="432" font-family="Arial,sans-serif" font-size="13" fill="#26333c">Declared bar: −5.50 · no score passes</text>',
        '<text x="16" y="464" font-family="Arial,sans-serif" font-size="13" fill="#56636b">Source ordinal 52 maps to LP2-53.</text>',
        '</svg>',
    ]
    return "\n".join(svg) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = HERE / "drift-ladder.svg"
    contents = make()
    if args.check:
        assert path.read_text(encoding="utf-8") == contents
        print("PASS: SVG reproduces the replayed planted and real-data scores")
    else:
        path.write_text(contents, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
