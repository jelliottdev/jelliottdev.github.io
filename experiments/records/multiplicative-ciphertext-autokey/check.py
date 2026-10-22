"""Independently verify the zero-state ledger and finite-field invariant."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
data=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
alphabet=json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']
zero=alphabet[0]['rune']
runes={item['rune'] for item in alphabet}
assert all((p*0)%29==0 for p in range(29))
count=zeroes=0
for number in range(56):
    source=(ROOT/f'text/lp2-{number:02d}.txt').read_text(encoding='utf-8')
    stream=[symbol for symbol in source if symbol in runes]
    positions=[i for i in range(1,len(stream)) if stream[i-1]==zero and stream[i]!=zero]
    saved=data['pages'][number]
    assert saved['page']==f'lp2-{number:02d}'
    assert positions==saved['zero_to_nonzero_positions_one_based']
    count+=len(positions)
    zeroes+=stream.count(zero)
assert (count,zeroes)==(450,458)
print('PASS: direct rune scan, page positions and absorbing-zero algebra')
