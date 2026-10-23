"""Corrected-IoC replay of the called Wulfic PIP and P.S. source grids."""
import argparse
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = HERE / 'plan.json'
RUNES = [0x16A0,0x16A2,0x16A6,0x16A9,0x16B1,0x16B3,0x16B7,0x16B9,0x16BB,
         0x16BE,0x16C1,0x16C4,0x16C7,0x16C8,0x16C9,0x16CB,0x16CF,0x16D2,
         0x16D6,0x16D7,0x16DA,0x16DD,0x16DF,0x16DE,0x16AA,0x16AB,0x16A3,
         0x16E1,0x16E0]
MAP = {chr(x): i for i, x in enumerate(RUNES)}
SEPARATORS = set('-. \n\r\t\u2022•/&$%')
MODES = ('sub','add','beaufort')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_words(text):
    words=[]; current=[]
    for ch in text:
        if ch in MAP:
            current.append(MAP[ch])
        elif ch in SEPARATORS:
            if current:
                words.append(current); current=[]
    if current:
        words.append(current)
    return [x for word in words for x in word], [len(word) for word in words]


def singleton_positions(lengths):
    ans=[]; pos=0
    for size in lengths:
        if size == 1: ans.append(pos)
        pos += size
    return ans


def source_primes(limit):
    flags=bytearray([1])*(limit+1)
    flags[0:2]=bytes([0,0])
    for p in range(2,int(limit**0.5)+1):
        if flags[p]:
            flags[p*p:limit+1:p]=bytes([0])*(((limit-p*p)//p)+1)
    return [i for i,flag in enumerate(flags) if flag]


def keys(plan):
    primes=source_primes(plan['source_rules']['pip_prime_limit'])
    pips=[primes[primes[n]-1] for n in range(min(50000,len(primes))) if primes[n]-1<len(primes)]
    ps=plan['source_rules']['ps_number']
    assert len(ps)==132
    n=int(ps); base=[]
    while n:
        base.append(n%29); n//=29
    base.reverse()
    return {
        'pip':[x%29 for x in pips],
        'ps-digits':[int(ch) for ch in ps],
        'ps-pairs':[int(ps[i:i+2])%29 for i in range(0,len(ps)-1,2)],
        'ps-base29':base,
    }, pips


def page_inputs(plan):
    audit=json.loads((HERE/'input-audit.json').read_text(encoding='utf-8'))
    assert digest(HERE/'input-audit.json')==plan['input_manifest']['sha256']
    assert [a['old'] for a in audit]==list(range(21,55))
    pages=[]
    for a in audit:
        path=ROOT/'data/pages'/f"{a['page']}.json"
        assert digest(path)==a['site_sha256']
        page=json.loads(path.read_text(encoding='utf-8'))
        flat,lengths=parse_words(page['raw'])
        assert page['id']==a['page'] and len(flat)==a['length']
        assert lengths==a['source_word_lengths']
        assert a['flat_equal'] and a['words_equal']
        pages.append({'old':a['old'],'page':a['page'],'flat':flat,
                      'lengths':lengths,'singletons':singleton_positions(lengths)})
    return pages


def decrypt_value(c,k,mode):
    if mode=='sub': return (c-k)%29
    if mode=='add': return (c+k)%29
    return (k-c)%29


def encrypt_value(p,k,mode):
    if mode=='sub': return (p+k)%29
    if mode=='add': return (p-k)%29
    return (k-p)%29


def normalized_ioc(plain):
    n=len(plain)
    if n<2: return 0.0
    f=[0]*29
    for x in plain: f[x]+=1
    return 29*sum(v*(v-1) for v in f)/(n*(n-1))


def screen(flat,singletons,key,offset,mode):
    for i in singletons:
        if decrypt_value(flat[i],key[offset+i],mode) not in (10,24):
            return None
    freq=[0]*29
    for i,c in enumerate(flat):
        freq[decrypt_value(c,key[offset+i],mode)]+=1
    n=len(flat)
    return 29*sum(v*(v-1) for v in freq)/(n*(n-1)) if n>1 else 0.0


def configurations(page,keyset):
    n=len(page['flat'])
    for name,key in keyset.items():
        cap=1000 if name=='pip' else 50
        for offset in range(max(0,min(cap,len(key)-n))):
            for mode in MODES:
                yield name,key,offset,mode


def positive_controls(keyset):
    solved=json.loads((ROOT/'data/pages/lp1-10.json').read_text(encoding='utf-8'))
    base=[MAP[ch] for ch in solved['reviewed_text'] if ch in MAP]
    assert len(base)==187
    plants=[]
    for name,key in keyset.items():
        length=100 if len(key)>=105 else 60
        plain=base[:length]+[10,24]
        assert len(key)>=len(plain)+3
        singleton=[len(plain)-2,len(plain)-1]
        for mode in MODES:
            cipher=[encrypt_value(p,key[3+i],mode) for i,p in enumerate(plain)]
            recovered=[decrypt_value(c,key[3+i],mode) for i,c in enumerate(cipher)]
            assert recovered==plain
            value=screen(cipher,singleton,key,3,mode)
            assert value is not None and value>1.3, (name,mode,value)
            plants.append({'key':name,'mode':mode,'offset':3,'length':len(plain),
                           'exact_recovery':True,'singleton_pass':True,'normalized_ioc':round(value,9)})
    return plants


def gate(plan):
    pages=page_inputs(plan)
    keyset,pips=keys(plan)
    assert len(pages)==34
    assert all(0<=x<29 for key in keyset.values() for x in key)
    lengths={name:len(key) for name,key in keyset.items()}
    configs={name:0 for name in keyset}
    for page in pages:
        for name,_,_,_ in configurations(page,keyset): configs[name]+=1
    assert configs['pip']>0 and configs['ps-digits']>0
    assert configs['ps-pairs']==configs['ps-base29']==0
    return pages,keyset,{
        'plan_sha256':digest(PLAN),
        'source_sha256':plan['source']['sha256'],
        'page_count':len(pages),
        'source_page_numbers':[x['old'] for x in pages],
        'current_page_ids':[x['page'] for x in pages],
        'key_lengths':lengths,
        'pip_first20':pips[:20],
        'configuration_counts':configs,
        'total_configurations':sum(configs.values()),
        'positive_controls':positive_controls(keyset),
    }


def scan(pages,keyset,flats,include_details=False):
    best=None; count=0; pass_count=0; details=[]; by_branch={}
    for page,flat in zip(pages,flats):
        page_best=None; page_admissible=0; page_hits=0
        for name,key,offset,mode in configurations(page,keyset):
            value=screen(flat,page['singletons'],key,offset,mode)
            if value is None: continue
            count+=1; page_admissible+=1
            if value>1.3: pass_count+=1; page_hits+=1
            candidate=(value,page['page'],name,offset,mode)
            if best is None or candidate>best: best=candidate
            if page_best is None or candidate>page_best: page_best=candidate
            prev=by_branch.get(name)
            if prev is None or candidate>prev: by_branch[name]=candidate
        if include_details:
            details.append({'page':page['page'],'source_page':page['old'],
                            'admissible':page_admissible,'above_1_3':page_hits,
                            'best':format_candidate(page_best)})
    return {'max':best,'admissible':count,'above_1_3':pass_count,
            'page_details':details,'branch_max':by_branch}


def format_candidate(candidate):
    if candidate is None: return None
    score,page,name,offset,mode=candidate
    return {'normalized_ioc':round(score,9),'page':page,'key':name,'offset':offset,'mode':mode}


def run(plan,pages,keyset,gate_report):
    observed=scan(pages,keyset,[p['flat'] for p in pages],True)
    rng=random.Random(20261023)
    controls=[]
    for trial in range(199):
        flats=[]
        for page in pages:
            flat=page['flat'].copy(); rng.shuffle(flat); flats.append(flat)
        null=scan(pages,keyset,flats)
        controls.append({'trial':trial+1,'max_normalized_ioc':None if null['max'] is None else round(null['max'][0],9),
                         'admissible':null['admissible'],'above_1_3':null['above_1_3']})
    obs_score=observed['max'][0] if observed['max'] else None
    return {
        'plan_sha256':digest(PLAN),
        'gate':gate_report,
        'observed':{
            'global_best':format_candidate(observed['max']),
            'admissible':observed['admissible'],
            'above_1_3':observed['above_1_3'],
            'page_details':observed['page_details'],
            'branch_max':{name:format_candidate(x) for name,x in observed['branch_max'].items()},
        },
        'controls':controls,
        'controls_at_least_observed':None if obs_score is None else sum(x['max_normalized_ioc'] is not None and x['max_normalized_ioc']>=round(obs_score,9) for x in controls),
    }


def save_or_check(path,obj,check):
    encoded=(json.dumps(obj,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
    if check:
        assert path.read_bytes()==encoded, f'{path.name} mismatch'
    else:
        path.write_bytes(encoded)
    print(('Checked ' if check else 'Wrote ')+str(path))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--gate',action='store_true',help='Run source-input and planted-message checks only')
    parser.add_argument('--run',action='store_true',help='Scan manuscript and 199 whole-search controls')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    if not args.gate and not args.run: parser.error('choose --gate or --run')
    plan=json.loads(PLAN.read_text(encoding='utf-8'))
    pages,keyset,gate_report=gate(plan)
    if args.gate:
        save_or_check(HERE/'gate.json',gate_report,args.check)
    if args.run:
        assert (HERE/'gate.json').read_bytes()==(json.dumps(gate_report,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
        save_or_check(HERE/'results.json',run(plan,pages,keyset,gate_report),args.check)


if __name__=='__main__': main()
