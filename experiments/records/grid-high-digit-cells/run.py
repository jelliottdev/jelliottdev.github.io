"""Audit the LP2-49–51 4-prefix cells and one fixed spatial control."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "exports/alphanumeric-grids.json"
PLAN = HERE / "plan.json"
OUTPUT = HERE / "results.json"
FIGURE = HERE / "cells.svg"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(locations):
    selected = set(locations)
    blocks = [sum(8 * block <= position // 8 < 8 * block + 8 for position in selected)
              for block in range(4)]
    touching = sum((position + 1 in selected and position % 8 < 7) +
                   (position + 8 in selected) for position in selected)
    return blocks, touching


def figure(locations, blocks, touching):
    selected = set(locations)
    w, h = 358, 615
    cells = []
    for position in range(256):
        row, col = divmod(position, 8)
        x, y = 25 + 30 * col, 66 + 15 * row
        fill = "#236084" if position in selected else "#eef1f3"
        cells.append(f'<rect x="{x}" y="{y}" width="26" height="12" rx="2" fill="{fill}"/>')
    labels = ''.join(f'<text x="330" y="{139 + 120*b}" text-anchor="end" class="count">{n} of 64</text>'
                     for b, n in enumerate(blocks))
    lines = ''.join(f'<line x1="17" y1="{63 + 120*b}" x2="340" y2="{63 + 120*b}" stroke="#9aa8af"/>'
                    for b in range(1, 4))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="Positions of 17 prefix-four cells in four eight-row blocks">'
            '<style>text{font:15px system-ui,sans-serif;fill:#24323a}.title{font-size:18px;font-weight:650}.count{font-size:13px;fill:#385869}</style>'
            '<rect width="100%" height="100%" fill="white"/>'
            '<text x="18" y="27" class="title">Where the 4-prefix cells fall</text>'
            f'<text x="18" y="49">17 of 256 cells · {touching} touching pairs</text>'
            + ''.join(cells) + lines + labels +
            '<text x="18" y="563">Each block has 8 rows × 8 columns.</text>'
            '<text x="18" y="587">Blue cells start with 4; gray cells do not.</text>'
            '</svg>\n')


def report():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    for item in plan["inputs"]:
        path = ROOT / item["path"]
        if digest(path) != item["sha256"]:
            raise ValueError(f'Input changed: {path}')
    tokens = [item["token"] for item in json.loads(SOURCE.read_text(encoding="utf-8"))["records"]]
    assert len(tokens) == 256 and all(len(token) == 2 for token in tokens)
    cells = [index for index, token in enumerate(tokens) if token[0] == "4"]
    suffixes = ''.join(tokens[index][1] for index in cells)
    blocks, touching = stats(cells)
    rng = random.Random(plan["seed"])
    reps = plan["replicates"]
    max_block_hist, touching_hist = Counter(), Counter()
    row_touching_hist = Counter()
    row_counts = [sum(8 * row <= position < 8 * row + 8 for position in cells)
                  for row in range(32)]
    for _ in range(reps):
        sample = rng.sample(range(256), len(cells))
        sample_blocks, sample_touching = stats(sample)
        max_block_hist[max(sample_blocks)] += 1
        touching_hist[sample_touching] += 1
        row_sample = [8 * row + col for row, count in enumerate(row_counts)
                      for col in rng.sample(range(8), count)]
        row_touching_hist[stats(row_sample)[1]] += 1
    alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx'
    digit = {char: i for i, char in enumerate(alphabet)}
    assert all(4 * 60 + digit[tokens[i][1]] <= 255 for i in cells)
    return {
        "schema": "liberpedia-grid-high-digit-cells-v1", "plan_sha256": digest(PLAN),
        "source_sha256": digest(SOURCE), "prefix_four_count": len(cells),
        "positions_zero_based": cells, "suffix_sequence": suffixes,
        "distinct_suffixes": ''.join(sorted(set(suffixes))),
        "missing_hex_suffixes": ''.join(sorted(set('0123456789ABCDEF') - set(suffixes))),
        "byte_maximum_suffix_digit": 255 - 4 * 60,
        "block_counts": blocks, "touching_pairs": touching,
        "control": {
            "description": "Uniformly choose 17 of 256 positions; symbols not shuffled or modeled.",
            "seed": plan["seed"], "replicates": reps,
            "max_block_at_least_observed": sum(n for k, n in max_block_hist.items() if k >= max(blocks)),
            "touching_at_least_observed": sum(n for k, n in touching_hist.items() if k >= touching),
            "within_row_touching_at_least_observed": sum(n for k, n in row_touching_hist.items() if k >= touching),
            "max_block_histogram": {str(k): n for k, n in sorted(max_block_hist.items())},
            "touching_histogram": {str(k): n for k, n in sorted(touching_hist.items())},
            "within_row_touching_histogram": {str(k): n for k, n in sorted(row_touching_hist.items())},
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    image = figure(result['positions_zero_based'], result['block_counts'], result['touching_pairs'])
    if args.check:
        assert json.loads(OUTPUT.read_text(encoding='utf-8')) == result
        assert FIGURE.read_text(encoding='utf-8') == image
        print('PASS grid-high-digit-cells')
    else:
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        FIGURE.write_text(image, encoding='utf-8', newline='\n')
        print('Wrote results.json and cells.svg')


if __name__ == '__main__':
    main()
