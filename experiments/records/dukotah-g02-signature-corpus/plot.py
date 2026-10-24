"""Render the pinned-versus-archived G-02 corpus comparison as a mobile-sized SVG."""

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    d = json.loads((HERE / "results.json").read_text(encoding="utf-8"))["independent_check"]
    rows = [
        ("Archived only", d["paths_only_archived"], "#8394a2"),
        ("In both", d["paths_common"], "#356f91"),
        ("Pinned only", d["paths_only_fresh"], "#aab5bd"),
    ]
    assert rows[0][1] + rows[1][1] == d["archived_files_scanned"]
    assert rows[1][1] + rows[2][1] == d["fresh_files_scanned"]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 226" role="img" '
             'aria-labelledby="title desc">',
             '<title id="title">The archived and pinned signature corpora overlap</title>',
             '<desc id="desc">105 archived-only paths, 123 shared paths, 10 pinned-only paths. '
             'Every shared path has the same source-program verdict and extracted timestamp.</desc>',
             '<rect width="320" height="226" fill="#f7f9fa"/>',
             '<text x="16" y="27" font-family="Arial,sans-serif" font-size="17" '
             'font-weight="700" fill="#1d2c35">Two snapshots, one shared core</text>']
    for i, (label, n, color) in enumerate(rows):
        y = 64 + i * 47
        width = max(5, round(135 * n / 123))
        parts.extend([
            f'<text x="16" y="{y+15}" font-family="Arial,sans-serif" font-size="13" fill="#34444e">{label}</text>',
            f'<rect x="126" y="{y}" width="{width}" height="20" rx="3" fill="{color}"/>',
            f'<text x="294" y="{y+16}" text-anchor="end" font-family="Arial,sans-serif" '
            f'font-size="15" font-weight="700" fill="#1d2c35">{n}</text>',
        ])
    parts.append('<text x="16" y="216" font-family="Arial,sans-serif" font-size="13" '
                 'fill="#43535e">Shared: same source result and time</text>')
    parts.append('</svg>')
    svg = "\n".join(parts) + "\n"
    path = HERE / "corpus-overlap.svg"
    if args.check:
        assert path.read_text(encoding="utf-8") == svg
        print("PASS: chart matches results")
    else:
        path.write_text(svg, encoding="utf-8", newline="\n")
        print(path)


if __name__ == "__main__":
    main()
