"""Standalone replay of the three pinned Campaign VII grid-as-key scripts."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = ('F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X',
          'S','T','B','E','M','L','NG','OE','D','A','AE','Y','IA','EA')
ABC = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


def load():
    inp = json.loads((HERE / 'inputs.json').read_text(encoding='utf-8'))
    raw = (HERE / 'input-indices.bin').read_bytes()
    lens = json.loads((HERE / 'page-lengths.json').read_text(encoding='utf-8'))
    assert len(raw) == sum(lens['lengths']) == 12956
    starts = [0]
    for n in lens['lengths']:
        starts.append(starts[-1]+n)
    targets = [(f'p{i:02d}', raw[starts[i]:starts[i+1]]) for i in range(55)]
    targets.append(('WHOLE', raw))
    return inp, targets


def streams(inp):
    p49,p50,p51 = (inp['archived_pages'][p] for p in ('p49','p50','p51'))
    a = {
        'p49':p49,'p50':p50,'p51':p51,
        'p49+50+51':p49+p50+p51,'p49+51':p49+p51,
        'p51+50+49_rev':(p49+p50+p51)[::-1],
        'xor_49_51':[a^b for a,b in zip(p49,p51)],
        'xor_49_50':[a^b for a,b in zip(p49,p50)],
        'xor_50_51':[a^b for a,b in zip(p50,p51)],
    }
    b, base_report = {}, {}
    vals = {c:i for i,c in enumerate(ABC)}
    for base in (59,60,62,64):
        streams_by_page = {p:[vals[t[0]]*base+vals[t[1]] for t in inp['raw_tokens'][p]]
                           for p in ('p49','p50','p51')}
        whole = sum(streams_by_page.values(), [])
        base_report[str(base)] = {'all_in_0_255':all(0<=v<=255 for v in whole),
                                  'min':min(whole),'max':max(whole)}
        b.update({f'b{base}_p49':streams_by_page['p49'],
                  f'b{base}_p51':streams_by_page['p51'],
                  f'b{base}_all':whole,
                  f'b{base}_49+51':streams_by_page['p49']+streams_by_page['p51']})
    token = p49+p50+p51
    onions = {k:list(bytes.fromhex(v)) for k,v in inp['onion_hex'].items()}
    assert all(len(x)==256 for x in onions.values())
    c={}
    for name, ob in onions.items():
        c[f'token^{name}']=[x^y for x,y in zip(token,ob)]
        c[name]=ob
    o234=[x^y^z for x,y,z in zip(onions['onion2'],onions['onion3'],onions['onion4'])]
    c['onion2^3^4']=o234
    c['token^onion2^3^4']=[x^y for x,y in zip(token,o234)]
    return {'A2_tokenpad':a,'A2_altbase':b,'B2_onion_xor':c}, base_report


def decode(cipher, key, sign, atbash, interrupt):
    out=[]; j=0; m=len(key)
    for c in cipher:
        if interrupt and c==0:
            out.append(0)
        else:
            out.append(((28-c if atbash else c)+sign*key[j%m])%29)
            j+=1
    return out


def text(indices):
    return ''.join(LABELS[v] for v in indices)


def model():
    path=HERE/'source/liber-primus/data/english_quadgrams.txt'
    counts={}; total=0
    for line in path.read_text(encoding='ascii').splitlines():
        q,c=line.split(); n=int(c); counts[q]=n; total+=n
    logtotal=math.log10(total)
    table={q:math.log10(v)-logtotal for q,v in counts.items()}
    return table, math.log10(0.01)-logtotal


def score(txt, table, floor):
    if len(txt)<4: return -999.0
    return sum(table.get(txt[i:i+4],floor) for i in range(len(txt)-3))/(len(txt)-3)


def controls(key, table, floor):
    phrase='THEPRIMESARESACREDANDTHETOTIENTFUNCTIONISSACREDALLTHINGSSHOULDBEENCRYPTED'
    # Source GP transliteration parser chooses multi-character runes longest-first.
    options=sorted(enumerate(LABELS), key=lambda p:-len(p[1]))
    base=[]; pos=0
    while pos<len(phrase):
        idx,label=next((i,t) for i,t in options if phrase.startswith(t,pos))
        base.append(idx); pos+=len(label)
    plain=(base*((120//len(base))+1))[:120]
    rows=[]
    for sign in (-1,1):
        for atbash in (False,True):
            for interrupt in (False,True):
                c=[]; expected=[]; j=0; forced_f=0
                for p in plain:
                    if interrupt and p==0:
                        c.append(0);expected.append(0);continue
                    transformed=(p-sign*key[j%len(key)])%29
                    v=(28-transformed if atbash else transformed)
                    if interrupt and v==0:
                        c.append(0); expected.append(0)
                        if p!=0: forced_f+=1
                    else:
                        c.append(v); expected.append(p); j+=1
                recovered=decode(c,key,sign,atbash,interrupt)
                assert recovered==expected
                sc=score(text(recovered),table,floor)
                rows.append({'sign':sign,'atbash':atbash,'interrupt':interrupt,
                             'length':len(recovered),'exact':True,'score':round(sc,6),
                             'pass_threshold':sc>-5.2,'f_runes':c.count(0),
                             'forced_literal_F':forced_f,
                             'unchanged_known_runes':120-forced_f,
                             'ciphertext_sha256':hashlib.sha256(bytes(c)).hexdigest(),
                             'constructed_plaintext_sha256':hashlib.sha256(bytes(expected)).hexdigest()})
                assert sc>-5.2
    return rows


def forensic(seq):
    freq=Counter(seq); n=len(seq)
    return {'entropy_bits':round(-sum((c/n)*math.log2(c/n) for c in freq.values()),3),
            'printable_ratio':round(sum(32<=v<=126 for v in seq)/n,3),
            'head_hex':bytes(seq[:8]).hex(),'distinct':len(freq)}


def run(check=False):
    inp,targets=load(); groups,base_report=streams(inp)
    table,floor=model()
    token=sum((inp['archived_pages'][p] for p in ('p49','p50','p51')),[])
    plants=controls(token,table,floor)
    assert [x^x for x in token]==[0]*256
    output={'schema':'liberpedia-campaign7-grid-key-source-replay-result-v1',
            'controls':plants,'base_report':base_report,'groups':{},
            'case_count':0}
    for group, keys in groups.items():
        hits=[]; best=None; bykey={}; cases=0; digest=hashlib.sha256(); plain_digest=hashlib.sha256()
        for name,rawkey in keys.items():
            key=[v%29 for v in rawkey]
            for target,cipher in targets:
                for sign in (-1,1):
                    for atbash in (False,True):
                        for interrupt in (False,True):
                            p=decode(cipher,key,sign,atbash,interrupt)
                            pt=text(p)
                            s=score(pt,table,floor)
                            method=f'sign{sign:+d} atb{int(atbash)} '+('INT' if interrupt else 'noint')
                            rec={'key':name,'target':target,'method':method,
                                 'plaintext':pt[:80],'score':s}
                            cases+=1
                            digest.update(f'{name}\t{target}\t{method}\t{s:.6f}\n'.encode('ascii'))
                            plain_digest.update(f'{name}\t{target}\t{method}\t{pt}\n'.encode('utf-8'))
                            if best is None or s>best['score']: best=rec
                            if name not in bykey or s>bykey[name]: bykey[name]=s
                            if s>-5.2: hits.append(rec)
        assert cases==len(keys)*56*8
        output['case_count']+=cases
        output['groups'][group]={'case_count':cases,'score_digest_sha256':digest.hexdigest(),
                                 'plaintext_digest_sha256':plain_digest.hexdigest(),
                                 'best':best,'n_hits':len(hits),
                                 'hits':sorted(hits,key=lambda x:-x['score'])[:20],
                                 'per_key_best':{k:round(v,3) for k,v in bykey.items()}}
    b2=groups['B2_onion_xor']
    output['xor_forensics']={'token_pad':forensic(token),
                             **{k:forensic(b2[k]) for k in ('token^onion2','token^onion3','token^onion4','onion2^3^4')}}
    assert output['case_count']==14784
    content=json.dumps(output,indent=2,ensure_ascii=False)+'\n'
    path=HERE/'results.json'
    if check:
        assert path.read_text(encoding='utf-8')==content
        print('PASS: read-only full-grid replay matches saved results')
    else:
        path.write_text(content,encoding='utf-8',newline='\n')
        print(json.dumps({k:(v['case_count'],round(v['best']['score'],3),v['n_hits']) for k,v in output['groups'].items()}))


if __name__=='__main__':
    arg=argparse.ArgumentParser();arg.add_argument('--check',action='store_true')
    run(arg.parse_args().check)
