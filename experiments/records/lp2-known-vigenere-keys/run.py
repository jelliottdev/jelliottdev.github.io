"""Compare two known repeating keys with nine fixed opening vectors.
Python 3.12 standard library; no network or language model.
"""
import argparse
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()

def decode(stream,key,phase,sign):
    return [(c+sign*key[(j+phase)%len(key)])%29 for j,c in enumerate(stream)]

def run():
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    alphabet=[r['rune'] for r in json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']]
    assert len(alphabet)==len(set(alphabet))==29
    lookup={r:i for i,r in enumerate(alphabet)}
    for opening in plan['openings']:
        if sha((ROOT/opening['source']).read_bytes())!=opening['sha256']:
            raise ValueError('Opening trace hash changed')
    cases=[];inputs=[]
    for page in plan['pages']:
        path=ROOT/'text'/(page+'.txt');data=path.read_bytes();text=data.decode('utf-8')
        if {c for c in text if '\u16a0'<=c<='\u16ff'}-set(alphabet):raise ValueError('Unknown rune')
        stream=[lookup[c] for c in text if c in lookup]
        inputs.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(data)})
        for key in plan['keys']:
            for phase in range(len(key['indices'])):
                for sign in plan['signs']:
                    output=decode(stream,key['indices'],phase,sign)
                    matches=[o['id'] for o in plan['openings'] if output[:12]==o['indices']]
                    cases.append({'page':page,'key':key['id'],'phase':phase,'sign':sign,
                                  'output_indices':output,'matching_openings':matches})
    return {'schema':'liberpedia-known-key-opening-v1','plan_sha256':sha((HERE/'plan.json').read_bytes()),
            'alphabet':alphabet,'inputs':inputs,'case_count':len(cases),'comparison_count':len(cases)*len(plan['openings']),
            'matching_case_count':sum(bool(c['matching_openings']) for c in cases),'cases':cases}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check',action='store_true');group.add_argument('--output',type=Path)
    args=parser.parse_args();result=run()
    if args.check:
        if result!=json.loads((HERE/'results.json').read_text(encoding='utf-8')):raise SystemExit('Rerun differs')
        print('All candidate sequences, matches and hashes reproduce exactly.')
    else:
        with args.output.open('x',encoding='utf-8',newline='\n') as f:
            json.dump(result,f,separators=(',',':'),ensure_ascii=True);f.write('\n')
    print(json.dumps({k:result[k] for k in ('case_count','comparison_count','matching_case_count')}))
if __name__=='__main__':main()
