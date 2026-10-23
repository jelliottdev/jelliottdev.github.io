"""Compact readable chart for the only executable G3 pointer flag."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "lowentropy.svg"


def main():
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    labels = (("Prime values", "value"), ("Prime index", "pi"), ("Prime totient", "phi"))
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 350" role="img" '
        'aria-labelledby="title desc" font-family="Arial, sans-serif">',
        '<title id="title">No excess repeated-symbol pointer run</title>',
        '<desc id="desc">On all three number streams, the longest low-entropy base32 run '
        'is shorter than the largest of 200 shuffled controls. Only a longer run of at least '
        '16 would be flagged by the source.</desc>',
        '<rect x="0" y="0" width="320" height="350" fill="#f5f6f7"/>',
        '<text x="16" y="29" font-size="17" font-weight="700" fill="#202a32">Repeated-symbol runs</text>',
        '<text x="16" y="52" font-size="13" fill="#46545f">Length in mapped base32 characters</text>',
    ]
    for row, (label, key) in enumerate(labels):
        y = 91 + row * 83
        real = result["streams"][key]["real"]["b32_lowentropy_run"]
        maximum = result["streams"][key]["null"]["b32_lowentropy_run"]["max"]
        parts += [
            f'<text x="16" y="{y}" font-size="14" font-weight="700" fill="#202a32">{label}</text>',
            f'<rect x="16" y="{y + 10}" width="{real * 9}" height="12" rx="2" fill="#27617b"/>',
            f'<text x="{22 + real * 9}" y="{y + 21}" font-size="13" fill="#202a32">{real} observed</text>',
            f'<rect x="16" y="{y + 31}" width="{maximum * 9}" height="12" rx="2" fill="#87939b"/>',
            f'<text x="{22 + maximum * 9}" y="{y + 42}" font-size="13" fill="#202a32">{int(maximum)} shuffled max</text>',
        ]
    parts += [
        '<line x1="16" y1="309" x2="304" y2="309" stroke="#c7cdd1"/>',
        '<text x="16" y="331" font-size="13" fill="#46545f">Flag only if observed exceeds shuffled max.</text>',
        '</svg>',
    ]
    svg = "\n".join(parts) + "\n"
    if OUT.exists() and OUT.read_text(encoding="utf-8") == svg:
        print("PASS", hashlib.sha256(OUT.read_bytes()).hexdigest())
    else:
        OUT.write_text(svg, encoding="utf-8", newline="\n")
        print("WROTE", hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
