"""Draw the verified Fibonacci residue cycle from the saved result."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE/'results.json').read_text(encoding='utf-8'))
cycle = result['residue_cycle']
assert len(cycle) == result['residue_period'] == 14
parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 330" role="img" aria-labelledby="title desc">',
         '<title id="title">Fibonacci remainders repeat after 14 terms</title>',
         '<desc id="desc">Read each row left to right: the remainders at offsets 0 through 13 are '
         + ', '.join(map(str, cycle)) + '. Offsets 14 and 15 return to 0 and 1.</desc>',
         '<rect width="440" height="330" fill="#f7f7f3"/>',
         '<g font-family="sans-serif" fill="#263b46">',
         '<text x="18" y="32" font-size="21">Fibonacci shifts modulo 29</text>',
         '<text x="18" y="59" font-size="16">Offset above; applied remainder below</text>']
for i, value in enumerate(cycle):
    x, y = 19+(i % 7)*58, 78+(i//7)*79
    parts.extend([f'<rect x="{x}" y="{y}" width="52" height="69" fill="white" stroke="#d7dddf"/>',
                  f'<text x="{x+26}" y="{y+22}" text-anchor="middle" font-size="14">{i}</text>',
                  f'<text x="{x+26}" y="{y+52}" text-anchor="middle" font-size="22">{value}</text>'])
parts.extend(['<text x="18" y="265" font-size="18">Offsets 14 and 15 return to 0, 1.</text>',
              '<text x="18" y="291" font-size="16">The repeated pair restarts the cycle.</text>',
              '<text x="18" y="317" font-size="16">Offsets 0, 14 and 28 give the same shifts.</text>',
              '</g></svg>'])
(HERE/'cycle.svg').write_text('\n'.join(parts)+'\n', encoding='utf-8', newline='\n')
print('cycle.svg generated from verified result residues.')
