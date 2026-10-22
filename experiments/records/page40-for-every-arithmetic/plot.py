"""Render an accessible SVG of the fixed arithmetic and fitted residual."""
import argparse
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def make_svg(result):
    rows = result["rows"]
    width, height = 1120, 480
    x0, dx = 280, 101
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">LP2-40 FOR EVERY: fixed steps and required residual</title>',
        '<desc id="desc">Eight columns compare the proposed crib, the output after shift, Atbash and prime-minus-one, and the archived ciphertext. The initial F is a zero placeholder. None of the seven other columns match before a residual is fitted from the ciphertext.</desc>',
        '<rect width="1120" height="480" fill="#fff"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#202b31} .head{font-size:25px;font-weight:700} .sub{font-size:16px;fill:#53616a} .label{font-size:17px;font-weight:600} .cell{font-size:23px;font-weight:700} .index{font-size:15px;fill:#53616a} .note{font-size:16px}</style>',
        '<text x="30" y="43" class="head">LP2-40 · FOR EVERY crib arithmetic</text>',
        '<text x="30" y="73" class="sub">The extra key is calculated from the observed runes; it is not a prediction.</text>',
    ]
    labels = [(133, "Proposed plaintext"), (220, "Fixed-rule output"), (307, "Archived ciphertext"), (394, "Required key, mod 29")]
    for y, label in labels:
        parts.append(f'<text x="30" y="{y}" class="label">{html.escape(label)}</text>')
    for i, row in enumerate(rows):
        x = x0 + i * dx
        for y in (105, 192, 279, 366):
            fill = "#f5f7f8" if y != 366 else ("#e8f0ed" if i == 0 else "#f7e8e3")
            parts.append(f'<rect x="{x}" y="{y}" width="88" height="64" fill="{fill}" stroke="#ccd5d8"/>')
        for y, value in ((132, row["proposed_plaintext_label"]),
                         (219, str(row["fixed_intermediate_index"])),
                         (306, str(row["archived_cipher_index"])),
                         (393, str(row["required_residual_mod_29"]))):
            parts.append(f'<text x="{x+44}" y="{y}" class="cell" text-anchor="middle">{html.escape(value)}</text>')
        parts.append(f'<text x="{x+44}" y="{151}" class="index" text-anchor="middle">index {row["proposed_plaintext_index"]}</text>')
        parts.append(f'<text x="{x+44}" y="{326}" class="index" text-anchor="middle">rune {i+1}</text>')
        if i == 0:
            parts.append(f'<text x="{x+44}" y="{414}" class="index" text-anchor="middle">F held</text>')
    parts += [
        '<text x="30" y="454" class="note">Fixed layers: 0 / 7 non-F matches. Every non-F key value above is a fitted difference.</text>',
        '</svg>\n',
    ]
    return "\n".join(parts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    svg = make_svg(result)
    target = HERE / "first-eight-trace.svg"
    if args.check:
        assert target.read_text(encoding="utf-8") == svg
        print("PASS: page 40 trace SVG reproduced")
    else:
        target.write_text(svg, encoding="utf-8")
        print(target)
