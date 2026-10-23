"""Measure the visually delimited LP2-53 red span without proposing a key."""
import argparse
import csv
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ALPHABET='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
INDEX={ch:i for i,ch in enumerate(ALPHABET)}
WIDTH=51


def source():
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    for entry in plan['inputs']:
        data=(ROOT/entry['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==entry['sha256'],entry['path']
    page=json.loads((ROOT/'data/pages/lp2-53.json').read_text(encoding='utf-8'))
    lines=[[INDEX[ch] for ch in line['raw'] if ch in INDEX] for line in page['lines']]
    assert [len(line) for line in lines]==[22,22,20,23,23,19,24,22,4]
    red=[lines[5][-1]]+lines[6]+lines[7]+lines[8]
    black=[v for line in lines[:5] for v in line]+lines[5][:-1]
    assert len(red)==51 and len(black)==128
    all_runes=[v for line in lines for v in line]
    assert red==all_runes[128:179]
    return plan,black,red


def metric(values):
    assert len(values)==WIDTH
    counts=Counter(values)
    equal_unordered_pairs=sum(value*(value-1) for value in counts.values())
    adjacent=sum(a==b for a,b in zip(values,values[1:]))
    return {'ioc_pair_numerator':equal_unordered_pairs,'ioc':equal_unordered_pairs/(WIDTH*(WIDTH-1)),
            'adjacent_equal_pairs':adjacent,'unique_runes':len(counts)}


def readings(plan):
    groups=[]
    for item in plan['inputs']:
        name=item['path']
        if not name.startswith('exports/readings/') or not name.endswith('.csv'):
            continue
        with (ROOT/name).open(encoding='utf-8',newline='') as handle:
            indices=[int(row['output_index']) for row in csv.DictReader(handle)]
        assert len(indices)>=WIDTH and all(0<=value<29 for value in indices)
        groups.append((Path(name).stem,indices))
    assert len(groups)==8
    return groups


def windows(groups):
    return [{'source':name,'start':start,**metric(indices[start:start+WIDTH])}
            for name,indices in groups for start in range(len(indices)-WIDTH+1)]


def distribution(window_rows,red):
    out={'window_count':len(window_rows)}
    for key in ('ioc_pair_numerator','adjacent_equal_pairs','unique_runes'):
        sorted_values=sorted(row[key] for row in window_rows)
        n=len(sorted_values)
        out[key]={'minimum':sorted_values[0],
                  'median':(sorted_values[(n-1)//2]+sorted_values[n//2])/2,
                  'maximum':sorted_values[-1],
                  'at_or_below_red':sum(value<=red[key] for value in sorted_values),
                  'at_or_above_red':sum(value>=red[key] for value in sorted_values)}
    return out


def make_results():
    plan,black,red=source()
    red_metric=metric(red)
    reading_groups=readings(plan)
    solved=windows(reading_groups)
    black_windows=windows([('lp2-53-black-prefix',black)])
    rng=random.Random(330153)
    shuffled_adjacent=[]
    for _ in range(10000):
        values=red[:]
        rng.shuffle(values)
        shuffled_adjacent.append(sum(a==b for a,b in zip(values,values[1:])))
    histogram=Counter(shuffled_adjacent)
    rune_text=''.join(ALPHABET[value] for value in red)
    return {'schema':'liberpedia-lp2-53-red-equality-invariants-results-v1',
            'plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),
            'red_rune_sha256':hashlib.sha256(rune_text.encode('utf-8')).hexdigest(),
            'red_start_ordinal':128,'red_length':WIDTH,'black_prefix_length':len(black),
            'red':red_metric,
            'solved_sections':[{'name':name,'runes':len(indices)} for name,indices in reading_groups],
            'solved_windows':distribution(solved,red_metric),
            'same_page_black_windows':distribution(black_windows,red_metric),
            'red_shuffle':{'trials':10000,'seed':330153,
                           'adjacent_count_histogram':dict(sorted(((str(k),v) for k,v in histogram.items()),key=lambda x:int(x[0]))),
                           'at_or_below_observed':sum(v<=red_metric['adjacent_equal_pairs'] for v in shuffled_adjacent),
                           'at_or_above_observed':sum(v>=red_metric['adjacent_equal_pairs'] for v in shuffled_adjacent)}}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=make_results()
    if args.check:
        assert result==json.loads((HERE/'results.json').read_text(encoding='utf-8'))
        print('PASS: LP2-53 red equality-invariant results match stored report')
    else:
        (HERE/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps({key:result[key] for key in ('red','solved_windows','same_page_black_windows','red_shuffle')},indent=2))
