"""Execute all called routes from the exact public P21–30 source program."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import random
import subprocess
import tempfile

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DEFAULT_SOURCE=ROOT.parent/'source-archives'/'Wulfic-Cicada3301-Liber_Primus'
def sha(x):return hashlib.sha256(x).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=pathlib.Path,default=DEFAULT_SOURCE);ap.add_argument('--check',action='store_true');args=ap.parse_args()
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf8'))
    source=args.source_root
    assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD']).decode().strip()==plan['source_revision']
    def blob(rel):
        data=subprocess.check_output(['git','-C',str(source),'show',plan['source_revision']+':'+rel])
        assert sha(data)==plan['source_files'][rel]['sha256'],rel
        return data
    script=blob('tools/legacy/p21_30_rearrange.py')
    with tempfile.TemporaryDirectory() as td:
        p=pathlib.Path(td)/'source_solver.py';p.write_bytes(script)
        spec=importlib.util.spec_from_file_location('source_solver',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    wordlist={w.strip().upper() for w in blob('data/corpora/wordlist.txt').decode().splitlines() if len(w.strip())>=2}
    raw_pages=[]
    for old in range(21,31):
        raw=blob(f'pages/page_{old:02d}/runes.txt').decode('utf8').strip()
        site_path=ROOT/f'data/pages/lp2-{old-17:02d}.json'
        assert sha(site_path.read_bytes())==plan['site_pages'][f'lp2-{old-17:02d}']
        assert m.parse_runes(raw)==m.parse_runes(json.loads(site_path.read_text(encoding='utf8'))['raw'])
        raw_pages.append((old,raw))
    def evaluate(old,raw):
        words=m.parse_runes_with_words(raw);flat=m.parse_runes(raw)
        _,mode,key=m.PAGE_CONFIG[old]
        baseline=m.decrypt(flat,key,mode)
        baseline_score=m.score_text(m.words_to_text(m.decrypt_words(words,key,mode)),wordlist)[0]
        with contextlib.redirect_stdout(io.StringIO()):
            source_rows=m.run_tests(old,flat,words,key,mode,wordlist)
        rows=[{'label':label,'word_score':points,'ioc':ioc,'preview':preview,'word_matches':matches}
              for points,ioc,label,preview,matches in source_rows]
        assert len(rows)==45,(old,len(rows))
        return {'page':f'lp2-{old-17:02d}','runes':len(flat),'words':len(words),
                'keyword':m.PAGE_CONFIG[old][0],'mode':mode,'baseline_ioc':m.compute_ioc(baseline),
                'baseline_score':baseline_score,'rows':rows}
    targets=[evaluate(old,raw) for old,raw in raw_pages]
    # Source scoreboard invariants, checked on the actual route outputs.
    word_order={'words_reverse','words_prime_first','words_by_length','words_by_gp_sum','words_by_first_char'}
    subsets={'prime_pos_0idx','prime_pos_1idx','nonprime_pos_0idx','nonprime_pos_1idx','fibonacci_pos','read_at_primes'}
    invariant={'full_length_ioc_cases':0,'word_order_score_cases':0,'subset_cases':0}
    for page in targets:
        for row in page['rows']:
            if row['label'] in subsets:invariant['subset_cases']+=1
            else:
                assert abs(row['ioc']-page['baseline_ioc'])<1e-12,(page['page'],row['label'])
                invariant['full_length_ioc_cases']+=1
            if row['label'] in word_order:
                assert row['word_score']==page['baseline_score'],(page['page'],row['label'])
                invariant['word_order_score_cases']+=1
    # Frozen full-message route/scorer control on first source page.
    old,raw=raw_pages[0]
    original_words=m.parse_runes_with_words(raw);lengths=[len(w) for w in original_words]
    choices={1:'I'}
    single_gp_letters={v for v in m.IDX_TO_LATIN.values() if len(v)==1}
    for w in sorted(wordlist):
        # Source's keyword program has no Latin-to-rune parser. Restrict the
        # control words to single-character GP labels so length is exact.
        if w.isascii() and w.isalpha() and all(c in single_gp_letters for c in w):
            n=len(w)
            if n not in choices:choices[n]=w
    assert all(n in choices for n in lengths),sorted(set(lengths)-choices.keys())
    message_words=[choices[n] for n in lengths]
    latin_single={v:i for i,v in m.IDX_TO_LATIN.items() if len(v)==1}
    known=[latin_single[ch] for word in message_words for ch in word]
    assert len(known)==len(m.parse_runes(raw))
    pre_route=known[::-1]
    key=m.PAGE_CONFIG[old][2];mode=m.PAGE_CONFIG[old][1]
    if mode=='beaufort':cipher=[(key[i%len(key)]-v)%29 for i,v in enumerate(pre_route)]
    elif mode=='add':cipher=[(v-key[i%len(key)])%29 for i,v in enumerate(pre_route)]
    else:cipher=[(v+key[i%len(key)])%29 for i,v in enumerate(pre_route)]
    assert m.rearrange_reverse(m.decrypt(cipher,key,mode))==known
    known_spaced=m.score_text(' '.join(message_words),wordlist)[0]
    known_flat=m.score_text(m.indices_to_text(known),wordlist)[0]
    # The source parser needs actual runes, not GP Latin labels.
    inverse={v:k for k,v in m.GP_RUNE_TO_IDX.items()}
    it=iter(cipher);planted_raw=''.join(inverse[next(it)] if ch in m.GP_RUNE_TO_IDX else ch for ch in raw)
    planted=evaluate(old,planted_raw)
    reverse_row=next(r for r in planted['rows'] if r['label']=='reverse')
    control={'page':'lp2-04','known_sha256':sha(bytes(known)),'cipher_sha256':sha(bytes(cipher)),
             'full_route_recovery':True,'known_spaced_score':known_spaced,'known_flat_score':known_flat,
             'source_reverse_route_score':reverse_row['word_score'],'source_reverse_route_ioc':reverse_row['ioc'],
             'source_page_word_lengths':lengths,'selected_words':message_words}
    assert known_spaced>0 and known_flat==0 and reverse_row['word_score']==0
    rng=random.Random(20261023);null=[]
    for trial in range(199):
        peaks=[]
        for old,raw in raw_pages:
            chars=[c for c in raw if c in m.GP_RUNE_TO_IDX];rng.shuffle(chars);it=iter(chars)
            shuffled=''.join(next(it) if c in m.GP_RUNE_TO_IDX else c for c in raw)
            result=evaluate(old,shuffled)
            peaks.append(max(r['word_score'] for r in result['rows']))
        null.append({'trial':trial,'global_max_score':max(peaks),'page_max_scores':peaks})
        if trial%40==0:print('null',trial,flush=True)
    out={'schema':'liberpedia-wulfic-p21-rearrangement-results-v1','plan_sha256':sha((HERE/'plan.json').read_bytes()),
         'source_wordlist_size':len(wordlist),'pages':targets,'invariants':invariant,'control':control,'null':null}
    path=HERE/'results.json'
    if args.check:assert json.loads(path.read_text(encoding='utf8'))==out
    else:path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    print('target top',max((r['word_score'],p['page'],r['label']) for p in targets for r in p['rows']))
    print('invariants',invariant,'control',known_spaced,known_flat)

if __name__=='__main__':main()
