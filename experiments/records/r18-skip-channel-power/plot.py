"""Small-screen diagram of B5 beam-selected skip counts."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def svg():
    d = json.loads((HERE / "replayed-b5_skipchannel.json").read_text(encoding="utf-8"))
    plant = d["wrong_keys_on_plant"]
    real = d["wrong_keys_on_real_ciphertext"]
    true = d["true_key_on_plant"]["n_skips"]
    best = d["real_candidates_full_book"][0]["n_skips"]
    x = lambda value: 28 + (value - 230) * 1.72
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 290" role="img" aria-labelledby="title desc" style="font-family:Arial,sans-serif">
<title id="title">Skip counts from selected beam paths</title>
<desc id="desc">The planted correct key has 362 inferred skips, beyond forty planted wrong keys. Real wrong keys overlap the best of twenty preselected real candidates at 353 skips.</desc>
<rect width="320" height="290" fill="#f4f6f7"/>
<text x="18" y="29" font-size="17" font-weight="700" fill="#202b32">Skip counts from a beam search</text>
<text x="18" y="51" font-size="13" fill="#45545d">Range across 40 keys; dots mark selected cases</text>
<text x="18" y="83" font-size="14" fill="#24353e">Wrong keys on planted text</text>
<line x1="{x(plant['min']):.1f}" x2="{x(plant['max']):.1f}" y1="101" y2="101" stroke="#87959e" stroke-width="9" stroke-linecap="round"/>
<circle cx="{x(plant['mean_skips']):.1f}" cy="101" r="5" fill="#fff" stroke="#45545d" stroke-width="2"/>
<text x="18" y="134" font-size="14" fill="#24353e">Correct key on planted text</text>
<circle cx="{x(true):.1f}" cy="151" r="7" fill="#1d5d79"/>
<text x="{x(true)-12:.1f}" y="174" text-anchor="end" font-size="13" fill="#1d5d79">{true}</text>
<text x="18" y="197" font-size="14" fill="#24353e">Wrong keys on LP2</text>
<line x1="{x(real['min']):.1f}" x2="{x(real['max']):.1f}" y1="215" y2="215" stroke="#87959e" stroke-width="9" stroke-linecap="round"/>
<circle cx="{x(real['mean_skips']):.1f}" cy="215" r="5" fill="#fff" stroke="#45545d" stroke-width="2"/>
<circle cx="{x(best):.1f}" cy="215" r="7" fill="#1d5d79"/>
<text x="18" y="249" font-size="13" fill="#45545d">Best of 20 earlier candidates: {best} skips</text>
<text x="18" y="272" font-size="13" fill="#45545d">Path choice uses an English score.</text>
</svg>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = HERE / "skip-counts.svg"
    data = svg()
    if args.check:
        assert path.read_text(encoding="utf-8") == data
        print("PASS: SVG matches completed source result")
    else:
        path.write_text(data, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
