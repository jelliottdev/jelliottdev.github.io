"""Draw the bounded keyword-plus-stream outcome at phone size."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def draw():
    d = json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    assert d['candidate_count'] == 224128
    assert d['source_screen_hit_count'] == 0
    best = d['best']['best_ioc']
    control = d['known_reading_control']['recovered_ioc']
    assert abs(best - 1.290220385674931) < 1e-12
    assert abs(control - 1.7230629745759511) < 1e-12
    left, scale = 18, 165
    x = lambda score: left + score * scale
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 310" role="img" aria-labelledby="title desc">
<title id="title">Keyword and prime-stream grid check</title>
<desc id="desc">The best LP2 score is 1.29, below the source's 1.4 screen. The planted known reading scores 1.72. Forty-two of 49 page-shuffle trials had a maximum at least as high as the LP2 maximum.</desc>
<rect width="340" height="310" fill="#f5f6f7"/>
<g font-family="Arial, sans-serif" fill="#263944">
<text x="16" y="29" font-size="17" font-weight="bold">Keyword + stream search</text>
<text x="16" y="52" font-size="13">224,128 settings · current LP2-04–37</text>
<text x="16" y="91" font-size="14" font-weight="bold">Best LP2 score</text>
<rect x="18" y="102" width="{best*scale:.1f}" height="17" fill="#426c83"/>
<text x="238" y="117" font-size="14">{best:.2f}</text>
<text x="16" y="153" font-size="14" font-weight="bold">Known-reading control</text>
<rect x="18" y="164" width="{control*scale:.1f}" height="17" fill="#779aa9"/>
<text x="304" y="179" font-size="14">{control:.2f}</text>
<line x1="{x(1.4):.1f}" y1="91" x2="{x(1.4):.1f}" y2="187" stroke="#526773" stroke-dasharray="4 4"/>
<text x="16" y="213" font-size="13">Source screen: IoC above 1.40</text>
<line x1="16" y1="230" x2="324" y2="230" stroke="#ccd4d8"/>
<text x="16" y="258" font-size="14" font-weight="bold">0 LP2 settings crossed it.</text>
<text x="16" y="285" font-size="13">42 of 49 shuffles peaked at least as high.</text>
</g></svg>\n'''


def main():
    path = HERE/'comparison.svg'
    svg = draw()
    if '--check' in sys.argv:
        assert path.read_text(encoding='utf-8') == svg
    else:
        path.write_text(svg, encoding='utf-8', newline='\n')
    print('PASS: phone-size grid figure')


if __name__ == '__main__':
    main()
