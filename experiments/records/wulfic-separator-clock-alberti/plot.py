"""Responsive chart of the source hit gate against each page's best IoC."""
from __future__ import annotations

import html
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def main() -> None:
    d = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    grouped = {}
    for row in d["rows"]:
        if row["source_ordinal"] != 15:
            grouped.setdefault(row["manuscript_page"], {})[row["parser"]] = row["max_ioc"]
    pages = sorted(r["manuscript_page"] for r in d["rows"] if r["parser"] == "literal" and r["source_ordinal"] != 15)
    x0, x1 = 94, 294
    def x(value: float) -> float:
        return x0 + (value - 0.9) / 0.5 * (x1 - x0)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 520" role="img" aria-labelledby="title desc">',
           '<title id="title">None of eleven LP2 pages reaches the source hit threshold</title>',
           '<desc id="desc">Dots show each page’s largest normalized index of coincidence over all 1,682 distinct separator-clock schedules. The original source parser and a corrected GP rune parser both stay below 1.4 on every LP2 page.</desc>',
           '<rect width="340" height="520" fill="#f6f7f8"/>',
           '<text x="18" y="30" fill="#1d2c38" font-family="Arial,sans-serif" font-size="17" font-weight="700">No LP2 page passes the gate</text>',
           '<text x="18" y="53" fill="#455561" font-family="Arial,sans-serif" font-size="13">Highest IoC after every source clock setting</text>',
           f'<line x1="{x(1.4):.1f}" y1="92" x2="{x(1.4):.1f}" y2="425" stroke="#6b7781" stroke-width="2" stroke-dasharray="5 4"/>']
    for i, page in enumerate(pages):
        y = 110 + i * 28
        values = grouped[page]
        out.append(f'<text x="18" y="{y+5}" font-family="Arial,sans-serif" font-size="13" fill="#253540">{html.escape(page.upper())}</text>')
        out.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#dce2e6"/>')
        out.append(f'<circle cx="{x(values["literal"]):.1f}" cy="{y-4}" r="4.5" fill="#305e78"/>')
        out.append(f'<circle cx="{x(values["canonical"]):.1f}" cy="{y+4}" r="4.5" fill="#8b9ba5"/>')
    out += [f'<text x="{x(1.0)-8:.1f}" y="440" font-family="Arial,sans-serif" font-size="12" fill="#455561">1.0</text>',
            f'<text x="{x(1.2)-8:.1f}" y="440" font-family="Arial,sans-serif" font-size="12" fill="#455561">1.2</text>',
            f'<text x="{x(1.4)-8:.1f}" y="440" font-family="Arial,sans-serif" font-size="12" fill="#455561">1.4</text>',
            '<circle cx="25" cy="467" r="5" fill="#305e78"/><text x="38" y="471" font-family="Arial,sans-serif" font-size="13" fill="#253540">Source rune parser</text>',
            '<circle cx="177" cy="467" r="5" fill="#8b9ba5"/><text x="190" y="471" font-family="Arial,sans-serif" font-size="13" fill="#253540">Corrected parser</text>',
            '<text x="18" y="499" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="#1d2c38">Source gate: above 1.4 · LP2 hits: 0</text>',
            '</svg>']
    (HERE / "comparison.svg").write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
