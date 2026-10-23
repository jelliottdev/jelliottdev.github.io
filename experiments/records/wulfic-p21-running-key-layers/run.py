"""Replay the two running-key branches of Wulfic's pinned P21–30 script.

The unlicensed upstream script/corpora are loaded from an exact pinned Git
checkout, never copied into this record. All search arithmetic is independent.
"""
import argparse
import collections
import hashlib
import json
import pathlib
import random
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEFAULT_SOURCE = ROOT.parent / 'source-archives' / 'Wulfic-Cicada3301-Liber_Primus'
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
LABELS = ('F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S','T','B','E','M','L','NG','OE','D','A','AE','Y','IA','EA')
RUNE_MAP = {c:i for i,c in enumerate(RUNES)}
LABEL_MAP = {s:i for i,s in enumerate(LABELS)}
CONFIG = {
  21:('CABAL',[5,24,17,24,20]),22:('DIVINITY',[23,10,1,10,9,10,16,26]),
  23:('ENCRYPTION',[18,9,5,4,26,13,16,10,3,9]),24:('OBSCURA',[3,17,15,5,1,4,24]),
  25:('CABAL',[5,24,17,24,20]),26:('ENCRYPT',[18,9,5,4,26,13,16]),
  27:('SHADOWS',[15,8,24,23,3,7,15]),28:('DEOR',[23,18,3,4]),
  29:('TOTIENT',[16,3,16,10,18,9,16]),30:('MOURNFUL',[19,3,1,4,9,0,1,20])}
MODES = ('sub','add','beaufort')

def digest(data): return hashlib.sha256(data).hexdigest()

def source_bytes(source, rel, plan):
    data = subprocess.check_output(['git','-C',str(source),'show',plan['source_revision']+':'+rel])
    assert digest(data) == plan['source_files'][rel]['sha256'], rel
    return data

def gp_text(s):
    s = s.upper()
    ans=[]; i=0
    aliases={'K':'C','V':'U','Q':'C','Z':'S'}
    while i<len(s):
        pair=s[i:i+2]
        if pair in LABEL_MAP:
            ans.append(LABEL_MAP[pair]); i+=2; continue
        c=aliases.get(s[i],s[i])
        if c in LABEL_MAP: ans.append(LABEL_MAP[c])
        i+=1
    return ans

def source_running_text(data):
    return gp_text(''.join(c for c in data.decode('utf8') if c.isalpha() or c==' '))

def source_words(raw):
    words=[]; cur=[]
    for c in raw:
        if c in RUNE_MAP: cur.append(RUNE_MAP[c])
        elif c in '-. ' and cur:
            words.append(cur);cur=[]
    if cur: words.append(cur)
    return [len(x) for x in words]

def ioc(x):
    if len(x)<2:return 0.0
    freq=collections.Counter(x)
    return 29*sum(v*(v-1) for v in freq.values())/(len(x)*(len(x)-1))

def decode(cipher, key, mode):
    if mode=='sub':return [(c-k)%29 for c,k in zip(cipher,key)]
    if mode=='add':return [(c+k)%29 for c,k in zip(cipher,key)]
    return [(k-c)%29 for c,k in zip(cipher,key)]

def encrypt(plain, key, mode):
    if mode=='sub':return [(p+k)%29 for p,k in zip(plain,key)]
    if mode=='add':return [(p-k)%29 for p,k in zip(plain,key)]
    return [(k-p)%29 for p,k in zip(plain,key)]

def key_for(running, offset, size, keyword=None, combine=None):
    r=running[offset:offset+size]
    if keyword is None:return r
    if combine=='plus':return [(keyword[i%len(keyword)]+r[i])%29 for i in range(size)]
    return [(keyword[i%len(keyword)]-r[i])%29 for i in range(size)]

def latin_words(plain,lengths):
    pos=0; out=[]
    for n in lengths:
        out.append(''.join(LABELS[v] for v in plain[pos:pos+n])); pos+=n
    return out

def score(plain, lengths, lexicon):
    words=latin_words(plain,lengths)
    total=0; matched=[]
    transforms=(lambda x:x.replace('NG','ING'),lambda x:x.replace('IA','ION'),lambda x:x.replace('C','K'),lambda x:x.replace('U','V'))
    for w in words:
        if w in lexicon:total+=len(w)**2;matched.append(w)
        for transform in transforms:
            w2=transform(w)
            if w2!=w and w2 in lexicon:
                total+=len(w2)**2;matched.append(w2);break
    return total,matched

def grid(cipher, corpora, keyword):
    n=len(cipher)
    for name,run in corpora.items():
        max_off=len(run)-n
        if max_off<0:continue
        for off in range(0,max_off,max(1,max_off//200)):
            key=key_for(run,off,n)
            for mode in MODES:
                yield ('running',name,off,mode,'none',key)
        for off in range(0,max_off,max(1,max_off//100)):
            for combine in ('plus','minus'):
                key=key_for(run,off,n,keyword,combine)
                for mode in MODES:
                    yield ('layered',name,off,mode,combine,key)

def search(pages,corpora,lexicon,keep=False):
    global_best=None; best_by_page={}; totals=collections.Counter(); top=[]; peak={}
    for page,cipher,lengths,keyword in pages:
        page_best=None
        for branch,name,off,mode,combine,key in grid(cipher,corpora,keyword):
            totals[branch]+=1
            plain=decode(cipher,key,mode)
            value=ioc(plain)
            if value>peak.get(branch,0):peak[branch]=value
            if value<=1.3:continue
            totals[branch+'_passed']+=1
            points,matches=score(plain,lengths,lexicon)
            if points: totals[branch+'_word_positive']+=1
            row={'page':page,'branch':branch,'corpus':name,'offset':off,'mode':mode,'combine':combine,
                 'ioc':value,'word_score':points,'word_matches':matches[:12],
                 'plain_sha256':digest(bytes(plain)),
                 'preview':' '.join(latin_words(plain,lengths))[:150]}
            rank=(points,value)
            if page_best is None or rank>(page_best['word_score'],page_best['ioc']):page_best=row
            if global_best is None or rank>(global_best['word_score'],global_best['ioc']):global_best=row
            if keep: top.append(row)
        best_by_page[page]=page_best
    if keep:
        top.sort(key=lambda r:(-r['word_score'],-r['ioc']))
    return {'counts':dict(totals),'peak_ioc':peak,'best_by_page':best_by_page,'global_best':global_best,'top':top[:40] if keep else []}

def make_control(lengths,lexicon):
    choices={1:'I'}
    for w in sorted(lexicon):
        if not w.isascii() or not w.isalpha():continue
        n=len(gp_text(w))
        if n and n not in choices:choices[n]=w
    assert all(n in choices for n in lengths), sorted(set(lengths)-choices.keys())
    picked=[choices[n] for n in lengths]
    plain=[v for w in picked for v in gp_text(w)]
    return plain,picked

def controls(page,run,keyword,lexicon):
    page_id,cipher,lengths,_=page
    known,words=make_control(lengths,lexicon)
    assert len(known)==len(cipher)
    items=[]
    for branch in ('running','layered'):
        for combine in (('none',) if branch=='running' else ('plus','minus')):
            key=key_for(run,0,len(known),None if branch=='running' else keyword,None if branch=='running' else combine)
            for mode in MODES:
                enc=encrypt(known,key,mode)
                got=decode(enc,key,mode)
                points,matched=score(got,lengths,lexicon)
                items.append({'branch':branch,'combine':combine,'mode':mode,'full_recovery':got==known,
                              'ioc':ioc(got),'word_score':points,'passed_source_gate':ioc(got)>1.3 and points>0,
                              'message_sha256':digest(bytes(known)),'cipher_sha256':digest(bytes(enc))})
    return {'page':page_id,'construction_words':words,'cases':items}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source-root',type=pathlib.Path,default=DEFAULT_SOURCE)
    ap.add_argument('--controls-only',action='store_true')
    ap.add_argument('--null-trials',type=int,default=49)
    args=ap.parse_args()
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf8'))
    src=args.source_root
    assert subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD']).decode().strip()==plan['source_revision']
    corpora={key:source_running_text(source_bytes(src,'data/corpora/'+file+'.txt',plan)) for key,file in (('deor','deor_poem'),('self_reliance','self_reliance'))}
    lexicon={w.strip().upper() for w in source_bytes(src,'data/corpora/wordlist.txt',plan).decode().splitlines() if 3<=len(w.strip())<=15}
    pages=[]
    for p in range(21,31):
        raw=source_bytes(src,f'pages/page_{p:02d}/runes.txt',plan).decode('utf8').strip()
        cipher=[RUNE_MAP[c] for c in raw if c in RUNE_MAP]
        site=json.loads((ROOT/f'data/pages/lp2-{p-17:02d}.json').read_text(encoding='utf8'))
        assert digest((ROOT/f'data/pages/lp2-{p-17:02d}.json').read_bytes())==plan['site_pages'][f'lp2-{p-17:02d}']
        assert cipher==[RUNE_MAP[c] for c in site['raw'] if c in RUNE_MAP]
        pages.append((f'lp2-{p-17:02d}',cipher,source_words(raw),CONFIG[p][1]))
    control=controls(pages[0],corpora['deor'],CONFIG[21][1],lexicon)
    (HERE/'controls.json').write_text(json.dumps(control,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
    print('Controls:',len(control['cases']), 'passing:',sum(v['passed_source_gate'] for v in control['cases']))
    if args.controls_only:return
    result=search(pages,corpora,lexicon,True)
    rng=random.Random(20261023);null=[]
    for trial in range(args.null_trials):
        shuffled=[]
        for page,cipher,lengths,keyword in pages:
            arr=cipher.copy();rng.shuffle(arr)
            shuffled.append((page,arr,lengths,keyword))
        rr=search(shuffled,corpora,lexicon)
        null.append({'trial':trial,'global_best_score':rr['global_best']['word_score'] if rr['global_best'] else 0,
                     'global_best_ioc':rr['global_best']['ioc'] if rr['global_best'] else 0,
                     'counts':rr['counts']})
        if trial%10==0:print('Null trial',trial,flush=True)
    final={'schema':'liberpedia-wulfic-p21-running-key-results-v1','plan_sha256':digest((HERE/'plan.json').read_bytes()),
           'control_plan_sha256':digest((HERE/'control-plan-v2.json').read_bytes()),'corpus_rune_lengths':{k:len(v) for k,v in corpora.items()},
           'target':result,'null':null}
    (HERE/'results.json').write_text(json.dumps(final,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
    print('Target global best',result['global_best'])

if __name__=='__main__':main()
