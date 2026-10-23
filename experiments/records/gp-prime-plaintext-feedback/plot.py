"""Small responsive explanation of the two rules and their full-search control."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    greater = result["null_exceedances"]
    trials = result["null_trials"]
    lower = trials - greater
    # The width is intentionally close to a phone content column. All labels
    # remain at least 13 units when the SVG is displayed at 320 CSS px.
    width = 272
    high_width = round(width * greater / trials, 2)
    low_width = width - high_width
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 292" role="img" aria-labelledby="title desc" style="max-width:100%;height:auto;font-family:Arial,sans-serif">
<title id="title">Prime-valued plaintext feedback test</title>
<desc id="desc">Two page-local rules use a previous plaintext rune or a running plaintext prime sum. In a 6,380-case whole-page search, {greater} of {trials} matched page-shuffle searches scored at least as high as the observed maximum.</desc>
<rect width="320" height="292" fill="#f4f6f7"/>
<text x="20" y="30" font-size="17" font-weight="700" fill="#172d39">Prime-valued feedback</text>
<text x="20" y="54" font-size="13" fill="#42545e">Each recovered rune helps set the next key.</text>
<rect x="20" y="72" width="280" height="44" rx="4" fill="#fff" stroke="#c6d0d5"/>
<text x="32" y="91" font-size="13" font-weight="700" fill="#173c54">Previous rune</text>
<text x="32" y="108" font-size="13" fill="#334b59">Decoded rune → prime value → next key</text>
<rect x="20" y="125" width="280" height="44" rx="4" fill="#fff" stroke="#c6d0d5"/>
<text x="32" y="144" font-size="13" font-weight="700" fill="#173c54">Running sum</text>
<text x="32" y="161" font-size="13" fill="#334b59">Add each decoded rune’s prime value</text>
<text x="20" y="198" font-size="14" font-weight="700" fill="#172d39">Did either rule stand out?</text>
<text x="20" y="218" font-size="13" fill="#42545e">Best score after all 6,380 candidates</text>
<rect x="20" y="229" width="{high_width}" height="20" fill="#42687c"/>
<rect x="{20 + high_width}" y="229" width="{low_width}" height="20" fill="#c5d1d7"/>
<text x="20" y="273" font-size="14" font-weight="700" fill="#172d39">{greater} / {trials} shuffles did as well or better</text>
</svg>
'''
    (HERE / "feedback-overview.svg").write_text(svg, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
