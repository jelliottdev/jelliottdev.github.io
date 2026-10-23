"""Small-screen explanation of the source search's selection limit and score."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
actual = data["manuscript"]["max_score"]
nulls = sorted(x["max_score"] for x in data["order_control"]["nulls"])
median = nulls[len(nulls) // 2]
at_least = data["order_control"]["at_least_manuscript"]
assert actual == 670 and median == 700 and at_least == 154


def sx(value: float) -> float:
    return 42 + (value - 550) * 254 / 350


svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 390" role="img" aria-labelledby="title desc">
<title id="title">Liber AL offset search: a selection gap and an ordinary page score</title>
<desc id="desc">Known messages at sampled offsets 300 and 1700 were found; one at unsampled offset 137 was missed. The real page's best trigram score 670 is below the shuffled-order median 700; 154 of 199 shuffles scored at least as high.</desc>
<rect x="1" y="1" width="338" height="388" rx="4" fill="#fff" stroke="#c6ccd0"/>
<g font-family="Arial, sans-serif" fill="#23323c">
<text x="18" y="29" font-size="17" font-weight="700">The search can miss an offset</text>
<text x="18" y="56" font-size="14">It first checks every 100th position.</text>
<line x1="42" y1="99" x2="298" y2="99" stroke="#74838d" stroke-width="2"/>
<circle cx="81" cy="99" r="6" fill="#315e78"/>
<circle cx="230" cy="99" r="6" fill="#315e78"/>
<circle cx="137" cy="99" r="6" fill="#a43c3c"/>
<text x="63" y="82" font-size="14">100</text>
<text x="211" y="82" font-size="14">200</text>
<text x="119" y="127" font-size="14" fill="#8a3030" font-weight="700">137</text>
<text x="18" y="156" font-size="14">In a planted test, offset 137 never</text>
<text x="18" y="176" font-size="14">reached the finer search.</text>
<line x1="18" y1="197" x2="322" y2="197" stroke="#d9dddf"/>
<text x="18" y="222" font-size="17" font-weight="700">The page’s score was ordinary</text>
<text x="18" y="248" font-size="14">Best common-trigram score</text>
<line x1="{sx(580):.1f}" y1="288" x2="{sx(870):.1f}" y2="288" stroke="#bec7cc" stroke-width="12" stroke-linecap="round"/>
<line x1="{sx(median):.1f}" y1="275" x2="{sx(median):.1f}" y2="301" stroke="#52636e" stroke-width="3"/>
<circle cx="{sx(actual):.1f}" cy="288" r="7" fill="#315e78"/>
<text x="24" y="269" font-size="13">580</text>
<text x="275" y="269" font-size="13">870</text>
<text x="18" y="326" font-size="14" fill="#315e78" font-weight="700">Page 670</text>
<text x="173" y="326" font-size="14">Shuffle median 700</text>
<text x="18" y="355" font-size="14">{at_least} of 199 shuffles scored at least</text>
<text x="18" y="375" font-size="14">as high as the page.</text>
</g></svg>'''
(HERE / "comparison.svg").write_text(svg + "\n", encoding="utf-8", newline="\n")
print("wrote comparison.svg")
