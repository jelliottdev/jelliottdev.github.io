"""Render a compact alignment of the archived and reported digit sequences."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render():
    data = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    rows = data['alignment']
    assert len(rows) == 57
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 178" role="img" aria-labelledby="t d">',
        '<title id="t">Reported and archived prime-distance digits</title>',
        '<desc id="d">57 archived word distances aligned with 53 reported digits. Pale columns agree; ochre columns show one minimum alignment with four gaps and three substitutions.</desc>',
        '<rect width="1120" height="178" fill="#fff"/>',
        '<text x="14" y="30" font-family="Arial,sans-serif" font-size="15" fill="#253744">LP2-15–16 prime-distance words</text>',
        '<text x="14" y="76" font-family="Arial,sans-serif" font-size="13" fill="#253744">Archive</text>',
        '<text x="14" y="111" font-family="Arial,sans-serif" font-size="13" fill="#253744">Report</text>',
    ]
    for i, row in enumerate(rows):
        x = 118 + i * 17
        fill = '#edf2f4' if row['same'] else '#f3e2bb'
        parts.append(f'<rect x="{x}" y="49" width="16" height="72" fill="{fill}"/>')
        a = '·' if row['archived_digit'] is None else str(row['archived_digit'])
        b = '·' if row['reported_digit'] is None else str(row['reported_digit'])
        parts.append(f'<text x="{x+8}" y="75" text-anchor="middle" font-family="ui-monospace,Consolas,monospace" font-size="15" fill="#253744">{a}</text>')
        parts.append(f'<text x="{x+8}" y="110" text-anchor="middle" font-family="ui-monospace,Consolas,monospace" font-size="15" fill="#253744">{b}</text>')
        if i % 10 == 0:
            parts.append(f'<text x="{x}" y="139" font-family="Arial,sans-serif" font-size="10" fill="#68747c">{i+1}</text>')
    parts.extend([
        '<rect x="118" y="151" width="12" height="12" fill="#edf2f4"/>',
        '<text x="136" y="161" font-family="Arial,sans-serif" font-size="11" fill="#47545b">same digit</text>',
        '<rect x="228" y="151" width="12" height="12" fill="#f3e2bb"/>',
        '<text x="246" y="161" font-family="Arial,sans-serif" font-size="11" fill="#47545b">gap or difference; alignment is not unique</text>',
        '</svg>'
    ])
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = HERE / 'word-distance-alignment.svg'
    fresh = render()
    if args.check:
        assert path.read_text(encoding='utf-8') == fresh
        print('PASS: saved alignment chart')
    else:
        path.write_text(fresh, encoding='utf-8', newline='\n')
        print('Wrote', path)


if __name__ == '__main__':
    main()
