"""Independent character scan and source-span audit for word-length reports."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
runes={x['rune'] for x in json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']}
pages=[(ROOT/f'text/lp2-{i:02d}.txt').read_text(encoding='utf-8') for i in range(56)]
text=''.join(pages).translate(str.maketrans('','','/\r\n'))
words=[];buffer=[]
for i,c in enumerate(text):
    if c in runes or (c=="'" and buffer and i+1<len(text) and text[i+1] in runes):buffer.append(c)
    elif buffer:words.append(''.join(buffer));buffer=[]
if buffer:words.append(''.join(buffer))
ledger=json.loads((ROOT/'exports/unsolved-word-tokens.json').read_text(encoding='utf-8'))
assert words==[x['token'] for x in ledger]
for ordinal,row in enumerate(ledger,1):
    assert row['ordinal']==ordinal
    a=int(row['start']['page'][-2:]);b=int(row['end']['page'][-2:]);lo=row['start']['offset'];hi=row['end']['offset_exclusive']
    fragment=pages[a][lo:hi] if a==b else pages[a][lo:]+''.join(pages[a+1:b])+pages[b][:hi]
    assert fragment.translate(str.maketrans('','','/\r\n'))==row['token']
    assert sum(c in runes for c in row['token'])==row['rune_length']
report=json.loads((ROOT/'exports/unsolved-word-lengths.json').read_text(encoding='utf-8'))
assert len(words)==2896 and sum(c in runes for c in text)==12956
for item in report['standalone_single_digits']:
    source=pages[int(item['location']['page'][-2:])]
    assert source[item['location']['offset']]==item['token']
assert [x['token'] for x in report['standalone_single_digits']]==['7','1','2','3','4','5']
assert report['all_historical_fields_match'] and all(report['historical_comparisons'].values())
print('PASS: independent 2896-token scan, all original source spans, 12956 rune count and six digit locations')
