"""Trace three declared routes through an invented 3-by-4 layout."""
from collections import Counter
from pathlib import Path
import json
import math

ROOT = Path(__file__).resolve().parents[1]


def build():
    routes = {
        'Row first': list(range(12)),
        'Column first': [4*r+c for c in range(4) for r in range(3)],
        'Alternating rows': [4*r+c for r in range(3)
                             for c in (range(4) if r % 2 == 0 else range(3, -1, -1))]
    }
    source = [0, 0, 1, 2, 1, 0, 3, 3, 2, 1, 0, 2]
    records = []
    for name, order in routes.items():
        assert sorted(order) == list(range(12))
        output = [source[i] for i in order]
        inverse = [None] * 12
        for i, source_position in enumerate(order):
            inverse[source_position] = output[i]
        assert inverse == source and Counter(output) == Counter(source)
        ragged = [i for i in order if i < 10]
        assert sorted(ragged) == list(range(10))
        records.append(dict(name=name, positions=order, output=output,
                            ten_cell_positions_without_padding=ragged))
    assert routes['Column first'] == [0, 4, 8, 1, 5, 9, 2, 6, 10, 3, 7, 11]
    assert routes['Alternating rows'] == [0, 1, 2, 3, 7, 6, 5, 4, 8, 9, 10, 11]
    data = dict(scope='Invented position-trace illustration, not an LP experiment.',
                rows=3, columns=4, source=source, routes=records)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 710" role="img" aria-labelledby="title desc">',
           '<title id="title">Three routes through the same twelve positions</title>',
           '<desc id="desc">Each grid numbers original positions zero through eleven. Arrows compare row-first, column-first and alternating-row traversal. Dashed connections jump between the ends of rows or columns. Exact readout orders appear beneath each grid.</desc>',
           '<rect width="360" height="710" fill="white"/>',
           '<defs><marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" fill="#526f7e"/></marker></defs>',
           '<style>text{font:14px Arial,sans-serif;fill:#253d49}.head{font-size:16px;font-weight:bold}.small{font-size:12px}</style>']
    for panel, record in enumerate(records):
        top = panel * 220
        svg.append(f'<text x="16" y="{top+28}" class="head">{record["name"]}</text>')
        centers = [(65+(i%4)*76, top+65+(i//4)*48) for i in range(12)]
        for a, b in zip(record['positions'], record['positions'][1:]):
            x1, y1 = centers[a]; x2, y2 = centers[b]
            dx, dy = x2-x1, y2-y1
            length = math.hypot(dx, dy)
            sx, sy = x1+18*dx/length, y1+18*dy/length
            ex, ey = x2-20*dx/length, y2-20*dy/length
            dashed = ' stroke-dasharray="4 3"' if dx and dy else ''
            svg.append(f'<path d="M{sx:.2f} {sy:.2f} L{ex:.2f} {ey:.2f}" fill="none" stroke="#526f7e" stroke-width="1.5" marker-end="url(#arrow)"{dashed}/>')
        for i, (x, y) in enumerate(centers):
            svg.extend([f'<circle cx="{x}" cy="{y}" r="17" fill="#fff" stroke="#bdc9d0"/>',
                        f'<text x="{x}" y="{y+5}" text-anchor="middle">{i}</text>'])
        # Two explicit lines retain legible labels at phone width.
        first = ' → '.join(map(str, record['positions'][:6]))
        second = ' → '.join(map(str, record['positions'][6:]))
        svg.extend([f'<text x="16" y="{top+195}" class="small">{first} →</text>',
                    f'<text x="16" y="{top+213}" class="small">{second}</text>'])
    svg.extend(['<text x="16" y="686" class="small">Numbers are source positions, not rune values.</text>',
                '<text x="16" y="704" class="small">Dashed arrows connect row or column ends.</text>', '</svg>'])
    (ROOT/'exports/route-order-example.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'exports/figures/route-order-example.svg').write_text('\n'.join(svg)+'\n',encoding='utf-8',newline='\n')
    print('Verified three full permutations, inverse restoration, count preservation and ten-cell selections.')


if __name__ == '__main__':
    build()
