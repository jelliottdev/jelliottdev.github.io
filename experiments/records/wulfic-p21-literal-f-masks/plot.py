"""Explain the gap between a rising IoC and the source's failed word gate."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    result = json.loads((HERE / "results.json").read_text(encoding="utf8"))
    rows = result["observed"]["pages"]
    assert len(rows) == 10 and sum(r["all_singleton_masks"] for r in rows) == 0
    left, right = 76, 312
    def x(ioc: float) -> float:
        return left + (ioc - .90) / .32 * (right - left)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 475" role="img" aria-labelledby="title desc">',
           '<title id="title">F-mask frequency gains fail the word gate</title>',
           '<desc id="desc">On ten LP2 pages, the best selected F mask often raises index of coincidence, but none of the 27,402 masks makes every single-rune word I or A.</desc>',
           '<rect width="340" height="475" fill="#f5f6f7"/>',
           '<text x="16" y="29" font-family="Arial,sans-serif" font-size="17" font-weight="700" fill="#172b3a">A higher score is not a reading</text>',
           '<text x="16" y="53" font-family="Arial,sans-serif" font-size="13" fill="#43505a">IoC before and after selecting an F mask</text>',
           '<text x="16" y="77" font-family="Arial,sans-serif" font-size="13" fill="#43505a">Every page: zero masks pass the I/A word gate</text>']
    for value in (1.0, 1.1, 1.2):
        px=x(value)
        out.append(f'<path d="M{px:.1f} 97V389" stroke="#d5dce0"/>')
        out.append(f'<text x="{px-14:.1f}" y="408" font-family="Arial,sans-serif" font-size="13" fill="#43505a">{value:.1f}</text>')
    for j, row in enumerate(rows):
        y=110+j*28
        a=x(row["baseline_ioc"]); b=x(row["best_ioc"])
        page=row["current_page"].replace("lp2-", "")
        out.extend([f'<text x="16" y="{y+5}" font-family="Arial,sans-serif" font-size="14" fill="#172b3a">Page {page}</text>',
                    f'<path d="M{a:.1f} {y}H{b:.1f}" stroke="#8aa5b4" stroke-width="4" stroke-linecap="round"/>',
                    f'<circle cx="{a:.1f}" cy="{y}" r="5" fill="#8a969d"/>',
                    f'<circle cx="{b:.1f}" cy="{y}" r="6" fill="#315d77"/>'])
    out.extend(['<circle cx="22" cy="430" r="5" fill="#8a969d"/>',
                '<text x="34" y="435" font-family="Arial,sans-serif" font-size="13" fill="#43505a">No mask</text>',
                '<circle cx="130" cy="430" r="6" fill="#315d77"/>',
                '<text x="143" y="435" font-family="Arial,sans-serif" font-size="13" fill="#43505a">Best IoC mask</text>',
                '<text x="16" y="462" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#172b3a">27,402 masks checked · 0 pass</text>',
                '</svg>'])
    (HERE / "comparison.svg").write_text("\n".join(out)+"\n", encoding="utf8")


if __name__ == "__main__":
    main()
