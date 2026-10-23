"""Small source-search comparison, legible at a 340px viewport."""
from __future__ import annotations

import collections
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    counts = collections.Counter(row["max_trigrams"] for row in result["controls"]["rows"])
    assert result["observed"]["max_trigrams"] == 6
    assert sum(counts.values()) == 199
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 320" role="img" aria-labelledby="title desc">',
           '<title id="title">Best route score compared with complete shuffled searches</title>',
           '<desc id="desc">The manuscript maximum is six trigram hits. In 199 full-search rune shuffles, 57 reached six or more.</desc>',
           '<rect width="340" height="320" fill="#f5f6f7"/>',
           '<text x="18" y="29" font-family="Arial,sans-serif" font-size="17" font-weight="700" fill="#172b3a">Six hits are not distinctive</text>',
           '<text x="18" y="54" font-family="Arial,sans-serif" font-size="13" fill="#43505a">Best route after the entire 58-route search</text>']
    for value in range(3, 9):
        y = 75 + (value - 3) * 31
        width = round(counts[value] / 75 * 184)
        fill = "#335d77" if value == 6 else "#aab9c2"
        out.extend([
            f'<text x="18" y="{y+17}" font-family="Arial,sans-serif" font-size="14" fill="#172b3a">{value} hits</text>',
            f'<rect x="76" y="{y}" width="{width}" height="22" rx="3" fill="{fill}"/>',
            f'<text x="{min(76+width+7, 300)}" y="{y+17}" font-family="Arial,sans-serif" font-size="14" fill="#172b3a">{counts[value]}</text>',
        ])
    out.extend([
        '<path d="M18 269H322" stroke="#cbd3d8"/>',
        '<text x="18" y="291" font-family="Arial,sans-serif" font-size="13" fill="#172b3a">Manuscript: 6 hits</text>',
        '<text x="18" y="311" font-family="Arial,sans-serif" font-size="13" fill="#43505a">57 of 199 shuffled searches reached 6+</text>',
        '</svg>'])
    (HERE / "comparison.svg").write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
