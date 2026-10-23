"""Independent page-text and decoded-trace check of substitution invariants."""
import csv
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RUNES='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
TO_INDEX={ch:i for i,ch in enumerate(RUNES)}


def measure(sequence):
    # Deliberately count equal position pairs, not histogram products.
    same=2*sum(sequence[i]==sequence[j]
               for i in range(len(sequence)) for j in range(i+1,len(sequence)))
    adjacent=sum(sequence[i]==sequence[i+1] for i in range(len(sequence)-1))
    return {'ioc_pair_numerator':same,'ioc':same/2550,
            'adjacent_equal_pairs':adjacent,'unique_runes':len(set(sequence))}


def summarize(sequences,red):
    values=[measure(v) for v in sequences]
    out={'window_count':len(values)}
    for field in ('ioc_pair_numerator','adjacent_equal_pairs','unique_runes'):
        ordered=sorted(v[field] for v in values)
        n=len(ordered)
        out[field]={'minimum':ordered[0],'median':(ordered[(n-1)//2]+ordered[n//2])/2,
                    'maximum':ordered[-1],
                    'at_or_below_red':sum(v<=red[field] for v in ordered),
                    'at_or_above_red':sum(v>=red[field] for v in ordered)}
    return out


def main():
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((ROOT/'images/lp2-53.jpg').read_bytes()).hexdigest()==plan['span']['source_image_sha256']
    assert hashlib.sha256((ROOT/'data/pages/lp2-53.json').read_bytes()).hexdigest()==plan['span']['page_json_sha256']
    lines=[line for line in (ROOT/'text/lp2-53.txt').read_text(encoding='utf-8').splitlines()
           if any(ch in TO_INDEX for ch in line)]
    line_runes=[[TO_INDEX[ch] for ch in line if ch in TO_INDEX] for line in lines]
    assert [len(line) for line in line_runes]==[22,22,20,23,23,19,24,22,4]
    black=[x for row in line_runes[:5] for x in row]+line_runes[5][:-1]
    red=line_runes[5][-1:]+[x for row in line_runes[6:9] for x in row]
    assert len(black)==128 and len(red)==51
    assert measure(red)==result['red']
    assert hashlib.sha256(''.join(RUNES[i] for i in red).encode('utf-8')).hexdigest()==result['red_rune_sha256']
    solved=[]
    sections=[]
    for path in sorted((ROOT/'exports/readings').glob('*.csv')):
        if path.stem=='lp2-56':
            continue
        with path.open(encoding='utf-8',newline='') as handle:
            rows=list(csv.reader(handle))
        column=rows[0].index('output_index')
        values=[int(row[column]) for row in rows[1:]]
        assert all(0<=v<29 for v in values)
        sections.append({'name':path.stem,'runes':len(values)})
        solved.extend(values[start:start+51] for start in range(len(values)-50))
    assert sections==result['solved_sections']
    assert summarize(solved,measure(red))==result['solved_windows']
    black_windows=[black[start:start+51] for start in range(78)]
    assert summarize(black_windows,measure(red))==result['same_page_black_windows']
    # All equality-based measures must survive a bijection of rune labels.
    permutation=list(range(29))
    random.Random(53).shuffle(permutation)
    assert measure(red)==measure([permutation[v] for v in red])
    rng=random.Random(330153)
    histogram=Counter()
    for _ in range(10000):
        shifted=red[:]
        rng.shuffle(shifted)
        assert measure(shifted)['ioc_pair_numerator']==measure(red)['ioc_pair_numerator']
        histogram[measure(shifted)['adjacent_equal_pairs']]+=1
    expected={str(k):v for k,v in sorted(histogram.items())}
    assert expected==result['red_shuffle']['adjacent_count_histogram']
    assert histogram[0]==result['red_shuffle']['at_or_below_observed']
    print(f"PASS: 51-rune red span, {len(solved)} solved windows, 78 black windows, 10,000 shuffles")


if __name__=='__main__':
    main()
