"""Scalar verifier for all nine selected source chain-key outputs and planted controls."""
import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
RUNES='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'


def primes(n):
    out=[];x=2
    while len(out)<n:
        if all(x%p for p in out if p*p<=x):out.append(x)
        x+=1
    return out


def selected_sequence(name,source_root,prime):
    if name=='prime':return prime
    if name=='prime^2':return [p*p for p in prime]
    if name=='gap':return [prime[i+1]-prime[i] for i in range(len(prime)-1)]
    if name=='cumsum_prime':
        ret=[];total=0
        for p in prime:total+=p;ret.append(total)
        return ret
    if name=='fib':
        ret=[];a=b=1
        for _ in range(4400):ret.append(a);a,b=b,a+b
        return ret
    if name=='phi(n)':return [sum(math.gcd(i,j)==1 for j in range(1,i+1)) for i in range(900)]
    if name=='pi':return [int(c) for c in (source_root/'pi.txt').read_text(encoding='utf-8') if c.isdigit()]
    if name=='n^3':return [i**3 for i in range(900)]
    raise ValueError(name)


def score(cipher,row,sequence):
    step=[(cipher[i]-cipher[i-1])%29 for i in range(1,min(len(cipher),501))]
    bij=row['bijection']
    if bij.startswith('dlog'):
        g=int(bij[4:]);d={pow(g,k,29):k for k in range(28)}
        assert len(d)==28
        transform=lambda s:d[s]
    elif bij=='s-1':transform=lambda s:s-1
    elif bij=='28-s':transform=lambda s:28-s
    else:raise ValueError(bij)
    key=[int(x)%28 for x in sequence]
    values=[];j=0
    for i,s in enumerate(step):
        if s:
            used=i if row['convention']=='A' else j
            values.append((transform(s)-row['sign']*key[row['offset']+used])%28)
            j+=1
    cnt=Counter(values);n=len(values)
    return 28*sum(v*(v-1) for v in cnt.values())/(n*(n-1))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-root',type=Path,required=True)
    args=ap.parse_args()
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    source=args.source_root
    for rel,field in (('tests5.py','source_test_sha256'),('results/tests5.txt','source_receipt_sha256'),('pi.txt','pi_digits_sha256')):
        assert hashlib.sha256((source/rel).read_bytes()).hexdigest()==plan[field]
    receipt=(source/'results/tests5.txt').read_text(encoding='utf-8')
    prime=primes(4400)
    relikd=source/'sources/relikd_LiberPrayground'
    sections={}
    for name in plan['sections']:
        rel=f'pages/{name}.txt';path=relikd/rel
        assert hashlib.sha256(path.read_bytes()).hexdigest()==plan['section_sha256'][rel]
        sections[name]=[RUNES.index(c) for c in path.read_text(encoding='utf-8') if c in RUNES]
    for name,part in result['lp2_sections'].items():
        row=part['best']
        seq=selected_sequence(row['sequence'],source,prime)
        assert abs(score(sections[name],row,seq)-row['ioc28'])<1e-12,(name,row)
        # The source printout rounds to three places; all nine best-grid rows agree.
        assert re.search(rf'{re.escape(name)}\s+best IoC28={row["ioc28"]:.3f}',receipt),(name,row)
        assert part['evaluated_configurations']==352800
    base=relikd/'data/baseline-rune-stream.txt'
    assert hashlib.sha256(base.read_bytes()).hexdigest()==plan['baseline_sha256']
    wp=[RUNES.index(c) for c in base.read_text(encoding='utf-8') if c in RUNES][:1500]
    for consume in (True,False):
        out=[];last=0;j=0;key=[p%28 for p in prime[50:]]
        for x in wp:
            if x==28:
                delta=0
                if consume:j+=1
            else:
                delta=1+(x+key[j])%28;j+=1
            last=(last+delta)%29;out.append(last)
        row=result['synthetic_controls'][str(consume).lower()]['best']
        assert row['sequence']=='prime' and row['offset']==51 and row['convention']==('A' if consume else 'B')
        assert abs(score(out,row,prime)-row['ioc28'])<1e-12
    ctrl=result['selected_section_control']
    observed=result['lp2_sections'][ctrl['section']]['best']['ioc28']
    assert ctrl['observed_best']==observed
    assert ctrl['exceedances']==sum(x>=observed for x in ctrl['shuffle_maxima'])
    assert ctrl['plus_one_tail']==(1+ctrl['exceedances'])/(1+len(ctrl['shuffle_maxima']))
    print('PASS: nine source-selected scores, two planted controls, exact receipts and 39 control summaries')


if __name__=='__main__':main()
