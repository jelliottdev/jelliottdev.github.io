"""Infer partial arbitrary feedback tables from fixed twelve-rune openings."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ALPHABET='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
INDEX={ch:i for i,ch in enumerate(ALPHABET)}
Q=29


def infer(cipher,plain,mode,q=Q):
    """Return the implied function entries, conflict count, and extension count."""
    assert len(plain)==12 and len(cipher)>=24
    table={}
    conflicts=0
    for i in range(1,12):
        source=cipher[i-1] if mode=='ciphertext' else plain[i-1]
        target=(cipher[i]-plain[i])%q
        if source in table and table[source]!=target:
            conflicts+=1
        else:
            table[source]=target
    count=0 if conflicts else q**(q-len(table))
    return table,conflicts,count


def forward(cipher,plain,mode,table):
    """Coverage of next twelve positions, not comparison to unknown plaintext."""
    if mode=='ciphertext':
        determined=[i for i in range(12,24) if cipher[i-1] in table]
        return {'determined_positions':determined,'determined_count':len(determined)}
    prev=plain[-1]
    chain=0
    for i in range(12,24):
        if prev not in table:
            break
        prev=(cipher[i]-table[prev])%Q
        chain+=1
    return {'sequential_prefix_length':chain,'first_unconstrained_position':12+chain if chain<12 else None}


def inputs():
    plan=json.loads((ROOT/'experiments/records/lp2-known-vigenere-keys/plan.json').read_text(encoding='utf-8'))
    openings=[(o['id'],o['indices']) for o in plan['openings']]
    pages=[]
    for number in range(56):
        page_id=f'lp2-{number:02d}'
        raw=(ROOT/'text'/f'{page_id}.txt').read_text(encoding='utf-8')
        runes=[INDEX[ch] for ch in raw if ch in INDEX]
        if runes:
            assert len(runes)>=24
            pages.append((page_id,runes[:24]))
    assert len(openings)==9 and len(pages)==55
    return pages,openings


def make_results():
    pages,openings=inputs()
    cases=[]
    summary={}
    for mode in ('ciphertext','plaintext'):
        assigned=Counter()
        conflicts=Counter()
        forward_counts=Counter()
        compatible=0
        for page_id,cipher in pages:
            for opening_id,plain in openings:
                table,conflict_count,key_count=infer(cipher,plain,mode)
                case={'mode':mode,'page':page_id,'opening':opening_id,
                      'assigned_entry_count':len(table),'conflict_count':conflict_count,
                      'compatible_full_table_count':key_count}
                if key_count:
                    compatible+=1
                    case['forward_coverage']=forward(cipher,plain,mode,table)
                    count=case['forward_coverage'].get('determined_count',case['forward_coverage'].get('sequential_prefix_length'))
                    forward_counts[str(count)]+=1
                cases.append(case)
                assigned[str(len(table))]+=1
                conflicts[str(conflict_count)]+=1
        summary[mode]={'cases':len(pages)*len(openings),'consistent_cases':compatible,
                       'conflicting_cases':len(pages)*len(openings)-compatible,
                       'assigned_entries_histogram':dict(sorted(assigned.items(),key=lambda p:int(p[0]))),
                       'conflict_count_histogram':dict(sorted(conflicts.items(),key=lambda p:int(p[0]))),
                       'forward_coverage_histogram_consistent_only':dict(sorted(forward_counts.items(),key=lambda p:int(p[0])))}
    plan_sha=hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest()
    return {'schema':'liberpedia-crib-inferred-feedback-table-results-v1','plan_sha256':plan_sha,
            'page_count':len(pages),'opening_count':len(openings),'total_cases':len(cases),
            'summary':summary,'cases':cases}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=make_results()
    if args.check:
        assert result==json.loads((HERE/'results.json').read_text(encoding='utf-8'))
        print('PASS: feedback table inference matches stored results')
    else:
        (HERE/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps(result['summary'],indent=2))
