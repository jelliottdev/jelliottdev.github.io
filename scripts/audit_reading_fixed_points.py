"""Separate unchanged indices from recorded interruptions in four LP1 controls.

Checks every saved trace row against original rune order and declared control
arithmetic. Descriptive known-reading audit only: no grille or chance model.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SECTIONS=['warning','welcome','first-koan','second-koan']

def audit():
    index=json.loads((ROOT/'data/index.json').read_bytes())
    alphabet=[a['rune'] for a in index['alphabet']]
    assert len(alphabet)==29 and len(set(alphabet))==29
    controls=json.loads((ROOT/'data/evidence/reading-methods.json').read_bytes())['controls']
    plan=json.loads((ROOT/'experiments/records/lp1-word-length-balance/plan.json').read_bytes())
    paths={'data/index.json','data/evidence/reading-methods.json','experiments/records/lp1-word-length-balance/plan.json'}
    summaries=[];positions=[]
    for section in SECTIONS:
        control=next(c for c in controls if c['id']==section)
        assert control['pages']==next(s['pages'] for s in plan['sections'] if s['id']==section)
        trace_path=f'exports/readings/{section}.csv';paths.add(trace_path)
        with (ROOT/trace_path).open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
        source=[]
        for page in control['pages']:
            path=f'text/{page}.txt';paths.add(path)
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==plan['input_hashes'][path]
            runes=[c for c in (ROOT/path).read_text(encoding='utf-8') if c in alphabet]
            source.extend((page,n,r) for n,r in enumerate(runes))
        assert len(source)==len(rows)
        key_position=control['start'];same=skips=natural=0
        for ordinal,((page,local,rune),row) in enumerate(zip(source,rows)):
            x=alphabet.index(rune);skip=ordinal in control['skip'];method=control['method']
            assert row['page']==page and int(row['page_rune_ordinal'])==local
            assert int(row['section_rune_ordinal'])==ordinal
            assert row['input_rune']==rune and int(row['input_index'])==x
            assert row['copied']==str(skip)
            if method=='vigenere':
                assert int(row['key_position_before'])==key_position
                assert int(row['key_slot_before'])==key_position%len(control['key'])
                if skip:
                    y=x;assert row['subtracted_value']==''
                else:
                    amount=control['key'][key_position%len(control['key'])]
                    assert int(row['subtracted_value'])==amount
                    y=(x-amount)%29;key_position+=1
                assert int(row['key_position_after'])==key_position
            else:
                assert not skip and method in ['atbash','shifted-atbash']
                y=(28-x+(control['shift'] if method=='shifted-atbash' else 0))%29
                assert all(row[k]=='' for k in ['subtracted_value','key_position_before','key_position_after','key_slot_before'])
            assert int(row['output_index'])==y
            unchanged=x==y;same+=unchanged;skips+=skip;natural+=unchanged and not skip
            if unchanged:
                positions.append({'section':section,'page':page,'page_rune_ordinal':local,
                    'section_rune_ordinal':ordinal,'rune':rune,'index':x,
                    'reason':'recorded interruption' if skip else 'ordinary transformation fixed point'})
        assert same==skips+natural
        summaries.append({'section':section,'method':control['method'],'runes':len(rows),
            'unchanged_indices':same,'recorded_interruptions':skips,
            'ordinary_fixed_points':natural,'changed_indices':len(rows)-same})
    assert sum(s['runes'] for s in summaries)==1796
    return {'scope':'Four published LP1 controls underlying the 464-word object; headings and interruption runes retained. Rune positions, not word counts.',
        'ordinal_rule':'Zero-based; section ordinals carry across pages in these controls.',
        'summaries':summaries,'unchanged_positions':positions,
        'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)},
        'auditor_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limits':'Replays declared known-reading arithmetic, including previously aligned interruptions. Does not infer new skip rules, test significance or specify a grille placement/readout.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('Use a new output path')
    result=audit()
    with args.output.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(result['summaries'],indent=2))
