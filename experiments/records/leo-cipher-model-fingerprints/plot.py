"""Small-screen explanation of the chain model's repeat-rate match."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def make() -> str:
    data = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    observed = data["observed"]
    chain = next(x for x in data["models"] if x["name"] == "chain c=c_prev+p+1")
    assert chain["equal1"] == 20
    rows = [
        ("LP2 text", observed["equal1"], observed["runes"] - 1, "#315e77"),
        ("Source chain +1", chain["equal1"], chain["runes"] - 1, "#596e7d"),
        ("Uniform 29-rune", 1, 29, "#adb8c0"),
    ]
    bits = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 312" role="img" aria-labelledby="title desc">',
        '<title id="title">Why one simulated chain has LP2-like repeat frequency</title>',
        '<desc id="desc">LP2 has 86 repeats in 12,955 adjacent pairs, or 0.664 percent. The source chain has 20 in 2,978, or 0.672 percent. Its repeat count equals the frequency of one plaintext rune, EA, by construction. Uniform-random runes repeat about 3.448 percent.</desc>',
        '<rect width="340" height="312" fill="#f5f6f7"/>',
        '<text x="16" y="29" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="#202a31">A close repeat-rate match</text>',
        '<text x="16" y="58" font-family="Arial,sans-serif" font-size="14" fill="#43535f">Identical adjacent runes</text>',
    ]
    for i, (label, count, denom, color) in enumerate(rows):
        y = 92 + i * 53
        rate = count / denom
        width = round(137 * rate / (1 / 29), 1)
        bits.extend([
            f'<text x="16" y="{y}" font-family="Arial,sans-serif" font-size="14" fill="#202a31">{label}</text>',
            f'<rect x="16" y="{y+10}" width="137" height="10" fill="#e0e5e9"/>',
            f'<rect x="16" y="{y+10}" width="{width}" height="10" fill="{color}"/>',
            f'<text x="169" y="{y+19}" font-family="Arial,sans-serif" font-size="14" fill="#202a31">{rate*100:.3f}%</text>',
        ])
    bits.extend([
        '<line x1="16" y1="252" x2="324" y2="252" stroke="#d5dadd"/>',
        '<text x="16" y="276" font-family="Arial,sans-serif" font-size="14" fill="#202a31">Chain +1 repeats exactly when</text>',
        '<text x="16" y="296" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="#202a31">the plaintext rune is EA.</text>',
        '</svg>\n',
    ])
    return "\n".join(bits)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    output = HERE / "repeat-rate.svg"
    svg = make()
    if args.check:
        assert output.read_text(encoding="utf-8") == svg
    else:
        output.write_text(svg, encoding="utf-8", newline="\n")
    print("Small-screen figure checked.")


if __name__ == "__main__":
    main()
