"""Generate a compact diagram of the measured uniform family collapse."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def figure():
    r = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    b, c = r['baseline'], r['collapsed']
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 460" role="img" aria-labelledby="title desc">
<title id="title">What happens if O, A and AE are written as one rune?</title>
<desc id="desc">On the 13,136-rune source stream, equal neighbors rise from {b['adjacent_equal']} to {c['adjacent_equal']}. IoC on a fixed 29-symbol scale rises from {b['fixed29_ioc']:.2f} to {c['fixed29_ioc']:.2f}. This is a uniform relabeling, not a decipherment.</desc>
<rect width="600" height="460" fill="white"/>
<g font-family="Arial, sans-serif" fill="#20262c">
<text x="24" y="34" font-size="23" font-weight="bold">Treating three rune types as one</text>
<text x="24" y="65" font-size="19">All 27 uniform maps checked · source text</text>
<g font-size="24" text-anchor="middle"><text x="65" y="123">O</text><text x="145" y="123">A</text><text x="225" y="123">AE</text><text x="482" y="123">O</text></g>
<path d="M275 114H411m-13-10 13 10-13 10" fill="none" stroke="#687780" stroke-width="3"/>
<path d="M28 140H253M446 140H519" stroke="#c4cbd0" stroke-width="2"/>
<text x="24" y="186" font-size="22" font-weight="bold">Equal neighboring runes</text>
<text x="24" y="225" font-size="21">Original</text><rect x="185" y="205" width="{b['adjacent_equal'] * 1.65:.1f}" height="25" fill="#7b8992"/><text x="{199 + b['adjacent_equal'] * 1.65:.1f}" y="225" font-size="22">{b['adjacent_equal']}</text>
<text x="24" y="267" font-size="21">Merged</text><rect x="185" y="247" width="{c['adjacent_equal'] * 1.65:.1f}" height="25" fill="#315e74"/><text x="{199 + c['adjacent_equal'] * 1.65:.1f}" y="267" font-size="22">{c['adjacent_equal']}</text>
<text x="24" y="321" font-size="22" font-weight="bold">Frequency concentration (IoC × 29)</text>
<text x="24" y="358" font-size="23">Original {b['fixed29_ioc']:.2f}</text><text x="300" y="358" font-size="23">Merged {c['fixed29_ioc']:.2f}</text>
<path d="M24 382H576" stroke="#d7dce0"/>
<text x="24" y="413" font-size="19">13,136 runes · includes the two solved LP2 pages</text>
<text x="24" y="443" font-size="19">A label change measures sensitivity; it does not decode.</text>
</g></svg>'''


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true')
    args = p.parse_args()
    svg = figure()
    path = HERE / 'collapse.svg'
    if args.check:
        assert path.read_text(encoding='utf-8') == svg
        print('PASS: measured labels and figure bytes')
    else:
        path.write_text(svg, encoding='utf-8', newline='\n')
