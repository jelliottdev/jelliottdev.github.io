"""Enumerate exact archived-row/ordinal-column routes with source traces.
Standard library only. Never overwrite an existing report.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()

def route(rows,axis,outer_reverse,inner_reverse,alternating):
    count=len(rows) if axis=='row' else max(map(len,rows),default=0)
    groups=list(range(count))
    if outer_reverse:groups.reverse()
    output=[]
    for ordinal,g in enumerate(groups):
        group=list(rows[g]) if axis=='row' else [row[g] for row in rows if g<len(row)]
        if inner_reverse ^ (alternating and ordinal%2==1):group.reverse()
        output.extend(group)
    return output

def run():
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    alphabet=[a['rune'] for a in json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']]
    lookup={r:i for i,r in enumerate(alphabet)}
    for opening in plan['openings']:
        if sha((ROOT/opening['source']).read_bytes())!=opening['sha256']:raise ValueError('Opening trace changed')
    pages=[]
    for pid in plan['pages']:
        path=ROOT/'text'/(pid+'.txt');raw=path.read_bytes();text=raw.decode('utf-8')
        if {c for c in text if '\u16a0'<=c<='\u16ff'}-set(alphabet):raise ValueError('Unknown rune')
        rows=[];positions=[]
        for line_no,line in enumerate(text.splitlines(),1):
            runes=[lookup[c] for c in line if c in lookup];row=[]
            for column,index in enumerate(runes,1):
                ordinal=len(positions);row.append(ordinal)
                positions.append({'ordinal':ordinal,'line':line_no,'rune_position':column,'index':index})
            if row:rows.append(row)
        cases=[]
        if rows:
            for axis,outer,inner,alternate in itertools.product(plan['axes'],plan['outer_reverse'],plan['inner_reverse'],plan['alternating']):
                order=route(rows,axis,outer,inner,alternate)
                if sorted(order)!=list(range(len(positions))):raise ValueError('Route is not a permutation')
                output=[positions[i]['index'] for i in order]
                cases.append({'axis':axis,'outer_reverse':outer,'inner_reverse':inner,'alternating':alternate,
                              'source_ordinals':order,'output_indices':output,
                              'matching_openings':[o['id'] for o in plan['openings'] if output[:12]==o['indices']]})
        pages.append({'page':pid,'source_sha256':sha(raw),'source_positions':positions,'cases':cases})
    return {'schema':'liberpedia-row-column-routes-v1','plan_sha256':sha((HERE/'plan.json').read_bytes()),
            'alphabet':alphabet,'pages':pages,'case_count':sum(len(p['cases']) for p in pages),
            'matching_case_count':sum(bool(c['matching_openings']) for p in pages for c in p['cases'])}

def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check',action='store_true');group.add_argument('--output',type=Path)
    args=parser.parse_args();result=run()
    if args.check:
        if result!=json.loads((HERE/'results.json').read_text(encoding='utf-8')):raise SystemExit('Rerun differs')
        print('All source traces, permutations and candidate sequences reproduce exactly.')
    else:
        with args.output.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,separators=(',',':'),ensure_ascii=True);f.write('\n')
    print(json.dumps({k:result[k] for k in ('case_count','matching_case_count')}))
if __name__=='__main__':main()
