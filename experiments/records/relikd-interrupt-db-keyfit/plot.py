"""Compact control-power chart for the source key-fit screen."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render():
    data = json.loads((HERE / "results.json").read_text(encoding="utf8"))
    rows = data["controls"]["matched_length"]
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 352" role="img" aria-labelledby="title desc">',
        '<title id="title">Known text recovery before the LP2 search</title>',
        '<desc id="desc">The source key fitter recovered only 35 to 86 percent of the six known-text controls at matching lengths. Yet its saved similarity limit accepts 13 of 18 LP2 candidates. These are source score hits, not readings.</desc>',
        '<rect x="0" y="0" width="320" height="352" fill="#f7f9fa"/>',
        '<g font-family="Arial, sans-serif" fill="#20313c">',
        '<text x="16" y="29" font-size="16" font-weight="700">Known text: incomplete recovery</text>',
        '<text x="16" y="48" font-size="12">Original key fitter · six matched-length plants</text>',
    ]
    for number, row in enumerate(rows):
        y = 84 + number * 34
        label = ("Vigenère" if row["branch"] == "Vigenere" else "Affine") + " · " + str(row["runes"])
        fraction = row["plaintext_runes_exact"] / row["runes"]
        width = round(153 * fraction, 1)
        color = "#326985" if row["branch"] == "Vigenere" else "#64788a"
        out += [
            f'<text x="16" y="{y}" font-size="12">{label}</text>',
            f'<rect x="115" y="{y-11}" width="153" height="12" rx="2" fill="#dde5e9"/>',
            f'<rect x="115" y="{y-11}" width="{width}" height="12" rx="2" fill="{color}"/>',
            f'<text x="274" y="{y}" font-size="12" font-weight="700">{round(100*fraction)}%</text>',
        ]
    accepted = sum(x["source_reported"] for x in data["target"])
    out += [
        '<line x1="16" y1="283" x2="304" y2="283" stroke="#cbd6dc"/>',
        f'<text x="16" y="311" font-size="14" font-weight="700">{accepted} / 18 LP2 fits cleared the source limit</text>',
        '<text x="16" y="331" font-size="12">A score hit is not a decoded reading.</text>',
        '</g></svg>\n',
    ]
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = render()
    path = HERE / "control-power.svg"
    if args.check:
        assert path.read_text(encoding="utf8") == text
    else:
        path.write_text(text, encoding="utf8", newline="\n")
    print("control power visual", len(text), "characters")


if __name__ == "__main__":
    main()
