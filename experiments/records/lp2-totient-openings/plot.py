"""Illustrate gcd counting, checking each total against saved totient terms."""
import json
from math import gcd
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE/'results.json').read_text(encoding='utf-8'))
parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 330" role="img" aria-labelledby="title desc">',
         '<title id="title">Counting coprime integers</title>',
         '<desc id="desc">For eight, count 1, 3, 5 and 7. For nine, count 1, 2, 4, 5, 7 and 8. Crossed numbers share a divisor greater than one with the row input.</desc>',
         '<rect width="440" height="330" fill="#f7f7f3"/>',
         '<g font-family="sans-serif" fill="#263b46">',
         '<text x="18" y="32" font-size="22">What the totient counts</text>',
         '<text x="18" y="60" font-size="16">Count k when gcd(k, n) = 1.</text>']
for row, n in enumerate([8, 9]):
    y = 97 + 102*row
    counted = [k for k in range(1, n+1) if gcd(k, n) == 1]
    assert len(counted) == result['shifts'][n-1]
    parts.append(f'<text x="18" y="{y}" font-size="19">n = {n}: φ({n}) = {len(counted)}</text>')
    for k in range(1, n+1):
        x, cy = 29+(k-1)*46, y+36
        parts += [f'<circle cx="{x}" cy="{cy}" r="19" fill="white" stroke="#647b86"/>',
                  f'<text x="{x}" y="{cy+6}" text-anchor="middle" font-size="18">{k}</text>']
        if k not in counted:
            parts.append(f'<path d="M{x-15} {cy+15}L{x+15} {cy-15}" stroke="#9b4035" stroke-width="2"/>')
parts += ['<text x="18" y="289" font-size="16">Crossed numbers are not counted.</text>',
          '<text x="18" y="314" font-size="16">Coprime to n does not mean prime.</text>',
          '</g></svg>']
(HERE/'counting.svg').write_text('\n'.join(parts)+'\n', encoding='utf-8', newline='\n')
print('counting.svg generated; gcd counts match saved totients.')
