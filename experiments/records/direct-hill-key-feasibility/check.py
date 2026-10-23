"""Independent stacked-rank check and exhaustive small-field key oracle."""
import itertools
import json
import random
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ALPHABET='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
INDEX={ch:i for i,ch in enumerate(ALPHABET)}


def rowrank(rows,q):
    work=[list(row) for row in rows]
    if not work:
        return 0
    height,width=len(work),len(work[0])
    top=0
    for j in range(width):
        k=next((k for k in range(top,height) if work[k][j]%q),None)
        if k is None:
            continue
        work[top],work[k]=work[k],work[top]
        inverse=pow(work[top][j]%q,-1,q)
        work[top]=[(value*inverse)%q for value in work[top]]
        for k in range(top+1,height):
            scale=work[k][j]%q
            if scale:
                work[k]=[(a-scale*b)%q for a,b in zip(work[k],work[top])]
        top+=1
        if top==height:
            break
    return top


def stacked_answer(cipher,plain,n,q):
    c=[cipher[i:i+n] for i in range(0,len(cipher),n)]
    p=[plain[i:i+n] for i in range(0,len(plain),n)]
    cr=[[v[row] for v in c] for row in range(n)]
    pr=[[v[row] for v in p] for row in range(n)]
    r=rowrank(cr,q)
    if rowrank(cr+pr,q)!=r or rowrank(pr,q)!=r:
        return r,0
    total=1
    for j in range(r,n):
        total*=q**n-q**j
    return r,total


def oracle_count(cipher,plain,n,q,invertibles):
    c=[cipher[i:i+n] for i in range(0,len(cipher),n)]
    p=[plain[i:i+n] for i in range(0,len(plain),n)]
    return sum(all(tuple(sum(row[k]*cv[k] for k in range(n))%q for row in a)==tuple(pv)
                   for cv,pv in zip(c,p)) for a in invertibles)


def exhaustive_controls():
    rng=random.Random(330129)
    counts={}
    for q,n,expected in [(2,2,6),(2,3,168),(3,2,48),(3,3,11232)]:
        invertibles=[]
        for entries in itertools.product(range(q),repeat=n*n):
            a=[entries[i*n:(i+1)*n] for i in range(n)]
            if rowrank(a,q)==n:
                invertibles.append(a)
        assert len(invertibles)==expected,(q,n,len(invertibles))
        fixtures=[]
        # Include zero input, full rank, each deficient rank, and broken mappings.
        for r in range(n+1):
            ccols=[[int(i==j) for i in range(n)] for j in range(r)]
            ccols+=[ccols[0] if r else [0]*n,[0]*n]
            a=invertibles[(7*r+3)%len(invertibles)]
            pcols=[[sum(a[i][k]*v[k] for k in range(n))%q for i in range(n)] for v in ccols]
            fixtures.append((ccols,pcols))
            broken=[v[:] for v in pcols]
            broken[-1][0]=(broken[-1][0]+1)%q
            fixtures.append((ccols,broken))
        # Random independent confirmations exercise less tidy relations too.
        for _ in range(12):
            ccols=[[rng.randrange(q) for _ in range(n)] for _ in range(n+2)]
            pcols=[[rng.randrange(q) for _ in range(n)] for _ in range(n+2)]
            fixtures.append((ccols,pcols))
        for ccols,pcols in fixtures:
            cipher=[x for v in ccols for x in v]
            plain=[x for v in pcols for x in v]
            _,predicted=stacked_answer(cipher,plain,n,q)
            observed=oracle_count(cipher,plain,n,q,invertibles)
            assert predicted==observed,(q,n,ccols,pcols,predicted,observed)
        counts[f'F{q}-n{n}']={'invertible_matrices':expected,'fixtures':len(fixtures)}
    return counts


def check_census():
    result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    plan=json.loads((ROOT/'experiments/records/lp2-known-vigenere-keys/plan.json').read_text(encoding='utf-8'))
    openings={o['id']:o['indices'] for o in plan['openings']}
    pages={}
    for number in range(56):
        page_id=f'lp2-{number:02d}'
        page=json.loads((ROOT/'data/pages'/f'{page_id}.json').read_text(encoding='utf-8'))
        text=''.join(line['raw'] for line in page['lines'])
        values=[INDEX[ch] for ch in text if ch in INDEX]
        if values:
            pages[page_id]=values[:12]
    assert len(pages)==55 and len(openings)==9
    summaries={}
    for n in (2,3):
        subset=[v for v in result['cases'] if v['dimension']==n]
        assert len(subset)==495
        seen=set()
        successes=0
        for case in subset:
            pair=case['page'],case['opening']
            assert pair not in seen
            seen.add(pair)
            cipher=pages[case['page']]
            plain=openings[case['opening']]
            rank,count=stacked_answer(cipher,plain,n,29)
            assert (rank,count)==(case['cipher_rank'],case['compatible_key_count']),(n,pair)
            assert (count>0)==(case['status']=='feasible')
            successes+=(count>0)
        assert len(seen)==len(pages)*len(openings)
        assert successes==result['summary'][str(n)]['status_counts'].get('feasible',0)
        summaries[str(n)]={'cases':len(seen),'feasible':successes}
    return summaries


if __name__=='__main__':
    controls=exhaustive_controls()
    census=check_census()
    print(json.dumps({'small_field_controls':controls,'independent_census':census},indent=2))
