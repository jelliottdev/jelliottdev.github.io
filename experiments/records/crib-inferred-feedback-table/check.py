"""Independent set-valued constraints and exhaustive small-field function oracle."""
import itertools
import json
import random
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ALPHABET='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
LOOKUP={ch:i for i,ch in enumerate(ALPHABET)}


def constraints(cipher,plain,mode,q):
    demanded={}
    for i in range(1,12):
        source=cipher[i-1] if mode=='ciphertext' else plain[i-1]
        demanded.setdefault(source,set()).add((cipher[i]-plain[i])%q)
    consistent=all(len(values)==1 for values in demanded.values())
    resolved={k:next(iter(v)) for k,v in demanded.items() if len(v)==1}
    count=q**(q-len(demanded)) if consistent else 0
    return demanded,resolved,count


def forward_coverage(cipher,plain,mode,known,q):
    if mode=='ciphertext':
        positions=[i for i in range(12,24) if cipher[i-1] in known]
        return {'determined_positions':positions,'determined_count':len(positions)}
    state=plain[11]
    steps=0
    for i in range(12,24):
        if state not in known:
            break
        state=(cipher[i]-known[state])%q
        steps+=1
    return {'sequential_prefix_length':steps,'first_unconstrained_position':12+steps if steps<12 else None}


def exhaustive_controls():
    rng=random.Random(293301)
    tally={}
    for q in (3,5):
        functions=list(itertools.product(range(q),repeat=q))
        fixtures=[]
        for mode in ('ciphertext','plaintext'):
            for seed in range(4):
                table=functions[(seed*271+7)%len(functions)]
                plain=[rng.randrange(q) for _ in range(12)]
                cipher=[rng.randrange(q)]
                for i in range(1,12):
                    source=cipher[i-1] if mode=='ciphertext' else plain[i-1]
                    cipher.append((plain[i]+table[source])%q)
                fixtures.append((mode,cipher,plain,'planted'))
            for _ in range(8):
                cipher=[rng.randrange(q) for _ in range(12)]
                plain=[rng.randrange(q) for _ in range(12)]
                fixtures.append((mode,cipher,plain,'random'))
            # Same input demanding two outputs must be rejected.
            cipher=[0]*12
            plain=[0]*12
            plain[2]=1
            fixtures.append((mode,cipher,plain,'conflict'))
        for mode,cipher,plain,kind in fixtures:
            _,_,predicted=constraints(cipher,plain,mode,q)
            observed=0
            for function in functions:
                if all(plain[i]==(cipher[i]-function[cipher[i-1] if mode=='ciphertext' else plain[i-1]])%q for i in range(1,12)):
                    observed+=1
            assert predicted==observed,(q,mode,kind,predicted,observed)
            if kind=='planted':
                assert observed>0
            elif kind=='conflict':
                assert observed==0
        tally[str(q)]={'functions_enumerated':len(functions),'fixtures':len(fixtures)}
    return tally


def independent_census():
    result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    source=json.loads((ROOT/'experiments/records/lp2-known-vigenere-keys/plan.json').read_text(encoding='utf-8'))
    openings={o['id']:o['indices'] for o in source['openings']}
    pages={}
    for number in range(56):
        page_id=f'lp2-{number:02d}'
        page=json.loads((ROOT/'data/pages'/f'{page_id}.json').read_text(encoding='utf-8'))
        text=''.join(line['raw'] for line in page['lines'])
        values=[LOOKUP[ch] for ch in text if ch in LOOKUP]
        if values:
            pages[page_id]=values[:24]
    assert len(pages)==55 and len(openings)==9
    counts=Counter()
    seen=set()
    for case in result['cases']:
        mode,page,opening=case['mode'],case['page'],case['opening']
        key=(mode,page,opening)
        assert key not in seen
        seen.add(key)
        cipher=pages[page]
        plain=openings[opening]
        demanded,known,count=constraints(cipher,plain,mode,29)
        assert len(demanded)==case['assigned_entry_count']
        assert count==case['compatible_full_table_count']
        first={}
        occurrence_conflicts=0
        for i in range(1,12):
            source=cipher[i-1] if mode=='ciphertext' else plain[i-1]
            target=(cipher[i]-plain[i])%29
            if source not in first:
                first[source]=target
            elif first[source]!=target:
                occurrence_conflicts+=1
        assert occurrence_conflicts==case['conflict_count']
        if count:
            assert case['forward_coverage']==forward_coverage(cipher,plain,mode,known,29)
        counts[mode]+=bool(count)
    assert len(seen)==990
    for mode in ('ciphertext','plaintext'):
        assert counts[mode]==result['summary'][mode]['consistent_cases']
    return dict(counts)


if __name__=='__main__':
    print(json.dumps({'small_field_controls':exhaustive_controls(),
                      'independent_consistent_cases':independent_census()},indent=2))
