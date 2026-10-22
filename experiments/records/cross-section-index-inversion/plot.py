"""Render the eight-rune worked example as a source-versus-archive diagram."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render():
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    rows = result['trace'][:8]
    source = result['first_word_source_indices']
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 235" role="img" aria-labelledby="t d">',
        '<title id="t">First word of the 729-over-index proposal</title>',
        '<desc id="d">The source gives index 28 for the seventh rune, but the 29-rune zero-based alphabet gives 27. The eighth rune has index zero, so division is undefined.</desc>',
        '<rect width="980" height="235" fill="#fff"/>',
        '<text x="18" y="28" font-family="Arial,sans-serif" font-size="17" fill="#233642">First word: claimed indices and archived rune values</text>',
        '<text x="18" y="72" font-family="Arial,sans-serif" font-size="13" fill="#34444f">Rune</text>',
        '<text x="18" y="107" font-family="Arial,sans-serif" font-size="13" fill="#34444f">GP prime</text>',
        '<text x="18" y="142" font-family="Arial,sans-serif" font-size="13" fill="#34444f">Claimed index</text>',
        '<text x="18" y="177" font-family="Arial,sans-serif" font-size="13" fill="#34444f">Actual index</text>',
        '<text x="18" y="212" font-family="Arial,sans-serif" font-size="13" fill="#34444f">Literal result</text>',
    ]
    for i, row in enumerate(rows):
        x = 184 + i * 98
        fill = '#f4e5c6' if i == 6 else '#f5dfdc' if i == 7 else '#edf2f4'
        out.append(f'<rect x="{x}" y="50" width="94" height="171" fill="{fill}"/>')
        for y, value in [(72, row['rune']), (107, row['prime_value']),
                         (142, source[i]), (177, row['index']),
                         (212, row.get('global_wrapped_label', 'undefined'))]:
            out.append(f'<text x="{x+47}" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="15" fill="#233642">{value}</text>')
    out.append('</svg>')
    return '\n'.join(out) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = HERE / 'first-word-trace.svg'
    fresh = render()
    if args.check:
        assert path.read_text(encoding='utf-8') == fresh
        print('PASS: first-word diagram')
    else:
        path.write_text(fresh, encoding='utf-8', newline='\n')
        print('Wrote', path)


if __name__ == '__main__':
    main()
