"""Render the saved control measurements; --check never writes expectations."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render():
    data = json.loads((HERE / 'controls-visual-data.json').read_bytes())
    assert hashlib.sha256((HERE / 'controls-results.json').read_bytes()).hexdigest() == data['hashes']['results_sha256']
    rows = data['rows']
    assert [(r['classes'], r['suppress']) for r in rows] == [(12, 0), (12, .9), (18, .9)]
    assert all(not r['exact_recovery'] and r['source_z_gate'] == 3 for r in rows)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 790" width="360" height="790" role="img" aria-labelledby="title desc">',
           '<title id="title">Three known synthetic controls missed both detection gates</title>',
           '<desc id="desc">Search-score and held-out z values are below the required value of three for all three controls. No complete class stream was recovered. No manuscript target was scored.</desc>',
           '<rect width="360" height="790" fill="white"/>',
           '<g fill="#242424" font-family="Arial,sans-serif" font-size="20">',
           '<text x="20" y="32" font-size="23">Three known controls</text>',
           '<text x="20" y="62" font-size="23">missed both gates</text>',
           '<text x="20" y="100">Pass requires z &gt; 3.</text>',
           '<circle cx="27" cy="139" r="6" fill="#303030"/><text x="44" y="146">Search-score z</text>',
           '<circle cx="27" cy="173" r="6" fill="#999999"/><text x="44" y="180">Held-out z</text>',
           '<line x1="280" y1="250" x2="280" y2="546" stroke="#777" stroke-dasharray="5 5"/>']
    for i, row in enumerate(rows):
        y = 220 + i * 120
        label = 'No repeat suppression' if row['suppress'] == 0 else 'Repeat suppression'
        svg += [f'<text x="20" y="{y}">{row["classes"]} groups</text>',
                f'<text x="20" y="{y+27}">{label}</text>',
                f'<line x1="40" y1="{y+60}" x2="320" y2="{y+60}" stroke="#e3e3e3"/>']
        for key, color, dy in [('source_partc_z', '#303030', -10), ('heldout_z', '#999999', 10)]:
            x = 40 + 80 * row[key]
            svg.append(f'<circle cx="{x:.2f}" cy="{y+60+dy}" r="6" fill="{color}"/>')
    for value in range(4):
        svg.append(f'<text x="{40+80*value}" y="580" text-anchor="middle">{value}</text>')
    svg += ['<text x="20" y="621">Higher z means stronger</text>',
            '<text x="20" y="648">separation from shuffles.</text>',
            '<text x="20" y="690">Complete class-stream</text>',
            '<text x="20" y="717">recovery: 0 of 3.</text>',
            '<text x="20" y="758">No manuscript target scored.</text>',
            '</g></svg>']
    return ('\n'.join(svg) + '\n').encode('utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    expected = render()
    path = HERE / 'control-gates.svg'
    if args.check:
        assert path.read_bytes() == expected, 'Saved chart differs; inspect before replacing.'
        print('PASS: saved chart matches the recorded control values.')
    else:
        path.write_bytes(expected)
