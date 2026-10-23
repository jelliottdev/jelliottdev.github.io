"""Replay three pinned word/boundary key-clock branches with added controls."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
from pathlib import Path

HERE=Path(__file__).resolve().parent
RESULT=HERE/'results.json'


def modules():
    out=[]
    for name in ('false_holes','wordsum_selfkey'):
        p=HERE/'source/analysis/campaign7'/f'{name}.py'
        spec=importlib.util.spec_from_file_location('source_'+name,p)
        mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out.append(mod)
    return out


def words_from_raw(raw, gp):
    words=[];cur=[]
    for char in raw:
        if gp.is_rune(char):cur.append(gp.RUNE_TO_IDX[char])
        elif cur:
            words.append(cur);cur=[]
    if cur:words.append(cur)
    return words


def score_words(mod,pages):
    by_variant={}
    best=(-999,None)
    count=0
    for variant in ('W1','W2','W3','W4','W5'):
        local=(-999,None)
        for sign in (-1,1):
            for atbash in (False,True):
                for pi,raw in enumerate(pages):
                    plain=mod.decrypt_variant(words_from_raw(raw,mod.gp),variant,sign,atbash)
                    value=mod.SC.score_norm(mod.gp.indices_to_translit(plain))
                    count+=1
                    rec={'source_page':pi,'variant':variant,'sign':sign,'atbash':atbash,
                         'score':value,'preview':mod.gp.indices_to_translit(plain)[:70],
                         'plaintext_sha256':hashlib.sha256(bytes(plain)).hexdigest()}
                    if value>local[0]:local=(value,rec)
                    if value>best[0]:best=(value,rec)
        by_variant[variant]=local[1]
    return {'candidate_count':count,'best':best[1],'by_variant':by_variant}


def corpus():
    raw=(HERE/'source/data/krisyotam_runes.txt').read_text(encoding='utf8')
    pages=[seg for seg in raw.split('%') if any(c in 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ' for c in seg)]
    assert len(pages)==57
    return pages


def plant_fh1(raw,fh):
    stream=fh.stream('DIVINITY',len(raw)+4)
    out=[];k=0
    for char in raw:
        if fh.gp.is_rune(char):
            out.append(fh.gp.IDX_TO_RUNE[(fh.gp.RUNE_TO_IDX[char]+stream[k])%29]);k+=1
        else:
            out.append(char)
            if char in {'-','.','/'}:k+=1
    assert k<=len(stream)
    return ''.join(out)


def plant_fh3(raw,fh):
    stream=fh.stream('DIVINITY',300)
    out=[];k=0
    for char in raw:
        if fh.gp.is_rune(char):
            out.append(fh.gp.IDX_TO_RUNE[(fh.gp.RUNE_TO_IDX[char]+stream[k%300])%29]);k+=1
        else:
            out.append(char)
            if char=='-':k=0
    return ''.join(out)


def plant_words(raw,mod,variant):
    original=words_from_raw(raw,mod.gp)
    output=[];k=0;cum=0;previous=0
    for word in original:
        cword=[]
        for p in word:
            if variant=='W5':
                c=(p+mod.gp.PRIMES[previous])%29
                previous=c
            else:c=(p+k)%29
            cword.append(c)
        output.append(cword)
        if variant=='W1':k=mod.primesum(cword)%29
        elif variant=='W2':k=mod.primesum(word)%29
        elif variant=='W3':cum+=mod.primesum(cword);k=cum%29
        elif variant=='W4':k=mod._totient(mod.primesum(cword))%29
    # Keep every non-rune position and replace runes in their original order.
    flat=iter(c for w in output for c in w)
    return ''.join(mod.gp.IDX_TO_RUNE[next(flat)] if mod.gp.is_rune(ch) else ch for ch in raw)


def positive_controls(fh,ws,pages):
    known=pages[-1]
    expected=fh.gp.runes_to_indices(known)
    score=fh.SC.score_norm(fh.gp.indices_to_translit(expected))
    assert score>-5
    p1=plant_fh1(known,fh)
    x=fh.fh1_spaces_advance([p1])
    assert x['rec']['sepset']=='-./' and x['rec']['key']=='DIVINITY' and abs(x['score']-score)<1e-10
    p3=plant_fh3(known,fh)
    y=fh.fh3_segment_reset([p3],known_tail=0)['best_unsolved_only']
    assert y['rec']['reset']=='word' and y['rec']['key']=='DIVINITY' and abs(y['score']-score)<1e-10
    word_plants={}
    for variant in ('W1','W2','W3','W4','W5'):
        encoded=plant_words(known,ws,variant)
        decoded=ws.decrypt_variant(words_from_raw(encoded,ws.gp),variant,-1,False)
        assert decoded==expected
        word_plants[variant]={'exact':True,'score':ws.SC.score_norm(ws.gp.indices_to_translit(decoded))}
        assert word_plants[variant]['score']>-5
    return {'known_page_score':score,'FH1_planted_exact_score':x['score'],
            'FH3_planted_exact_score':y['score'],'word_plants':word_plants}


def shuffle_pages(rawpages,mod,rng):
    out=[]
    for raw in rawpages:
        chars=list(raw)
        positions=[i for i,c in enumerate(chars) if mod.gp.is_rune(c)]
        symbols=[chars[i] for i in positions]
        rng.shuffle(symbols)
        for position,symbol in zip(positions,symbols):chars[position]=symbol
        out.append(''.join(chars))
    return out


def source_parity(fh,ws,pages):
    original=json.loads((HERE/'source/analysis/campaign7/false_holes_results.json').read_text(encoding='utf8'))
    a=fh.fh1_spaces_advance(pages)
    b=fh.fh2_first_rune_shift(pages)
    c=fh.fh3_segment_reset(pages)
    assert abs(a['score']-original['FH1_spaces_advance_keystream']['score'])<1e-10
    assert a['rec']==original['FH1_spaces_advance_keystream']['rec']
    assert abs(b['score']-original['FH2_first_rune_gematria_shift']['score'])<1e-10
    assert b['rec']==original['FH2_first_rune_gematria_shift']['rec']
    for key in ('best_all_pages','best_unsolved_only'):
        assert c[key]['rec']==original['FH3_segment_key_reset'][key]['rec']
        assert abs(c[key]['score']-original['FH3_segment_key_reset'][key]['score'])<1e-10
    d=score_words(ws,pages[:55])
    o=json.loads((HERE/'source/analysis/campaign7/wordsum_selfkey_results.json').read_text(encoding='utf8'))
    assert round(d['best']['score'],3)==o['best_score']
    assert all(d['best'][key]==o['best'][source_key] for key,source_key in [('variant','variant'),('sign','sign'),('atbash','atbash'),('source_page','page'),('preview','text')])
    for variant,score in o['per_variant_best'].items():assert round(d['by_variant'][variant]['score'],3)==score
    return {'FH1_best_all':a,'FH2_affine_subset_best_all':b,'FH3_best_all':c['best_all_pages'],
            'FH3_best_unsolved':c['best_unsolved_only'],'wordsum_best':d['best'],
            'FH3_AN_END_full_reading_not_recovered':True}


def compute():
    fh,ws=modules();pages=corpus()
    positives=positive_controls(fh,ws,pages)
    print('PASS planted controls',flush=True)
    parity=source_parity(fh,ws,pages)
    print('PASS archived source parity',flush=True)
    uns=pages[:55]
    real={'FH1':fh.fh1_spaces_advance(uns),'FH3':fh.fh3_segment_reset(uns,known_tail=0)['best_unsolved_only'],
          'word_sums':score_words(ws,uns)}
    assert real['word_sums']['candidate_count']==1100
    rng=random.Random(3301);nulls=[]
    for i in range(49):
        pp=shuffle_pages(uns,fh,rng)
        a=fh.fh1_spaces_advance(pp)['score']
        b=fh.fh3_segment_reset(pp,known_tail=0)['best_unsolved_only']['score']
        c=score_words(ws,pp)['best']['score']
        nulls.append({'replicate':i,'FH1_best':a,'FH3_best':b,'word_sums_best':c,'global_best':max(a,b,c)})
        print(f'null {i+1}/49',flush=True)
    counts={key:sum(n[{'FH1':'FH1_best','FH3':'FH3_best','word_sums':'word_sums_best'}[key]]>=
                    (real[key]['best']['score'] if key=='word_sums' else real[key]['score']) for n in nulls)
            for key in real}
    return {'schema':'liberpedia-word-boundary-key-clocks-results-v1','positive_controls':positives,
            'archived_source_parity':parity,'real':real,'null_controls':nulls,'null_at_least_observed':counts,
            'global_real_best':max(real['FH1']['score'],real['FH3']['score'],real['word_sums']['best']['score'])}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    x=compute()
    if a.check:
        saved=json.loads(RESULT.read_text(encoding='utf8'))
        assert all(saved[key]==value for key,value in x.items())
        assert saved['plan_sha256']==hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest()
        print('PASS complete saved result')
    else:
        RESULT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
        print('Saved',RESULT)
