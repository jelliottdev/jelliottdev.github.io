"""Independent streaming parser on page-record raw fields."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
data=json.loads((HERE/'results.json').read_text(encoding='utf8'))
alphabet=json.loads((ROOT/'data/index.json').read_text(encoding='utf8'))['alphabet']
lookup={entry['rune']:i for i,entry in enumerate(alphabet)}
pages=[]
for n in range(56):
    source=json.loads((ROOT/f'data/pages/lp2-{n:02}.json').read_text(encoding='utf8'))['raw']
    assert source==(ROOT/f'text/lp2-{n:02}.txt').read_text(encoding='utf8')
    pages.append(source)

def parse(separate):
    tokens=[]
    current=[]
    for n,page in enumerate(pages):
        if separate and n and current:
            tokens.append(current);current=[]
        for c in page:
            if c in '-.':
                if current:tokens.append(current);current=[]
            elif c in lookup:
                current.append(lookup[c])
    if current:tokens.append(current)
    return tokens

def measure(tokens):
    lag_pairs=[(w[i],w[i+6]) for w in tokens for i in range(len(w)-6)]
    adjacent=[(w[i],w[i+1]) for w in tokens for i in range(len(w)-1)]
    return {'tokens':len(tokens),'runes':sum(map(len,tokens)),
            'lag_six_opportunities':len(lag_pairs),
            'lag_six_matches':sum((24-2*a)%29==b for a,b in lag_pairs),
            'adjacent_opportunities':len(adjacent),
            'adjacent_doublets':sum(a==b for a,b in adjacent),
            'maximum_word_runes':max(map(len,tokens))}

assert measure(parse(True))==data['split_pages']
assert measure(parse(False))==data['joined_pages']
assert len(data['boundary_details'])==55
assert sum(row['rune_to_rune'] for row in data['boundary_details'])==32
print('Page-record raw fields and an independent streaming parser reproduce both variants.')
