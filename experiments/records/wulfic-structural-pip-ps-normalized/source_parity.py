"""Compare the corrected replay's core operations to the pinned source file."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',type=Path,required=True,help='Pinned structural_analysis.py file')
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    raw=args.source.read_bytes()
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(raw).hexdigest()==plan['source']['sha256']
    text=raw.decode('utf-8')
    prefix=text.split('# ============================================================\n# STEP 1')[0]
    env={'__file__':str(args.source)}
    exec(compile(prefix,str(args.source),'exec'),env)
    tree=ast.parse(text)
    source_sieve=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='sieve')
    exec(compile(ast.Module(body=[source_sieve],type_ignores=[]),str(args.source),'exec'),env)
    spec=importlib.util.spec_from_file_location('replay',HERE/'run.py')
    replay=importlib.util.module_from_spec(spec); spec.loader.exec_module(replay)
    assert env['RUNE_TO_IDX']==replay.MAP
    assert env['SEPARATORS']==replay.SEPARATORS
    values=env['sieve'](1000000)
    assert values==replay.source_primes(1000000)
    pips=[values[values[n]-1] for n in range(min(50000,len(values))) if values[n]-1<len(values)]
    keys,ours=replay.keys(plan)
    assert pips==ours and keys['pip']==[p%29 for p in pips]
    number=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id=='PS_NUMBER' for t in n.targets))
    assert number==plan['source_rules']['ps_number']
    assert keys['ps-digits']==[int(c) for c in number]
    assert keys['ps-pairs']==[int(number[i:i+2])%29 for i in range(0,len(number)-1,2)]
    n=int(number); base=[]
    while n: base.append(n%29); n//=29
    assert keys['ps-base29']==list(reversed(base))
    rng=random.Random(72016)
    cases=0
    for _ in range(100):
        c=[rng.randrange(29) for _ in range(rng.randrange(2,100))]
        key=[rng.randrange(29) for _ in c]
        for mode in replay.MODES:
            expected=env['decrypt'](c,key,mode)
            actual=[replay.decrypt_value(x,y,mode) for x,y in zip(c,key)]
            assert expected==actual
            assert abs(env['ioc'](expected)*29-replay.normalized_ioc(actual))<1e-12
            singleton=[0,len(c)-1]
            words=[(expected[i],) for i in singleton]
            assert env['check_singleton_constraint'](words)==all(expected[i] in (10,24) for i in singleton)
            cases+=1
    raw_cases={'all_same_100':[10]*100,
               'alternating_100':[10,24]*50,
               'all_distinct_29':list(range(29))}
    raw_gate=[]
    for name,values in raw_cases.items():
        value=env['ioc'](values)
        assert 0.0<=value<=1.0 and not value>1.3
        raw_gate.append({'case':name,'raw_ioc':round(value,9),'source_gate_pass':False})
    assert raw_gate[0]['raw_ioc']==1.0
    receipt={'source_sha256':hashlib.sha256(raw).hexdigest(),'mapping_equal':True,
             'separators_equal':True,'million_limit_sieve_equal':True,
             'pip_count':len(pips),'pip_first20':pips[:20],
             'key_lengths':{k:len(v) for k,v in keys.items()},
             'source_decrypt_ioc_singleton_vectors':cases,
             'raw_gate_controls':raw_gate}
    encoded=(json.dumps(receipt,indent=2)+'\n').encode('utf-8')
    path=HERE/'source-parity.json'
    if args.check: assert path.read_bytes()==encoded
    else: path.write_bytes(encoded)
    print(f'Source parity passed: {cases} vectors, all four key streams.')


if __name__=='__main__': main()
