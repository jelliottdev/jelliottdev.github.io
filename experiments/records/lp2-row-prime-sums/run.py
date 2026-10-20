"""Test the combined count of prime row sums against fixed-length page shuffles.
Python 3.12 standard library only. Existing output files are never overwritten.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()

def sieve(limit):
    flags=[True]*(limit+1)
    flags[0]=False
    if limit>=1:flags[1]=False
    for n in range(2,int(limit**.5)+1):
        if flags[n]:
            for k in range(n*n,limit+1,n):flags[k]=False
    return flags

def run():
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    index=json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))
    values={a['rune']:a['prime'] for a in index['alphabet']}
    pages=[];inputs=[]
    for pid in plan['pages']:
        path=ROOT/'text'/(pid+'.txt');raw=path.read_bytes();text=raw.decode('utf-8')
        if {c for c in text if '\u16a0'<=c<='\u16ff'}-set(values):raise ValueError('Unknown rune in '+pid)
        rows=[]
        for line_no,line in enumerate(text.splitlines(),1):
            row=[values[c] for c in line if c in values]
            if row:rows.append((line_no,row))
        if not rows:raise ValueError('No rune rows in '+pid)
        pages.append((pid,rows));inputs.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(raw)})
    flags=sieve(max(sum(sum(row) for _,row in rows) for _,rows in pages))
    observed=[]
    for pid,rows in pages:
        observed.append({'page':pid,'rows':[{'line':line,'runes':len(row),'sum':sum(row),'prime':flags[sum(row)]} for line,row in rows]})
    total=sum(row['prime'] for page in observed for row in page['rows'])
    rng=random.Random(plan['seed']);trials=[]
    for number in range(plan['shuffle_trials']):
        counts=[]
        for pid,rows in pages:
            stream=[v for _,row in rows for v in row];rng.shuffle(stream)
            offset=0;count=0
            for _,row in rows:
                end=offset+len(row);count+=flags[sum(stream[offset:end])];offset=end
            assert offset==len(stream)
            counts.append(count)
        score=sum(counts)
        trials.append({'trial':number+1,'page_counts':counts,'total':score,'at_least_observed':score>=total})
    exceed=sum(t['at_least_observed'] for t in trials)
    return {'schema':'liberpedia-row-prime-null-v1','plan_sha256':sha((HERE/'plan.json').read_bytes()),
            'alphabet':index['alphabet'],'inputs':inputs,'observed':observed,'row_count':sum(len(x['rows']) for x in observed),
            'prime_row_count':total,'null_page_order':plan['pages'],'null_trials':trials,
            'exceedances':exceed,'monte_carlo_p':(exceed+1)/(len(trials)+1),'threshold':plan['threshold'],
            'below_threshold':(exceed+1)/(len(trials)+1)<plan['threshold']}

def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check',action='store_true');group.add_argument('--output',type=Path)
    args=parser.parse_args();result=run()
    if args.check:
        if result!=json.loads((HERE/'results.json').read_text(encoding='utf-8')):raise SystemExit('Rerun differs')
        print('All observed row sums and 999 full-dataset shuffles reproduce exactly.')
    else:
        with args.output.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=True,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ('row_count','prime_row_count','exceedances','monte_carlo_p','below_threshold')}))
if __name__=='__main__':main()
