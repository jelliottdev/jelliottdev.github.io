"""Illustrate four saved candidate positions, without treating them as plaintext."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
baseline = json.loads((HERE.parent/'lp2-prime-minus-one-openings/results.json').read_text(encoding='utf-8'))
variant = json.loads((HERE/'results.json').read_text(encoding='utf-8'))
select = lambda data: next(c for c in data['cases']
                          if c['page'] == 'lp2-00' and c['offset'] == 0 and c['sign'] == -1)
before, after = select(baseline)['output_indices'][:4], select(variant)['output_indices'][:4]
assert after == [(v-1) % 29 for v in before]
svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 350" role="img" aria-labelledby="title desc">',
       '<title id="title">Primes versus primes minus one</title>',
       '<desc id="desc">First four saved LP2-00 candidate indices, offset zero and subtraction. Every ordinary-prime output is one index below the baseline, modulo 29. Neither candidate is a known reading.</desc>',
       '<rect width="440" height="350" fill="#f7f7f3"/>',
       '<g font-family="sans-serif" fill="#263b46">',
       '<text x="20" y="31" font-size="21">One position lower, modulo 29</text>',
       '<text x="20" y="58" font-size="16">LP2-00 · offset 0 · subtraction</text>',
       '<text x="20" y="94" font-size="17">Primes − 1</text>',
       '<text x="279" y="94" font-size="17">Primes</text>']
for i, (a, b) in enumerate(zip(before, after)):
    y = 131+i*43
    svg += [f'<path d="M20 {y+10}H420" stroke="#d7dddf"/>',
            f'<text x="60" y="{y}" font-size="21">{a}</text>',
            f'<text x="176" y="{y}" font-size="17">− 1 →</text>',
            f'<text x="303" y="{y}" font-size="21">{b}</text>']
svg += ['<text x="20" y="304" font-size="16">These are candidate alphabet indices,</text>',
        '<text x="20" y="328" font-size="16">not a known reading or a new solution.</text>',
        '</g></svg>']
(HERE/'comparison.svg').write_text('\n'.join(svg)+'\n', encoding='utf-8', newline='\n')
print('comparison.svg generated from saved candidate indices.')
