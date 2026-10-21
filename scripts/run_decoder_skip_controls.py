"""Execute the frozen 216-plant decoder benchmark; independent check required."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from decoder_skip_controls import key_fixture,encode,load_model,beam_decode,rigid_decode

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/plans/decoder-skip-controls.json'


def produce():
    plan=json.loads(PLAN.read_bytes())
    for source in plan['inputs']:
        assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256'],source['path']
    model,floor=load_model(ROOT/'experiments/records/english-scorer-controls/english_quadgrams.txt')
    records=[]
    for section in plan['sections']:
        path=ROOT/f'exports/readings/{section}.csv'
        with path.open(encoding='utf-8',newline='') as source:all_rows=list(csv.DictReader(source))
        rows=all_rows[:plan['prefix_runes']];plain=[int(r['output_index']) for r in rows]
        assert plain and all(0<=p<29 for p in plain)
        endpoints={k:[rows[0][k],rows[-1][k]] for k in ['page','page_rune_ordinal','section_rune_ordinal']}
        for seed in plan['seeds']:
            for repetition in plan['key_repetitions']:
                correct=key_fixture(seed,repetition,plan['key_slots'])
                wrong=key_fixture(seed+1000,repetition,plan['key_slots'])
                for mechanism in plan['encoders']:
                    cipher,trace=encode(plain,correct,mechanism,seed)
                    for c,p,t in zip(cipher,plain,trace,strict=True):
                        assert (c-int(t['rewritten'])-correct[t['accepted_slot']])%29==p
                    results=[]
                    for condition,key in [('correct',correct),('wrong',wrong)]:
                        configs=[('rigid',None,0)]+[('beam',w,s) for w in plan['beam_widths'] for s in plan['maximum_skips']]
                        for decoder,width,skip in configs:
                            if decoder=='rigid':out=rigid_decode(cipher,key,plan['latin'],model,floor,plain,trace)
                            else:out=beam_decode(cipher,key,width,skip,plan['latin'],model,floor,plain,trace)
                            matches=[a==b for a,b in zip(out['indices'],plain,strict=True)]
                            prefix=next((i for i,m in enumerate(matches) if not m),len(matches))
                            out.update(key_condition=condition,decoder=decoder,width=width,maximum_skip=skip,
                                       exact_match=all(matches),matching_indices=sum(matches),length=len(plain),
                                       longest_correct_prefix=prefix,score_accepted=out['normalized_score'] is not None and out['normalized_score']>=plan['threshold'])
                            results.append(out)
                    records.append({'section':section,'source_rows_available':len(all_rows),'endpoints':endpoints,
                                    'seed':seed,'key_repetition':repetition,'encoder':mechanism,'plaintext':plain,
                                    'ciphertext':cipher,'encoder_trace':trace,'results':results})
        print('Completed',section,flush=True)
    assert len(records)==216 and sum(len(r['results']) for r in records)==2160
    return {'status':'producer results; independent beam replay pending','plan_sha256':hashlib.sha256(PLAN.read_bytes()).hexdigest(),
            'implementation_sha256':hashlib.sha256((ROOT/'scripts/decoder_skip_controls.py').read_bytes()).hexdigest(),
            'producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'plants':records}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():parser.error('Choose a new output path')
    result=produce()
    with args.output.open('x',encoding='utf-8',newline='\n') as out:json.dump(result,out,indent=2);out.write('\n')
    print('Saved all 216 plants and 2160 decoder results; independent replay pending')
