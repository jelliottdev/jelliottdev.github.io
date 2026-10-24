"""Independently check the offset-screen model input and saved control comparison."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
RECORD = HERE
TRANS = ['F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S','T','B','E','M','L','NG','OE','D','A','AE','Y','IA','EA']
ALIASES = {'V':1,'K':5,'Z':15,'Q':5}
TOKENS = sorted(((t,i) for i,t in enumerate(TRANS)), key=lambda x:-len(x[0]))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def encode(text):
    s = text.upper(); out=[]; i=0
    while i < len(s):
        for token,index in TOKENS:
            if s.startswith(token,i):
                out.append(index);i+=len(token);break
        else:
            if s[i] in ALIASES: out.append(ALIASES[s[i]])
            i+=1
    return np.asarray(out,dtype=np.int64)


def rebuild_kjv_model():
    idx=encode((HERE/'source-kjv.txt').read_text(encoding='utf-8',errors='ignore'))
    counts=np.ones((29,29,29),dtype=np.float64)
    np.add.at(counts,(idx[:-2],idx[1:-1],idx[2:]),1.0)
    return np.log10(counts/counts.sum(axis=2,keepdims=True)).astype(np.float32)


def calculate():
    plan=read('plan.json')
    for item in plan['inputs']:
        name=Path(item['path']).name
        assert item['path']=='experiments/records/dukotah-offset-model-integrity/'+name
        assert sha(HERE/name)==item['sha256'], name
    capsule=read('source-capsule-manifest.json')
    specs={x['id']:x for x in capsule['items'] if x.get('id') in {'corpus.kjv','corpus.moby','corpus.pride','corpus.war'}}
    assert len(specs)==4
    assert sha(HERE/'source-kjv.txt')==specs['corpus.kjv']['sha256']
    current=read('corpora-receipt.json')['corpora']
    assert {r['name'] for r in current}=={'kjv.txt','moby.txt','pride.txt','war.txt'}
    exact={r['name']:r['exact_match'] for r in current}
    for row in current:
        spec=specs['corpus.'+row['name'].removesuffix('.txt')]
        assert row['expected_sha256']==spec['sha256'] and row['expected_bytes']==spec['bytes']
        assert row['exact_match']==(row['bytes']==spec['bytes'] and row['sha256']==spec['sha256'])
    assert exact=={'kjv.txt':True,'moby.txt':False,'pride.txt':False,'war.txt':True}
    assert not read('corpus-recovery-check.json')['exact_match_found']

    cache=np.load(HERE/'trigram-kjv-only.npy',allow_pickle=False)
    assert cache.shape==(29,29,29) and np.array_equal(cache,rebuild_kjv_model())
    src=read('source-control-offset.json'); fresh=read('control_offset.json')
    assert len(src['rows'])==len(fresh['rows'])==40
    assert [r['trial'] for r in src['rows']]==list(range(40))
    assert [r['trial'] for r in fresh['rows']]==list(range(40))
    for d in (src,fresh):
        rows=d['rows'];n=len(rows)
        assert sum(r['rune_match']>.95 for r in rows)==d['recovered']
        assert sum(r['dense_rank'] is not None for r in rows)==d['dense_found']
        assert sum(r['pipeline_first'] for r in rows)==int(round(d['pipeline_first']*n))
        assert d['recovery']==d['recovered']/n and d['survival']==d['dense_found']/n
    different=[i for i,(a,b) in enumerate(zip(src['rows'],fresh['rows'])) if a!=b]
    assert different==[15,17,25,27,36]
    pilot=read('pilot-a1.json');archived=read('source-checkpoint-A1-0.json')
    assert pilot['unit']==archived['i']==0 and pilot['offsets']==archived['n_offsets']==1048576
    assert pilot['all_fields_exact'] is False
    assert pilot['best']!=archived['best']
    return {
        'schema':'liberpedia-offset-model-integrity-results-v1',
        'plan_sha256':sha(HERE/'plan.json'),
        'source_revision':plan['source_revision'],
        'corpus_hashes_match':exact,
        'kjv_only_model_rebuilt_exact':True,
        'source_control':{'recovered':src['recovered'],'retained':src['dense_found'],
                          'ranked_first':sum(r['pipeline_first'] for r in src['rows'])},
        'fallback_control':{'recovered':fresh['recovered'],'retained':fresh['dense_found'],
                            'ranked_first':sum(r['pipeline_first'] for r in fresh['rows'])},
        'identical_trial_rows':40-len(different), 'changed_trial_ids':different,
        'a1_unit0':{'offsets_scanned':1048576,
                    'source_best_offset':archived['best']['offset'],
                    'fallback_best_offset':pilot['best']['offset'],
                    'source_best_score':archived['best']['score'],
                    'fallback_best_score':pilot['best']['score'],
                    'exact_checkpoint_parity':False},
        'interpretation':'Control totals can agree while selected offsets differ. The fallback model cannot verify the source full-grid target result.'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args()
    result=calculate()
    target=HERE/'results.json'
    if a.write:
        target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
    else:
        assert target.exists() and read('results.json')==result
    print('PASS: exact input hashes, KJV-only model reconstruction, 40 trial rows, five rank changes, A1 checkpoint mismatch')


if __name__=='__main__':
    main()
