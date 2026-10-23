"""Render a compact, phone-readable summary of the two conditional tests."""
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent


def draw():
    d = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    assert d['C3']['letters_checked'] == 29
    assert len(d['C3']['count_compatible']) == 3
    assert d['C3']['excluded_under_source_rule'] == 29
    c = d['C15']
    assert abs(c['minimum_expected_chi2'] - 4802.036755067442) < 1e-8
    assert abs(c['observed_lp2_chi2'] - 26.361685705464648) < 1e-8
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 410" role="img" aria-labelledby="title desc">
<title id="title">Two conditional letter-encoding checks</title>
<desc id="desc">Of 29 possible marker runes, three survive the frequency check and none survive the word-position check. In the dedicated-symbol homophone model the best expected chi-square is 4,802, compared with 26 for LP2.</desc>
<rect width="340" height="410" fill="#f5f6f7"/>
<g font-family="Arial, sans-serif" fill="#263944">
<text x="16" y="30" font-size="18" font-weight="bold">Two proposed encoding rules</text>
<text x="16" y="58" font-size="14" font-weight="bold">1. A repeat marks one plaintext rune</text>
<text x="16" y="83" font-size="13">29 possible marker runes</text>
<rect x="16" y="95" width="306" height="20" rx="3" fill="#cad6dc"/>
<text x="16" y="142" font-size="13">3 fit the total repeat count</text>
<rect x="16" y="154" width="32" height="20" rx="3" fill="#426c83"/>
<text x="16" y="201" font-size="13">0 also fit positions inside words</text>
<line x1="16" y1="213" x2="322" y2="213" stroke="#bec9ce" stroke-width="2"/>
<text x="16" y="250" font-size="14" font-weight="bold">2. Fixed, dedicated homophones</text>
<text x="16" y="276" font-size="13">Best expected frequency mismatch</text>
<text x="16" y="310" font-size="26" font-weight="bold">4,802</text>
<text x="116" y="307" font-size="13">model minimum</text>
<text x="16" y="348" font-size="26" font-weight="bold">26</text>
<text x="116" y="345" font-size="13">observed in LP2</text>
<text x="16" y="387" font-size="13">Only these specified rules were tested.</text>
</g></svg>\n'''


def main():
    output = HERE / 'comparison.svg'
    svg = draw()
    if '--check' in sys.argv:
        assert output.read_text(encoding='utf-8') == svg
    else:
        output.write_text(svg, encoding='utf-8', newline='\n')
    print('PASS: two-rule figure')


if __name__ == '__main__':
    main()
