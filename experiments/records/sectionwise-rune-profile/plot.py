"""Draw a phone-legible equal-length comparison from saved results."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "results.json").read_text(encoding="utf-8"))["comparison"]


def x(value, low, high):
    return 29 + (value - low) / (high - low) * 300


rows = [
    ("Rune collision (IoC)", "ioc", .03, .04, "0.030", "0.040", "0.03382"),
    ("Adjacent equal runes", "doublet_rate", 0, .02, "0%", "2%", "0.98%"),
]
elements = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 300" role="img" aria-labelledby="t d">',
    '<title id="t">LP2 ending compared with equal-length earlier windows</title>',
    '<desc id="d">Both LP2-54–55 measures are inside the middle 95 percent of 308-rune windows from LP2-40–53. Gray marks that range; blue dots mark the ending.</desc>',
    '<rect width="360" height="300" fill="#fff"/>',
    '<text x="17" y="29" font-size="19" font-family="Arial, sans-serif" fill="#202d35">Same-length comparison</text>',
    '<text x="17" y="50" font-size="13" font-family="Arial, sans-serif" fill="#52616b">LP2-54–55 versus earlier 308-rune spans</text>',
]
for row, (label, key, low, high, left, right, observed_label) in enumerate(rows):
    label_y = 82 + row * 98
    axis_y = label_y + 24
    measure = data[key]
    interval_low, interval_high = measure["central_95"]
    point = data["ending"]["ioc" if key == "ioc" else "doublet_rate"]
    elements += [
        f'<text x="17" y="{label_y}" font-size="15" font-family="Arial, sans-serif" fill="#202d35">{label}</text>',
        f'<text x="330" y="{label_y}" text-anchor="end" font-size="15" font-weight="700" font-family="Arial, sans-serif" fill="#215a79">{observed_label}</text>',
        f'<line x1="29" x2="329" y1="{axis_y}" y2="{axis_y}" stroke="#ccd4d8" stroke-width="2"/>',
        f'<line x1="{x(interval_low, low, high):.1f}" x2="{x(interval_high, low, high):.1f}" y1="{axis_y}" y2="{axis_y}" stroke="#879aa5" stroke-width="12" stroke-linecap="round"/>',
        f'<circle cx="{x(point, low, high):.1f}" cy="{axis_y}" r="8" fill="#215a79" stroke="white" stroke-width="2"/>',
        f'<text x="29" y="{axis_y+24}" font-size="13" font-family="Arial, sans-serif" fill="#52616b">{left}</text>',
        f'<text x="329" y="{axis_y+24}" text-anchor="end" font-size="13" font-family="Arial, sans-serif" fill="#52616b">{right}</text>',
    ]
elements += [
    '<line x1="17" x2="35" y1="267" y2="267" stroke="#879aa5" stroke-width="9" stroke-linecap="round"/>',
    '<text x="46" y="272" font-size="13" font-family="Arial, sans-serif" fill="#52616b">Middle 95% of earlier spans</text>',
    '<circle cx="25" cy="288" r="6" fill="#215a79"/>',
    '<text x="46" y="293" font-size="13" font-family="Arial, sans-serif" fill="#52616b">LP2-54–55</text>',
    '</svg>',
]
(HERE / "comparison.svg").write_bytes(("\n".join(elements) + "\n").encode("utf-8"))
