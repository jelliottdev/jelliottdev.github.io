"""Phone-readable dot plot of B3's best result for each historic key stream."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
rows = [("2012 P.S. digits", "ps_digits"), ("P.S. pairs", "ps_2dig"),
        ("P.S. base 29", "ps_base29"), ("Telnet primes", "missing_primes"),
        ("Telnet gaps", "missing_gaps"), ("2012 spaces", "trail_2012"),
        ("2013 spaces", "trail_2013"), ("2014 spaces", "trail_2014"),
        ("2015 spaces", "trail_2015")]
width, height = 340, 476
left, right = 14, 326
x0, x1 = 151, 317


def x(value):
    return x0 + (value + 7.2) / 2.0 * (x1 - x0)


parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
         '<title id="title">No historical numeric key stream met the English-score bar</title>',
         '<desc id="desc">Nine source-defined numeric streams have best scores from minus 7.083 to minus 6.757. The advancement bar is minus 5.2.</desc>',
         '<rect width="340" height="476" fill="#f6f7f8"/>',
         '<text x="14" y="30" font-family="Arial,sans-serif" font-size="16" font-weight="700" fill="#17222b">Best score for each stream</text>',
         '<text x="14" y="53" font-family="Arial,sans-serif" font-size="13" fill="#435461">Higher means more English-like</text>']
for tick in (-7.0, -6.5, -6.0, -5.5, -5.2):
    pos = x(tick)
    parts.append(f'<line x1="{pos:.1f}" y1="85" x2="{pos:.1f}" y2="411" stroke="#d4dce1"/>')
    parts.append(f'<text x="{pos:.1f}" y="431" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#41505c">{tick:.1f}</text>')
parts.append(f'<line x1="{x(-5.2):.1f}" y1="79" x2="{x(-5.2):.1f}" y2="411" stroke="#345f78" stroke-width="2"/>')
for i, (label, key) in enumerate(rows):
    y = 105 + i * 36
    score = data["per_stream_best"][key]
    pos = x(score)
    parts.append(f'<text x="14" y="{y + 5}" font-family="Arial,sans-serif" font-size="13" fill="#17222b">{label}</text>')
    parts.append(f'<circle cx="{pos:.1f}" cy="{y}" r="5" fill="#345f78"/>')
    parts.append(f'<text x="{pos + 10:.1f}" y="{y + 5}" font-family="Arial,sans-serif" font-size="13" fill="#274b63">{score:.3f}</text>')
parts.extend(['<text x="14" y="458" font-family="Arial,sans-serif" font-size="13" fill="#435461">Source bar: −5.2 · 0 of 4,032 cases passed</text>', '</svg>'])
(HERE / "scores.svg").write_text("\n".join(parts) + "\n", encoding="utf-8", newline="\n")
