"""Build a compact phone-readable diagram from the frozen census."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render():
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    fit = [case for case in result["cases"] if case["compatible"]]
    assert len(fit) == 1 and (fit[0]["page"], fit[0]["crib"]) == ("lp2-12", "second-koan")
    assert fit[0]["assigned_symbols"] == 10 and fit[0]["following_positions_forced"] == 5
    fixed = {14, 17, 19, 21, 24}
    cells = []
    for i in range(12):
        position = i + 13
        x = 18 + (i % 6) * 51
        y = 171 + (i // 6) * 43
        color = "#dceaf1" if position in fixed else "#eaedef"
        cells.append(f'<rect x="{x}" y="{y}" width="43" height="35" rx="4" fill="{color}"/>'
                     f'<text x="{x+21.5}" y="{y+23}" text-anchor="middle" class="cell">{position}</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 291" role="img" aria-labelledby="title desc">
<title id="title">What one matching substitution crib fixes</title>
<desc id="desc">Of 495 proposed page-and-opening pairs, one is compatible. It fixes ten of 29 symbol mappings and five of the next twelve rune positions.</desc>
<style>.head{{font:700 17px system-ui,sans-serif;fill:#182a35}}.body{{font:14px system-ui,sans-serif;fill:#273b47}}.cell{{font:700 14px system-ui,sans-serif;fill:#233845}}</style>
<rect width="340" height="291" fill="#f8f9fa"/>
<text x="18" y="29" class="head">One compatible page opening</text>
<text x="18" y="56" class="body">LP2-12 + second-koan crib · 1 of 495 pairs</text>
<line x1="18" y1="71" x2="322" y2="71" stroke="#cbd4d9"/>
<text x="18" y="100" class="body">10 of 29 symbols assigned</text>
<text x="18" y="125" class="body">19 remain free · 19! complete keys</text>
<text x="18" y="157" class="head">Next 12 positions</text>
{''.join(cells)}
<rect x="18" y="264" width="13" height="13" fill="#dceaf1"/><text x="37" y="276" class="body">5 forced</text>
<rect x="160" y="264" width="13" height="13" fill="#eaedef"/><text x="179" y="276" class="body">7 free</text>
</svg>'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    svg = render()
    path = HERE / "continuation.svg"
    if args.check:
        assert path.read_text(encoding="utf-8") == svg
        print("PASS: diagram matches saved census")
    else:
        path.write_text(svg, encoding="utf-8", newline="\n")
        print(path)
