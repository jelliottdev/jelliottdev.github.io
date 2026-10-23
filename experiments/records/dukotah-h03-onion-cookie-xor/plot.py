"""Mobile-readable maxima for the eight fixed cookie/blob pairs."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))["cases"]
LABELS = {"canon_256": "Grid payload", "rsahex_cu343": "Onion 2",
          "rsahex_fv7ly": "Onion 3", "rsahex_avowy": "Onion 4"}


def main():
    pairs = {}
    for c in CASES:
        key = c["cookie"], c["blob"]
        pairs[key] = max(pairs.get(key, 0), c["printable_count"])
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="350" height="420" viewBox="0 0 350 420" role="img" aria-label="Maximum printable bytes per cookie and blob, all below 26 of 32 required">',
           '<rect width="350" height="420" fill="#fff"/>',
           '<g font-family="Arial,sans-serif" fill="#20272c">',
           '<text x="12" y="27" font-size="18" font-weight="700">Cookie XOR, eight pairs</text>',
           '<text x="12" y="49" font-size="13" fill="#53616b">Highest printable count across eight blocks each</text>',
           '<line x1="278.5" y1="71" x2="278.5" y2="370" stroke="#a74539" stroke-width="2" stroke-dasharray="4 3"/>',
           '<text x="231" y="70" font-size="13" fill="#a74539">Pass: 26/32</text>']
    for group, cookie in enumerate(("cookie167", "cookie761")):
        base = 90 + group * 155
        out.append(f'<text x="12" y="{base}" font-size="14" font-weight="700">Cookie {cookie[-3:]}</text>')
        for j, blob in enumerate(LABELS):
            count = pairs[(cookie, blob)]
            y = base + 28 + j * 29
            w = count * 6.1
            out.extend([f'<text x="12" y="{y+12}" font-size="13">{LABELS[blob]}</text>',
                        f'<rect x="120" y="{y}" width="{w:.1f}" height="16" fill="#356078"/>',
                        f'<text x="{124+w:.1f}" y="{y+13}" font-size="13" font-weight="700">{count}</text>'])
    out.extend(['<text x="12" y="397" font-size="13" fill="#53616b">One pair = eight fixed 32-byte XOR blocks.</text>', '</g></svg>'])
    (HERE / "xor-maxima.svg").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
