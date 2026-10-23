"""Replay the finite archived page-24 operations with full-search controls."""
import hashlib
import json
import random
import sys
from pathlib import Path

from engine import ioc, runeglish, stage_one, stage_two

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def sha(stream):
    return hashlib.sha256(bytes(stream)).hexdigest()


def execute():
    inputs=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    positive=json.loads((HERE/'positive.json').read_text(encoding='utf-8'))
    assert positive['exact_extraction'] and positive['source_function_parity']
    assert positive['full_search_best_score']>positive['uniform_control_max']
    assert inputs['source_commit']==plan['source']['commit']
    assert hashlib.sha256((ROOT/inputs['site_path']).read_bytes()).hexdigest()==inputs['site_sha256']
    cipher=inputs['runes'];weights=inputs['trigram_weights']
    arms=stage_one(cipher)
    first={key:{'selected_runes':len(stream),'normalized_ioc':ioc(stream),
                'stream_sha256':sha(stream),'runeglish':runeglish(stream)}
           for key,stream in arms.items()}
    assert len({first[key]['normalized_ioc'] for key in first if key.startswith('whole_columnar')})==1
    settings=stage_two(cipher,weights)
    constant_ioc=settings[0]['ioc']
    observed=[{'width':row['width'],'shift':row['shift'],'trigram_score':row['trigram_score'],
               'output_sha256':sha(row['plain']),'runeglish':runeglish(row['plain']) if index<10 else None}
              for index,row in enumerate(settings)]
    null=[]
    for trial in range(256):
        shuffled=cipher[:]
        random.Random(20261023+trial).shuffle(shuffled)
        ranked=stage_two(shuffled,weights)
        null.append({'trial':trial,'max_trigram_score':ranked[0]['trigram_score'],
                     'width':ranked[0]['width'],'shift':ranked[0]['shift']})
    tail=sum(row['max_trigram_score']>=observed[0]['trigram_score'] for row in null)
    return {'schema':'liberpedia-wulfic-p24-results-v1',
            'plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),
            'input_sha256':hashlib.sha256((HERE/'inputs.json').read_bytes()).hexdigest(),
            'positive_sha256':hashlib.sha256((HERE/'positive.json').read_bytes()).hexdigest(),
            'source_commit':inputs['source_commit'],'page':inputs['site_page'],
            'source_page':24,'stage_one':first,'stage_two':{
                'source_settings':len(observed),'constant_normalized_ioc':constant_ioc,
                'ranked':observed},
            'null_seed_rule':'Random(20261023+trial).shuffle(page) for trial 0..255',
            'null':null,'null_ge_observed':tail,
            'add_one_tail_fraction':f'{tail+1}/{len(null)+1}'}


def main():
    output=execute()
    path=HERE/'results.json'
    if '--check' in sys.argv:
        assert output==json.loads(path.read_text(encoding='utf-8'))
    else:
        path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS: seven source arms, all 377 post-extraction settings and 256 full-search controls')


if __name__=='__main__':main()
