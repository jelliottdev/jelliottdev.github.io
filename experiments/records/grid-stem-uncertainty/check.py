"""Independent page-record and combination check for the I/l grid audit."""
from collections import Counter
import csv
from itertools import product
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPORT = json.loads((HERE/'results.json').read_text(encoding='utf-8'))
ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx'


def value(token):
    answer = ALPHABET.find(token[0])*60 + ALPHABET.find(token[1])
    assert answer <= 255
    return answer


entries = []
for page, expected_rows in ((49,10),(50,13),(51,9)):
    raw=json.loads((ROOT/f'data/pages/lp2-{page:02}.json').read_text(encoding='utf-8'))['raw']
    rows=[]
    for line in raw.splitlines():
        if re.fullmatch(r'[A-Za-z0-9]{2}(?:-[A-Za-z0-9]{2}){7}/?',line):
            rows.append(line.rstrip('/').split('-'))
    assert len(rows)==expected_rows
    for row_number,row in enumerate(rows,1):
        for col_number,token in enumerate(row,1):
            entries.append((f'lp2-{page:02}',row_number,col_number,token))
assert len(entries)==256

with (ROOT/'exports/alphanumeric-grids.csv').open(encoding='utf-8',newline='') as f:
    csv_entries=list(csv.DictReader(f))
for i,(page,row,col,token) in enumerate(entries):
    item=csv_entries[i]
    assert (item['page'],int(item['row']),int(item['column']),item['token'],int(item['sequence'])) == (page,row,col,token,i+1)

stem_positions=[i for i,item in enumerate(entries) if item[3][-1] in ('I','l')]
assert len(stem_positions)==10
for position,cell in zip(stem_positions,REPORT['stem_cells']):
    page,row,col,token=entries[position]
    assert (cell['page'],cell['row'],cell['column'],cell['sequence'],cell['wiki_token']) == (page,row,col,position+1,token)
    assert cell['alternatives']==[token[0]+'I',token[0]+'l']
    assert cell['base60_bytes']==[value(t) for t in cell['alternatives']]
    assert cell['differing_bits']==(cell['base60_bytes'][0]^cell['base60_bytes'][1]).bit_count()

variant_by_mask={item['mask']:item for item in REPORT['variants']}
assert len(variant_by_mask)==1024
for choices in product((0,1),repeat=10):
    mask=sum(bit<<i for i,bit in enumerate(choices))
    candidate=[item[3] for item in entries]
    for position,bit in zip(stem_positions,choices):
        candidate[position]=candidate[position][0]+('l' if bit else 'I')
    bytes_=[value(token) for token in candidate]
    expected={'mask':mask,'distinct_tokens':len(Counter(candidate)),
              'one_bits':sum(bin(v).count('1') for v in bytes_),
              'even_bytes':sum(not (v&1) for v in bytes_)}
    assert variant_by_mask[mask]==expected
for metric in ('distinct_tokens','one_bits','even_bytes'):
    all_values=[entry[metric] for entry in REPORT['variants']]
    assert REPORT['ranges'][metric]==[min(all_values),max(all_values)]
print('Independent page-record parser and all 1024 byte inventories agree.')
