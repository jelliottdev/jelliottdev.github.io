"""Render a phone-legible count comparison from the saved report."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
row = json.loads((HERE / "results.json").read_text(encoding="utf-8"))["lag13"]
low, high = row["shuffled_middle_95"]
observed = row["two_pair_matches"]
x = lambda value: 28 + value / 25 * 300
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 230" role="img" aria-labelledby="t d">
<title id="t">Exact two-rune repeats 13 positions apart</title>
<desc id="d">The observed count of {observed} sits within the middle 95 percent of page-preserving shuffle counts, {low} to {high}.</desc>
<rect width="360" height="230" fill="#fff"/>
<text x="17" y="28" font-size="18" font-family="Arial, sans-serif" fill="#202d35">Lag 13: repeated two-rune</text>
<text x="17" y="51" font-size="18" font-family="Arial, sans-serif" fill="#202d35">patterns</text>
<text x="17" y="75" font-size="13" font-family="Arial, sans-serif" fill="#52616b">12,186 eligible 15-rune windows</text>
<line x1="28" y1="123" x2="328" y2="123" stroke="#ccd4d8" stroke-width="2"/>
<line x1="{x(low):.1f}" y1="123" x2="{x(high):.1f}" y2="123" stroke="#879aa5" stroke-width="13" stroke-linecap="round"/>
<circle cx="{x(observed):.1f}" cy="123" r="9" fill="#215a79" stroke="white" stroke-width="2"/>
<text x="17" y="106" font-size="14" font-family="Arial, sans-serif" fill="#202d35">Observed</text>
<text x="328" y="106" text-anchor="end" font-size="16" font-weight="700" font-family="Arial, sans-serif" fill="#215a79">{observed}</text>
<text x="28" y="152" font-size="13" font-family="Arial, sans-serif" fill="#52616b">0</text>
<text x="328" y="152" text-anchor="end" font-size="13" font-family="Arial, sans-serif" fill="#52616b">25</text>
<line x1="18" y1="186" x2="36" y2="186" stroke="#879aa5" stroke-width="9" stroke-linecap="round"/>
<text x="46" y="191" font-size="13" font-family="Arial, sans-serif" fill="#52616b">Page-shuffle middle 95%: {low}–{high}</text>
<circle cx="26" cy="211" r="6" fill="#215a79"/>
<text x="46" y="216" font-size="13" font-family="Arial, sans-serif" fill="#52616b">Observed: {observed}</text>
</svg>'''
(HERE / "comparison.svg").write_bytes((svg + "\n").encode("utf-8"))
