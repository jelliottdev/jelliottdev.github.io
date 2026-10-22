"""Independent line-split and streaming-token replay of all source differences."""
from collections import Counter
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
saved=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
alphabet={item['rune'] for item in json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']}

raw=(ROOT/'exports/sources/cicada-2014-seventh-onion/0-55.jpg.runes.txt').read_text(encoding='utf-8')
blocks=[];lines=[]
for line in raw.splitlines(keepends=True):
    if line.strip()=='%':
        blocks.append(''.join(lines).strip('\r\n'))
        lines=[]
    else:
        lines.append(line)
blocks.append(''.join(lines).strip('\r\n'))
assert len(blocks)==56
wiki=[(ROOT/f'text/lp2-{n:02d}.txt').read_text(encoding='utf-8').strip('\r\n') for n in range(56)]

def parts(text):
    gaps=[''];runes=[]
    for char in text:
        if char in alphabet:
            runes.append(char);gaps.append('')
        else:
            gaps[-1]+=char
    return runes,gaps

def scan(pages):
    chars=''.join(''.join(char for char in page if char not in '/\r\n') for page in pages)
    starts=[];lengths=[];current=-1;rune_ordinal=0;active=False
    for i,char in enumerate(chars):
        if char in alphabet:
            if not active:
                starts.append(rune_ordinal);lengths.append(0);current+=1;active=True
            lengths[current]+=1;rune_ordinal+=1
        elif char=="'" and active and i+1<len(chars) and chars[i+1] in alphabet:
            pass
        else:
            active=False
    hist=Counter(lengths)
    return {'runes':rune_ordinal,'tokens':len(lengths),'starts':starts,
            'histogram':{str(k):v for k,v in sorted(hist.items())},
            'long_tokens_10_plus':sum(n>=10 for n in lengths),
            'eleven_eleven_ten_windows':sum(lengths[i:i+3]==[11,11,10] for i in range(len(lengths)-2))}

baseline=scan(wiki);source=scan(blocks)
for name,result in [('wiki',baseline),('source',source)]:
    assert {k:v for k,v in result.items() if k!='starts'}==saved[name]
assert baseline['starts']==source['starts']
assert baseline['runes']==source['runes']==12956
assert baseline['tokens']==source['tokens']==2896
assert not saved['complete_source_added_token_starts']
assert not saved['complete_source_removed_token_starts']

seen=[];global_ordinal=0
for n,(old,new) in enumerate(zip(blocks,wiki)):
    old_runes,old_gaps=parts(old)
    new_runes,new_gaps=parts(new)
    assert old_runes==new_runes
    for ordinal,(a,b) in enumerate(zip(old_gaps,new_gaps)):
        if a!=b:
            seen.append((n,ordinal,global_ordinal+ordinal,a,b,new_runes,new_gaps))
    global_ordinal+=len(new_runes)
assert len(seen)==saved['non_rune_differences']==33
for details,row in zip(seen,saved['one_gap_variants']):
    n,ordinal,global_position,old_gap,new_gap,runes,gaps=details
    assert (row['page'],row['before_page_rune_ordinal'],row['before_global_rune_ordinal'])==(f'lp2-{n:02d}',ordinal,global_position)
    assert (row['source_gap'],row['wiki_gap'])==(old_gap,new_gap)
    modified=gaps.copy();modified[ordinal]=old_gap
    hybrid=wiki.copy()
    hybrid[n]=''.join(gap+rune for gap,rune in zip(modified,runes))+modified[-1]
    result=scan(hybrid)
    added=set(result['starts'])-set(baseline['starts'])
    removed=set(baseline['starts'])-set(result['starts'])
    assert row['added_token_starts']==sorted(added)==[]
    assert row['removed_token_starts']==sorted(removed)==[]
    assert row['token_count']==result['tokens']==2896
    assert row['token_count_delta']==0
    assert row['long_tokens_10_plus']==result['long_tokens_10_plus']==109
    assert row['eleven_eleven_ten_windows']==result['eleven_eleven_ten_windows']==1
    assert row['histogram_changes']=={}
print('PASS: independent page split and streaming tokenizer verify all 33 one-gap variants and invariant token starts')
