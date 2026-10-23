"""One grouped, source-specific replay of three finite prime/keyword stream families."""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

from engine import (MODES, STEPPED_VARIANTS, decode, fskip_decode, key_matrix,
                    normalized_ioc, prime_key, prime_orderings, quick_score,
                    repeated, singleton_count, stepped_selected, stream_hash)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
N_NULL = 49
SEED = 20261023


def load():
    data=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    pages={int(k):v for k,v in data['pages'].items()}
    for page,row in pages.items():
        raw=(ROOT/row['site_path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==row['site_sha256']
        assert len(row['runes'])>0
    return data,pages


def all_keyword(pages,words,ciphers,detail):
    best=None;best_fit=None;hit_count=0;full_count=0;rows=[]
    for page in range(21,31):
        row=pages[page];cipher=np.asarray(ciphers[page],dtype=np.uint8)
        page_best=None;page_hits=0
        for name,word in words.items():
            key=repeated(word,len(cipher))
            for mode in MODES:
                plain=decode(cipher,key,mode)
                ioc=normalized_ioc(plain)
                hits=singleton_count(plain,row['keyword_singletons'])
                all_fit=bool(row['keyword_singletons']) and hits==len(row['keyword_singletons'])
                page_hits+=all_fit;hit_count+=all_fit;full_count+=1
                case={'page':row['site_page'],'keyword':name,'mode':mode,
                      'ioc':ioc,'singletons_fit':hits,'singletons_total':len(row['keyword_singletons'])}
                if detail:case['decoded_sha256']=stream_hash(plain)
                if page_best is None or ioc>page_best['ioc']:page_best=case
                if best is None or ioc>best['ioc']:best=case
                if all_fit and (best_fit is None or ioc>best_fit['ioc']):best_fit=case
        if detail:rows.append({'page':row['site_page'],'candidate_count':len(words)*3,
                               'all_singleton_fit_count':page_hits,'max_ioc':page_best})
    result={'candidate_count':full_count,'all_singleton_fit_count':hit_count,
            'max_ioc':best,'best_all_singleton_fit':best_fit}
    if detail:result['pages']=rows
    return result


def prime_configs(n):
    sequences,all_primes=prime_orderings(n)
    configs=[]
    for label,primes in sequences:
        for kind in ('totient','p_mod29','idx_mod29'):
            key=prime_key(primes,kind,all_primes)
            for mode in MODES:
                configs.append((label,kind,mode,False,key))
                if label.startswith('seq_off'):
                    configs.append((label,kind,mode,True,key))
    return configs


def all_prime(pages,ciphers,configs,detail):
    best=None;source_top=None;screen_count=0;full_count=0;rows=[]
    for page in (21,22,24,26,27,28,29,30):
        row=pages[page];cipher=np.asarray(ciphers[page],dtype=np.uint8)
        page_best=None;page_screen=0
        for label,kind,mode,fskip,key in configs[page]:
            plain=fskip_decode(cipher,key,mode) if fskip else decode(cipher,key,mode)
            ioc=normalized_ioc(plain)
            score=quick_score(plain)
            singles=0 if fskip else singleton_count(plain,row['prime_singletons'])
            total=0 if fskip else len(row['prime_singletons'])
            screen=bool(ioc>1.2 or score>100 or (not fskip and total>0 and singles>total*.5))
            if label.startswith('seq_off'):
                page_screen+=screen;screen_count+=screen
            full_count+=1
            case={'page':row['site_page'],'sequence':label,'key_form':kind,
                  'mode':mode,'f_skip':fskip,'ioc':ioc,'quick_score':score,
                  'singletons_fit':singles,'singletons_total':total}
            rank_score=score+ioc*30+singles*20
            if detail:case['decoded_sha256']=stream_hash(plain)
            if page_best is None or ioc>page_best['ioc']:page_best=case
            if best is None or ioc>best['ioc']:best=case
            if (not label.startswith('seq_off') or screen) and (source_top is None or rank_score>source_top['source_rank_score']):
                source_top={**case,'source_rank_score':rank_score}
        if detail:rows.append({'page':row['site_page'],'candidate_count':len(configs[page]),
                               'sequential_screen_count':page_screen,'max_ioc':page_best})
    result={'candidate_count':full_count,'sequential_screen_count':screen_count,
            'max_ioc':best,'source_top_retained':source_top}
    if detail:result['pages']=rows
    return result


def stepped_case(row,mode_index,ioc,decoded_hash,names):
    offset=row%1001
    variant_index=(row//1001)%8
    keyword_index=row//(1001*8)
    return {'keyword':names[keyword_index], 'variant':STEPPED_VARIANTS[variant_index],
            'offset':offset,'mode':MODES[mode_index], 'ioc':ioc,
            'decoded_sha256':decoded_hash}


def all_stepped(pages,ciphers,names,keys,detail):
    best=None;hits=0;survivors=0;rows=[]
    for page in (28,53,24,39,29,30,34,51,21,33,45):
        row=pages[page];cipher=ciphers[page]
        found=stepped_selected(cipher,row['stepped_singletons'],keys)
        page_hits=sum(score>1.3 for _,_,score,_ in found)
        hits+=page_hits;survivors+=len(found)
        page_best=None
        if found:
            winner=max(found,key=lambda item:item[2])
            page_best=stepped_case(*winner,names)
            page_best['page']=row['site_page']
            if best is None or page_best['ioc']>best['ioc']:best=page_best
        if detail:rows.append({'page':row['site_page'],'source_configurations':len(keys)*3,
                               'all_singleton_fit_count':len(found),'ioc_above_1_3_count':page_hits,
                               'max_ioc_after_singleton_gate':page_best})
    result={'source_configurations':len(keys)*3*11,'all_singleton_fit_count':survivors,
            'ioc_above_1_3_count':hits,'max_ioc_after_singleton_gate':best}
    if detail:result['pages']=rows
    return result


def planted_controls(pages,words,names,keys,prime):
    result=[]
    examples=[('keyword_only',21,words['CABAL'],0),
              ('prime_stream',21,prime[21][0][4],0),
              ('keyword_stepped',39,keys[0],0)]
    for group,page,key,_ in examples:
        n=len(pages[page]['runes'])
        singleton_key={'keyword_only':'keyword_singletons','prime_stream':'prime_singletons',
                       'keyword_stepped':'stepped_singletons'}[group]
        plain=np.resize(np.asarray([10,24,18,16],dtype=np.uint8),n)
        for i,pos in enumerate(pages[page][singleton_key]):plain[pos]=(10,24)[i%2]
        full_key=np.resize(np.asarray(key,dtype=np.int64),n)
        cipher=((plain.astype(np.int64)+full_key)%29).astype(np.uint8)
        recovered=decode(cipher,full_key,'sub')
        assert np.array_equal(recovered,plain)
        assert normalized_ioc(recovered)>1.3
        assert singleton_count(recovered,pages[page][singleton_key])==len(pages[page][singleton_key])
        result.append({'branch':group,'source_page':page,'runes':n,
                       'planted_plain_sha256':stream_hash(plain),'cipher_sha256':stream_hash(cipher),
                       'exact_recovery':True,'normalized_ioc':normalized_ioc(plain)})
    return result


def execute():
    start=time.monotonic()
    data,pages=load()
    ciphers={page:row['runes'] for page,row in pages.items()}
    max_length=max(len(row['runes']) for row in pages.values())
    names,keys,max_prime_index=key_matrix(data['stepped_keywords'],max_length)
    prime={page:prime_configs(len(pages[page]['runes'])) for page in (21,22,24,26,27,28,29,30)}
    controls=planted_controls(pages,data['keyword_only'],names,keys,prime)
    observed={
        'keyword_only':all_keyword(pages,data['keyword_only'],ciphers,True),
        'prime_stream':all_prime(pages,ciphers,prime,True),
        'keyword_stepped':all_stepped(pages,ciphers,names,keys,True),
    }
    rng=random.Random(SEED)
    null=[]
    for trial in range(N_NULL):
        shuffled={}
        for page in sorted(pages):
            row=ciphers[page][:]
            rng.shuffle(row)
            shuffled[page]=row
        kw=all_keyword(pages,data['keyword_only'],shuffled,False)
        pr=all_prime(pages,shuffled,prime,False)
        st=all_stepped(pages,shuffled,names,keys,False)
        null.append({'trial':trial,
                     'keyword_only_max_ioc':kw['max_ioc']['ioc'],
                     'keyword_only_all_singleton_fit_count':kw['all_singleton_fit_count'],
                     'prime_stream_max_ioc':pr['max_ioc']['ioc'],
                     'prime_stream_sequential_screen_count':pr['sequential_screen_count'],
                     'keyword_stepped_max_ioc':None if st['max_ioc_after_singleton_gate'] is None else st['max_ioc_after_singleton_gate']['ioc'],
                     'keyword_stepped_ioc_above_1_3_count':st['ioc_above_1_3_count']})
        if (trial+1)%10==0:print(f'control {trial+1}/{N_NULL}',flush=True)
    combined_keys=json.loads((ROOT/'experiments/records/wulfic-keyword-prime-layer-grid/keys.json').read_text(encoding='utf-8'))
    assert len(combined_keys)==16 and all(data['stepped_keywords'][name]==vector for name,vector in combined_keys.items())
    return {
        'schema':'liberpedia-wulfic-prime-keyword-batch-results-v1',
        'source_commit':data['source_commit'],'input_sha256':hashlib.sha256((HERE/'inputs.json').read_bytes()).hexdigest(),
        'stepped_key_matrix':{'rows':len(keys),'max_page_runes':max_length,'max_prime_index_used':max_prime_index},
        'duplicate_configuration_crosswalk':{
            'combined_record':'wulfic-keyword-prime-layer-grid',
            'same_literal_keyword_vectors':len(combined_keys),
            'keyword_add_sequential_source_cases_in_combined_grid':16*50*2*11,
            'condition':'16 common keyword arrays, source prime-totient offsets0..49, sub/add decoding, and eleven source pages all lie within the earlier combined grid; Beaufort and offsets50..1000 are not counted as overlaps.'
        },
        'planted_controls':controls,'observed':observed,
        'null_seed':SEED,'null_trials':N_NULL,'null':null,
        'null_ge':{
            'keyword_only_max_ioc':sum(x['keyword_only_max_ioc']>=observed['keyword_only']['max_ioc']['ioc'] for x in null),
            'prime_stream_max_ioc':sum(x['prime_stream_max_ioc']>=observed['prime_stream']['max_ioc']['ioc'] for x in null),
            'keyword_stepped_max_ioc':sum((x['keyword_stepped_max_ioc'] or -1)>=(observed['keyword_stepped']['max_ioc_after_singleton_gate'] or {'ioc':-1})['ioc'] for x in null),
            'keyword_stepped_hit_count':sum(x['keyword_stepped_ioc_above_1_3_count']>=observed['keyword_stepped']['ioc_above_1_3_count'] for x in null),
        },
        'elapsed_seconds':round(time.monotonic()-start,2)
    }


def main():
    result=execute()
    target=HERE/'results.json'
    if '--check' in sys.argv:
        saved=json.loads(target.read_text(encoding='utf-8'))
        result.pop('elapsed_seconds');saved.pop('elapsed_seconds')
        assert result==saved
    else:
        target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS: three source-specific grids and 49 full-procedure controls')


if __name__=='__main__':main()
