"""Exact Campaign VII C1 replay with source-rule power controls."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0,str(HERE/'source/analysis'))
sys.path.insert(0,str(HERE/'source/src'))
from campaign7 import c1_skipkey as source  # type: ignore


def source_parity():
    with tempfile.TemporaryDirectory(prefix='liberpedia-c1-') as td:
        target = Path(td)/'liber-primus'
        shutil.copytree(HERE/'source',target)
        original = json.loads((target/'analysis/campaign7/c1_skipkey_results.json').read_text(encoding='utf-8'))
        program = target/'analysis/campaign7/c1_skipkey.py'
        subprocess.run([sys.executable,str(program)],cwd=target,text=True,capture_output=True,
                       encoding='utf-8',check=True)
        rerun = json.loads((target/'analysis/campaign7/c1_skipkey_results.json').read_text(encoding='utf-8'))
        assert rerun == original
    return True


def source_grid():
    pages = source.load_pages();assert len(pages)==57
    unsolved=pages[:-2]
    sample=sorted(range(len(unsolved)),key=lambda i:-len(unsolved[i]))[:6]
    assert sample==[29,43,47,11,17,21]
    rows=[]
    for name,path in source.KEY_TEXTS.items():
        key=source.load_key(path)
        assert len(key)>=400
        for pi in sample:
            for offset in (0,len(key)//4,len(key)//2):
                value,text=source.beam_decrypt(unsolved[pi],key,offset)
                rows.append({'key_text':name,'source_page':pi,'site_page':pi if pi<50 else pi+1,
                             'offset':offset,'cipher_runes':len(unsolved[pi]),
                             'score':value,'latin_length':len(text),'preview':text[:80],
                             'plaintext_sha256':hashlib.sha256(text.encode('ascii')).hexdigest()})
    assert len(rows)==54
    archive=json.loads((HERE/'source/analysis/campaign7/c1_skipkey_results.json').read_text(encoding='utf-8'))
    best=max(rows,key=lambda r:r['score'])
    assert round(best['score'],3)==archive['best_score']
    assert (best['key_text'],best['source_page'],best['offset'],best['preview'])==(
        archive['best']['key_text'],archive['best']['page'],archive['best']['offset'],archive['best']['plaintext'])
    return rows


def plant(known,key,offset,skip_collision):
    cipher=[];position=offset;skips=0
    for plain in known:
        assert position+2<len(key)
        advance=1
        if skip_collision and cipher and (plain+key[position+1])%29==cipher[-1]:
            advance=2;skips+=1
        position+=advance
        cipher.append((plain+key[position])%29)
    return cipher,skips


def controls():
    with (ROOT/'exports/readings/lp2-56.csv').open(encoding='utf-8',newline='') as f:
        known=[int(row['output_index']) for row in csv.DictReader(f)]
    assert len(known)==85
    messages=[('documented-85',known),('repeated-273',(known*4)[:273])]
    rows=[]
    for name,path in source.KEY_TEXTS.items():
        key=source.load_key(path)
        for offset in (0,len(key)//4,len(key)//2):
            for message_name,plain in messages:
                truth=source.gp.indices_to_translit(plain)
                for skipped in (False,True):
                    cipher,count=plant(plain,key,offset,skipped)
                    score,text=source.beam_decrypt(cipher,key,offset)
                    rows.append({'key_text':name,'offset':offset,'message':message_name,
                                 'mechanism':'collision-skip' if skipped else 'no-skip',
                                 'cipher_runes':len(cipher),'planted_skips':count,
                                 'plaintext_exact':text==truth,'above_source_bar':score>-5.0,
                                 'source_score':score,'output_sha256':hashlib.sha256(text.encode('ascii')).hexdigest(),
                                 'output_latin_length':len(text)})
    assert len(rows)==36
    return rows


def compute():
    assert source_parity()
    positive=controls()
    real=source_grid()
    return {'schema':'liberpedia-longkey-skip-beam-results-v1',
            'plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),
            'source_parity':True,'controls':positive,'real':real,
            'control_counts':{'no_skip_exact':sum(r['plaintext_exact'] for r in positive if r['mechanism']=='no-skip'),
                              'collision_skip_exact':sum(r['plaintext_exact'] for r in positive if r['mechanism']=='collision-skip'),
                              'collision_skip_above_bar':sum(r['above_source_bar'] for r in positive if r['mechanism']=='collision-skip')},
            'real_above_source_bar':sum(r['score']>-5.0 for r in real)}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    result=compute();dest=HERE/'results.json'
    if args.check:
        assert result==json.loads(dest.read_text(encoding='utf-8'))
        print('PASS exact source grid, 36 plants and saved results')
    else:
        dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        print('Saved',dest)
