"""Render the fixed missing-prime histograms as a small archival SVG."""

import argparse
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "results.json"
OUTPUT = HERE / "missing-primes.svg"


def chart():
    report = json.loads(SOURCE.read_text(encoding="utf-8"))
    models = (("global_digit_shuffle", "Global shuffle", "#345a70"),
              ("within_row_digit_shuffle", "Within-row shuffle", "#9b8e7b"))
    plot_x, plot_y, plot_w, plot_h = 62, 48, 652, 226
    top = 36
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 350" role="img" aria-labelledby="title desc">',
             '<title id="title">Missing prime values under two shuffled-grid controls</title>',
             '<desc id="desc">The observed grid misses three of 49 possible prime values. Across 5,000 global shuffles and 5,000 within-row shuffles, zero to eight values are missing; three is common in both controls.</desc>',
             '<rect width="760" height="350" fill="#fff"/>',
             '<text x="62" y="26" font-family="Georgia,serif" font-size="18" fill="#222">Missing prime values in 5,000 grids per control</text>']
    # The observed value gets a quiet background band, not a third data series.
    group = plot_w / 9
    observed_x = plot_x + 3 * group
    parts.append(f'<rect x="{observed_x:.1f}" y="{plot_y}" width="{group:.1f}" height="{plot_h}" fill="#f3f4ef"/>')
    for percent in (0, 10, 20, 30):
        y = plot_y + plot_h - plot_h * percent / top
        parts.extend((f'<line x1="{plot_x}" y1="{y:.1f}" x2="{plot_x+plot_w}" y2="{y:.1f}" stroke="#d9dbda"/>',
                      f'<text x="53" y="{y+4:.1f}" text-anchor="end" font-family="Arial,sans-serif" font-size="11" fill="#555">{percent}%</text>'))
    for number in range(9):
        x = plot_x + number * group
        for model_index, (key, _label, color) in enumerate(models):
            count = report["controls"][key]["missing_primes"]["histogram"].get(str(number), 0)
            height = plot_h * (100 * count / 5000) / top
            bar_x = x + 12 + model_index * 22
            parts.append(f'<rect x="{bar_x:.1f}" y="{plot_y+plot_h-height:.1f}" width="19" height="{height:.1f}" fill="{color}"/>')
        parts.append(f'<text x="{x+group/2:.1f}" y="292" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#333">{number}</text>')
    parts.extend((f'<text x="{observed_x+group/2:.1f}" y="{plot_y+15}" text-anchor="middle" font-family="Arial,sans-serif" font-size="10" fill="#555">observed</text>',
                  '<text x="388" y="316" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#333">Number absent from the 49-value universe</text>'))
    for index, (_key, label, color) in enumerate(models):
        x = 467 + 145 * index
        parts.extend((f'<rect x="{x}" y="32" width="12" height="12" fill="{color}"/>',
                      f'<text x="{x+17}" y="42" font-family="Arial,sans-serif" font-size="10" fill="#333">{html.escape(label)}</text>'))
    parts.append('</svg>')
    return '\n'.join(parts) + '\n'


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = chart()
    if args.check:
        if OUTPUT.read_text(encoding="utf-8") != content:
            raise SystemExit("Published chart does not match the results")
        print("PASS: missing-prime chart matches the fixed control histograms")
    elif args.write:
        OUTPUT.write_text(content, encoding="utf-8", newline="\n")
        print("Wrote", OUTPUT)
    else:
        print(content, end="")
