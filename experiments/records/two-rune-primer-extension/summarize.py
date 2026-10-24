"""Retain per-page witnesses and compact null maxima from the unchanged score grid."""
import hashlib
import json
from pathlib import Path
import numpy as np
import engine as e

HERE=Path(__file__).resolve().parent


def main():
    result=json.loads((HERE/'results.json').read_bytes())
    scores=np.load(HERE/'scores.npy',allow_pickle=False)
    pages=json.loads((HERE/'pages.json').read_bytes())['pages']
    observed=[]
    for pi,page in enumerate(pages):
        index=int(np.argmax(scores[0,pi]))
        observed.append(e.witness(page['runes'],page['page'],index,scores[0,pi,index]))
    nulls=[]
    for trial,row in enumerate(result['nulls']):
        winners=np.argmax(scores[trial+1],axis=1)
        nulls.append({'seed':row['seed'],'page_order':[p['page'] for p in pages],
                      'maximum_scores':[float(scores[trial+1,pi,index]) for pi,index in enumerate(winners)],
                      'primer_pairs':[list(divmod(int(index),29)) for index in winners]})
    out={'plan_sha256':result['plan_sha256'],'score_array_sha256':result['scores_sha256'],
         'tie_rule':'Exact score; earliest source page, then lexicographic primer(s0,s1).',
         'observed_per_page_witnesses':observed,'null_per_page_maxima':nulls,
         'source_manifest_sha256':hashlib.sha256((HERE/'input-manifest.json').read_bytes()).hexdigest(),
         'page_inputs_sha256':hashlib.sha256((HERE/'pages.json').read_bytes()).hexdigest()}
    with (HERE/'page-maxima.json').open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(out,indent=2)+'\n')
    print('Saved55observedpagewitnesses and49x55nullpage maxima; no additional search.')


if __name__=='__main__':main()
