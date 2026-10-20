"""Draw the complete ordinary Atbash pairing from the published alphabet."""
import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render():
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    if len(alphabet) != 29:
        raise ValueError("Expected the 29-symbol rune alphabet")
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 730" role="img" aria-labelledby="title desc">',
        '<title id="title">Ordinary Atbash: complete index pairs</title>',
        '<desc id="desc">Each pair sums to 28. Indices 0 through 13 exchange with 28 through 15. Index 14 maps to itself. Labels represent whole runes.</desc>',
        '<rect width="480" height="730" fill="#fff"/>',
        '<g font-family="Arial, sans-serif" fill="#20242a">',
        '<text x="24" y="36" font-size="25">Ordinary Atbash</text>',
        '<text x="24" y="65" font-size="19">Output index = 28 − input index</text>',
        '<text x="24" y="103" font-size="18" fill="#5c626b">Index · rune label</text>',
        '<text x="304" y="103" font-size="18" fill="#5c626b">Index · rune label</text>',
    ]
    for index in range(15):
        opposite = 28 - index
        # The published labels can span multiple Latin letters but name one rune.
        left = html.escape(str(alphabet[index]["latin"]))
        right = html.escape(str(alphabet[opposite]["latin"]))
        y = 136 + 36 * index
        parts.extend([
            f'<path d="M24 {y+12}H456" stroke="#dce0e4"/>',
            f'<text x="40" y="{y}" font-size="22">{index} · {left}</text>',
            f'<text x="232" y="{y}" font-size="24" text-anchor="middle">↔</text>',
            f'<text x="320" y="{y}" font-size="22">{opposite} · {right}</text>',
        ])
    parts.extend([
        '<text x="24" y="687" font-size="18">The middle pair is one unchanged symbol.</text>',
        '<text x="24" y="715" font-size="18">Substitute symbols; keep their text positions.</text>',
        '</g></svg>',
    ])
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = render()
        with args.output.open("x", encoding="utf-8", newline="\n") as destination:
            destination.write(result)
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    print("Saved:", args.output)


if __name__ == "__main__":
    main()
