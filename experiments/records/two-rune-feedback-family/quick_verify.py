"""Verify saved bytes, aliases, matched-null inputs and whole-family gate arithmetic."""
import hashlib
import io
import json
from pathlib import Path
import random
import numpy as np

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def array_sha(array):
    out=io.BytesIO();np.save(out,array,allow_pickle=False)
    return hashlib.sha256(out.getvalue()).hexdigest()


def verify():
    if (HERE/'record.json').exists():
        record=json.loads((HERE/'record.json').read_bytes());prefix='experiments/records/'+record['id']+'/'
        for role in ('inputs','outputs'):
            for item in record['reproduction'][role]:
                assert item['path'].startswith(prefix),item['path']
                assert sha(HERE/item['path'][len(prefix):])==item['sha256'],item['path']
    p=json.loads((HERE/'protocol-frozen.json').read_bytes());r=json.loads((HERE/'results.json').read_bytes())
    for item in p['files']:assert sha(HERE/item['path'])==item['sha256'],item['path']
    for item in json.loads((HERE/'source-manifest.json').read_bytes())['files']:assert sha(HERE/item['path'])==item['sha256']
    assert r['protocol_sha256']==sha(HERE/'protocol-frozen.json')
    observed=np.load(HERE/'observed-effective-scores.npy',allow_pickle=False)
    nulls=np.load(HERE/'null-page-maxima-scores.npy',allow_pickle=False)
    primers=np.load(HERE/'null-page-maxima-primers.npy',allow_pickle=False)
    assert observed.shape==(48,55,841) and nulls.shape==primers.shape==(49,56,55)
    assert np.isfinite(observed).all() and np.isfinite(nulls).all() and np.max(primers)<841
    assert sha(HERE/'observed-effective-scores.npy')==r['observed_effective_scores_sha256']
    assert sha(HERE/'null-page-maxima-scores.npy')==r['null_page_scores_sha256']
    assert sha(HERE/'null-page-maxima-primers.npy')==r['null_page_primers_sha256']
    assert float(np.max(observed))==r['observed']['best']['score']
    assert r['null_maximum']==float(np.max(nulls))
    assert r['hit_bar']==max(-5.5,float(np.max(nulls))+.5)
    assert r['null_ge_observed']==int(np.sum(np.max(nulls,axis=(1,2))>=r['observed']['best']['score']))
    labels=p['labels'];effective={row['id']:i for i,row in enumerate(p['effective_labels'])}
    negative=np.array([(-a)%29*29+(-b)%29 for a in range(29) for b in range(29)])
    expanded=np.empty((56,55,841),dtype='<f8')
    for li,label in enumerate(labels):
        values=observed[effective[label['representative']]]
        expanded[li]=values[:,negative] if label['negate_starting_key'] else values
    assert len(r['gate_hits'])==int(np.sum(expanded>=r['hit_bar']))
    order=np.argsort(-expanded.reshape(-1),kind='stable')[:40]
    pages=json.loads((HERE/'pages.json').read_bytes())['pages']
    for row,flat in zip(r['observed']['top40'],order):
        li,rest=divmod(int(flat),55*841);pi,key=divmod(rest,841)
        assert row['label']==labels[li]['id'] and row['page']==pages[pi]['page'] and row['starting_key']==list(divmod(key,29))
        assert row['score']==float(expanded[li,pi,key])
    for i,row in enumerate(r['null_global_witnesses']):
        assert row['seed']==p['null_seed']+i
        rng=random.Random(row['seed']);corpus=[]
        for page in pages:
            values=list(page['runes']);rng.shuffle(values);corpus.extend(values)
        assert row['input_sha256']==hashlib.sha256(bytes(corpus)).hexdigest()
        assert row['scores_sha256']==array_sha(nulls[i]) and row['primers_sha256']==array_sha(primers[i])
        flat=int(np.argmax(nulls[i]));li,pi=divmod(flat,55)
        assert row['best']['label']==labels[li]['id'] and row['best']['page']==pages[pi]['page']
        assert row['best']['score']==float(np.max(nulls[i]))
        assert row['best']['starting_key']==list(divmod(int(primers[i,li,pi]),29))
    print('PASS: declared bytes, alias-expanded ordering,49shared shuffled inputs and whole-family gate arithmetic; no decoding searches run.')


if __name__=='__main__':verify()
