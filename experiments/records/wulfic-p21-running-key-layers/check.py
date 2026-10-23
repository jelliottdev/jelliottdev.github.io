"""Check the saved source replay via original source functions and Git blobs.

The source search itself is not re-used from run.py. This checker reconstructs
all 24,639 target and 49 complete shuffled grids independently.
"""
import argparse
import collections
import hashlib
import importlib.util
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
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=pathlib.Path,default=DEFAULT_SOURCE);args=ap.parse_args()
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf8'))
    results=json.loads((HERE/'results.json').read_text(encoding='utf8'))
    controls=json.loads((HERE/'controls.json').read_text(encoding='utf8'))
    powers=[json.loads((HERE/name).read_text(encoding='utf8')) for name in ('power-addendum.json','power-addendum-v2.json','power-addendum-v3.json')]
    assert results['plan_sha256']==sha((HERE/'plan.json').read_bytes())
    assert results['control_plan_sha256']==sha((HERE/'control-plan-v2.json').read_bytes())
    for power,name in zip(powers,('power-addendum-plan.json','power-addendum-v2-plan.json','power-addendum-v3-plan.json')):
        assert power['plan_sha256']==sha((HERE/name).read_bytes())
    source=args.source_root
    assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD']).decode().strip()==plan['source_revision']
    def blob(name):
        b=subprocess.check_output(['git','-C',str(source),'show',plan['source_revision']+':'+name])
        assert sha(b)==plan['source_files'][name]['sha256']
        return b
    for name in plan['source_files']:blob(name)
    # Import raw committed bytes, not the working file: a Windows checkout may
    # apply CRLF conversion without changing the pinned Git object.
    with tempfile.TemporaryDirectory() as tmp:
        sp=pathlib.Path(tmp)/'source_solver.py'
        sp.write_bytes(blob('tools/legacy/p21_30_autokey_solver.py'))
        spec=importlib.util.spec_from_file_location('source_solver',sp);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    corpora={name:m.text_to_indices(''.join(c for c in blob('data/corpora/'+filename+'.txt').decode('utf8') if c.isalpha() or c==' ')) for name,filename in [('deor','deor_poem'),('self_reliance','self_reliance')]}
    assert {k:len(v) for k,v in corpora.items()}==results['corpus_rune_lengths']
    pages=[]
    for old in range(21,31):
        raw=blob(f'pages/page_{old:02d}/runes.txt').decode('utf8').strip()
        cipher=m.parse_runes(raw)
        site_path=ROOT/f'data/pages/lp2-{old-17:02d}.json'
        assert sha(site_path.read_bytes())==plan['site_pages'][f'lp2-{old-17:02d}']
        assert cipher==m.parse_runes(json.loads(site_path.read_text(encoding='utf8'))['raw'])
        pages.append((f'lp2-{old-17:02d}',cipher,m.PAGE_CONFIG[old][2]))
    raw0=blob('pages/page_21/runes.txt').decode('utf8').strip()
    lengths=[];current=0
    for char in raw0:
        if char in m.GP_RUNE_TO_IDX:current+=1
        elif char in '-. ' and current:lengths.append(current);current=0
    if current:lengths.append(current)
    assert sum(lengths)==len(pages[0][1])
    lex={w.strip().upper() for w in blob('data/corpora/wordlist.txt').decode().splitlines() if 3<=len(w.strip())<=15}
    def cases(pages):
        counts=collections.Counter();peak={}
        for page,cipher,keyword in pages:
            n=len(cipher)
            for name,run in corpora.items():
                max_off=len(run)-n
                if max_off<0:continue
                for off in range(0,max_off,max(1,max_off//200)):
                    for mode in ('sub','add','beaufort'):
                        plain=m.running_key_decrypt(cipher,run,off,mode)
                        counts['running']+=1
                        value=m.compute_ioc(plain)
                        peak['running']=max(peak.get('running',0),value)
                        if value>1.3:counts['running_passed']+=1
                for off in range(0,max_off,max(1,max_off//100)):
                    for combine in ('plus','minus'):
                        key=[(keyword[i%len(keyword)]+(1 if combine=='plus' else -1)*run[off+i])%29 for i in range(n)]
                        for mode in ('sub','add','beaufort'):
                            if mode=='sub':plain=[(c-k)%29 for c,k in zip(cipher,key)]
                            elif mode=='add':plain=[(c+k)%29 for c,k in zip(cipher,key)]
                            else:plain=[(k-c)%29 for c,k in zip(cipher,key)]
                            counts['layered']+=1
                            value=m.compute_ioc(plain)
                            peak['layered']=max(peak.get('layered',0),value)
                            if value>1.3:counts['layered_passed']+=1
        return dict(counts),peak
    target_counts,target_peak=cases(pages)
    assert target_counts==results['target']['counts']
    assert all(abs(target_peak[k]-v)<1e-12 for k,v in results['target']['peak_ioc'].items())
    assert results['target']['global_best'] is None
    assert all(x is None for x in results['target']['best_by_page'].values())
    rng=random.Random(20261023)
    assert len(results['null'])==49
    for trial,row in enumerate(results['null']):
        shuffled=[]
        for page,cipher,keyword in pages:
            c=cipher.copy();rng.shuffle(c);shuffled.append((page,c,keyword))
        null_counts,_=cases(shuffled)
        assert row['trial']==trial and null_counts==row['counts']
        assert row['global_best_score']==0 and row['global_best_ioc']==0
    assert len(controls['cases'])==9 and all(c['full_recovery'] and c['passed_source_gate'] for c in controls['cases'])
    choices={1:'I'}
    for word in sorted(lex):
        if word.isascii() and word.isalpha():
            n=len(m.text_to_indices(word))
            if n and n not in choices:choices[n]=word
    assert controls['construction_words']==[choices[n] for n in lengths]
    known_control=[x for word in controls['construction_words'] for x in m.text_to_indices(word)]
    assert len(known_control)==len(pages[0][1])
    def score(indices):
        pos=0;words=[]
        for n in lengths:
            words.append(m.indices_to_text(indices[pos:pos+n]));pos+=n
        return m.score_text(' '.join(words),lex)[0]
    def keys(key_source,combine):
        running=corpora[key_source][:len(known_control)]
        if combine=='none':return running
        keyword=pages[0][2]
        return [(keyword[i%len(keyword)]+(1 if combine=='plus' else -1)*running[i])%29 for i in range(len(running))]
    def encrypt(plain,key,mode):
        if mode=='sub':return [(p+k)%29 for p,k in zip(plain,key)]
        if mode=='add':return [(p-k)%29 for p,k in zip(plain,key)]
        return [(k-p)%29 for p,k in zip(plain,key)]
    for saved in controls['cases']:
        key=keys('deor',saved['combine'])
        cipher=encrypt(known_control,key,saved['mode'])
        if saved['branch']=='running':decoded=m.running_key_decrypt(cipher,corpora['deor'],0,saved['mode'])
        else:
            if saved['mode']=='sub':decoded=[(c-k)%29 for c,k in zip(cipher,key)]
            elif saved['mode']=='add':decoded=[(c+k)%29 for c,k in zip(cipher,key)]
            else:decoded=[(k-c)%29 for c,k in zip(cipher,key)]
        assert decoded==known_control and saved['full_recovery']
        assert saved['message_sha256']==sha(bytes(known_control)) and saved['cipher_sha256']==sha(bytes(cipher))
        assert abs(saved['ioc']-m.compute_ioc(decoded))<1e-12
        assert saved['word_score']==score(decoded)>0 and saved['passed_source_gate'] and saved['ioc']>1.3
    known_readings_path=ROOT/'data/evidence/known-readings.json'
    v3plan=json.loads((HERE/'power-addendum-v3-plan.json').read_text(encoding='utf8'))
    assert sha(known_readings_path.read_bytes())==v3plan['known_readings_sha256']
    welcome=next(v for v in json.loads(known_readings_path.read_text(encoding='utf8'))['controls'] if v['id']=='welcome')['decoded_pages']
    for version,power in enumerate(powers):
        known=corpora['deor'][:len(pages[0][1])] if version<2 else welcome[0]['rune_indices']+welcome[1]['rune_indices'][:10]
        key_name='deor' if version==0 else 'self_reliance'
        key=corpora[key_name][:len(known)]
        cipher=encrypt(known,key,'sub')
        assert len(known)==len(pages[0][1]) and m.running_key_decrypt(cipher,corpora[key_name],0,'sub')==known
        assert power['full_recovery'] and power['known_sha256']==sha(bytes(known)) and power['cipher_sha256']==sha(bytes(cipher))
        assert abs(power['known_ioc']-m.compute_ioc(known))<1e-12 and power['known_word_score']==score(known)
        candidates=[]
        for source_name,run in corpora.items():
            max_off=len(run)-len(cipher)
            for offset in range(0,max_off,max(1,max_off//200)):
                for mode in ('sub','add','beaufort'):
                    plain=m.running_key_decrypt(cipher,run,offset,mode);ci=m.compute_ioc(plain)
                    if ci>1.3:candidates.append((score(plain),ci,'running',source_name,offset,mode,'none'))
            for offset in range(0,max_off,max(1,max_off//100)):
                for combine in ('plus','minus'):
                    keyword=pages[0][2]
                    kval=[(keyword[i%len(keyword)]+(1 if combine=='plus' else -1)*run[offset+i])%29 for i in range(len(cipher))]
                    for mode in ('sub','add','beaufort'):
                        if mode=='sub':plain=[(c-k)%29 for c,k in zip(cipher,kval)]
                        elif mode=='add':plain=[(c+k)%29 for c,k in zip(cipher,kval)]
                        else:plain=[(k-c)%29 for c,k in zip(cipher,kval)]
                        ci=m.compute_ioc(plain)
                        if ci>1.3:candidates.append((score(plain),ci,'layered',source_name,offset,mode,combine))
        candidates.sort(key=lambda x:(-x[0],-x[1]))
        rank=next(i+1 for i,c in enumerate(candidates) if c[2:] == ('running',key_name,0,'sub','none'))
        assert rank==power['true_rank']
        assert candidates[0][:2]==(power['best']['word_score'],power['best']['ioc'])
    log=(HERE/'source-log.txt').read_text(encoding='utf-8-sig')
    assert log.count('No results with IoC > 1.3')==10
    print('PASS: 24,639 target cells, 49 full-grid nulls, original-source 10-page verdict, nine controls, three post-target one-page diagnostics')

if __name__=='__main__':main()
