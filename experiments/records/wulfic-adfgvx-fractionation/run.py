"""Bounded replay of Wulfic's archived fractionation grid and a separate exact inverse."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
# Source ordering is deliberately specified rather than inferred from code points.
RUNE_TO_IDX = dict(zip([0x16A0,0x16A2,0x16A6,0x16A9,0x16B1,0x16B3,0x16B7,0x16B9,0x16BB,0x16BE,0x16C1,0x16C4,0x16C7,0x16C8,0x16C9,0x16CB,0x16CF,0x16D2,0x16D6,0x16D7,0x16DA,0x16DD,0x16DF,0x16DE,0x16AA,0x16AB,0x16A3,0x16E1,0x16E0],range(29)))
IDX_TO = ['F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S','T','B','E','M','L','NG','OE','D','A','AE','Y','IO','EA']
PAIRS = {'TH':2,'OE':22,'EA':28,'IO':27,'NG':21,'AE':25,'EO':12}
LP = set('THE AND FOR ARE NOT YOU ALL THIS THAT WITH HAVE FROM SELF TRUTH SEEK WITHIN SACRED HOLY WISDOM PATH BEING WAY EACH KNOW FOLLOW COMMAND LAW INSTRUCTION WELCOME PILGRIM DIVINITY PRIMES ENCRYPT END EMERGE FIND WILL ONE YOUR EVERY DUTY DEEP ABOVE SAME OTHER SONG'.split())
SEPARATORS = set('-. \n\r\t\u2022/')

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def gp(text):
    out=[]; i=0; text=text.upper(); single={s:j for j,s in enumerate(IDX_TO)}
    while i<len(text):
        if text[i:i+2] in PAIRS: out.append(PAIRS[text[i:i+2]]); i+=2
        elif text[i] in single: out.append(single[text[i]]); i+=1
        else: i+=1
    return out
def parse(raw):
    words=[]; cur=[]
    for ch in raw:
        code=ord(ch)
        if code in RUNE_TO_IDX: cur.append(RUNE_TO_IDX[code])
        elif ch in SEPARATORS and cur: words.append(cur); cur=[]
    if cur: words.append(cur)
    return [x for w in words for x in w], [len(w) for w in words]
def table(key):
    alpha=list(dict.fromkeys(key + list(range(29))))
    assert len(alpha)==29
    inv={symbol:divmod(i,5) for i,symbol in enumerate(alpha)}
    return alpha,inv
def fractionate(seq,inv): return [v for s in seq for v in inv[s]]
def defractionate(seq,alpha):
    out=[]
    for r,c in zip(seq[::2],seq[1::2]):
        k=r*5+c
        out.append(alpha[k] if 0<=r<6 and 0<=c<5 and k<29 else -1)
    return out
def transpose(seq,width): return [seq[i] for c in range(width) for i in range(c,len(seq),width)]
def source_inverse(seq,width):
    # Archived source allocates ceil(n/width) to every column, truncating at overrun.
    n=len(seq); rows=(n+width-1)//width; cols={}; pos=0
    for c in range(width):
        cols[c]=seq[pos:pos+rows]; pos+=rows
        if pos>n:
            cols[c]=cols[c][:n-pos+rows]
            break
    return [cols[c][r] for r in range(rows) for c in range(width) if c in cols and r<len(cols[c])]
def exact_inverse(seq,width):
    n=len(seq); full=n//width; extra=n%width; pos=0; cols=[]
    for c in range(width):
        z=full+(c<extra); cols.append(seq[pos:pos+z]); pos+=z
    assert pos==n
    return [cols[c][r] for r in range(full+bool(extra)) for c in range(width) if r<len(cols[c])]
def score(seq,sizes):
    pos=0; value=0
    for z in sizes:
        w=''.join(IDX_TO[x] for x in seq[pos:pos+z] if 0<=x<29); pos+=z
        if w in LP: value+=len(w)*4
        elif len(w)>=3 and any(t in w for t in LP if len(t)>=3): value+=4
    return value
def ioc(seq):
    n=len(seq); c=Counter(seq)
    return sum(x*(x-1) for x in c.values())/(n*(n-1)) if n>1 else 0
def measurements(seq,sizes):
    return {'score':score(seq,sizes),'raw_ioc':ioc(seq),'invalid':seq.count(-1),'output_sha256':hashlib.sha256(bytes(x+1 for x in seq)).hexdigest()}
def split_point(label,n):
    return {'n':n,'n-5':n-5,'n+5':n+5,'n//2':n//2,'2*n//3':2*n//3}[label]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--check',action='store_true'); a=ap.parse_args()
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    inputs=[]; rows=[]; controls=[]
    for page in plan['targets']:
        p=ROOT/'data'/'pages'/f'{page}.json'; dat=json.loads(p.read_text(encoding='utf-8'))
        flat,sizes=parse(dat['raw']); assert len(flat)==dat['rune_count']
        inputs.append({'page':page,'site_json_sha256':digest(p),'runes':len(flat),'words':len(sizes),'source_global_page':int(page[-2:])+17})
        n=len(flat)
        for keyword in plan['keywords']:
            alpha,inv=table(gp(keyword)); coords=fractionate(flat,inv)
            assert len(coords)==2*n
            for label,pt in [(t,split_point(t,n)) for t in plan['source_named_routes']['split_points']]:
                pairs=list(zip(coords[:pt],coords[pt:][:pt])); plain=defractionate([v for pair in pairs for v in pair],alpha)
                if len(plain)!=n: rows.append({'page':page,'key':keyword,'route':'split:'+label,'status':'source-skipped','output_length':len(plain)}); continue
                m=measurements(plain,sizes); rows.append({'page':page,'key':keyword,'route':'split:'+label,'status':'scored',**m,'source_gate':m['score']>20 or m['raw_ioc']>1.3})
            for width in plan['source_named_routes']['columnar_widths']:
                src=defractionate(source_inverse(coords,width)[:2*n],alpha)[:n]
                fix=defractionate(exact_inverse(coords,width)[:2*n],alpha)[:n]
                for route,plain in [(f'source-column:{width}',src),(f'exact-column:{width}',fix)]:
                    if len(plain)!=n: rows.append({'page':page,'key':keyword,'route':route,'status':'source-skipped','output_length':len(plain)}); continue
                    m=measurements(plain,sizes); rows.append({'page':page,'key':keyword,'route':route,'status':'scored',**m,'source_gate':m['score']>20 or m['raw_ioc']>1.3})
                # Deterministic planted full-message round trip at the actual target length.
                message=[(i*7+3)%29 for i in range(n)]; encoded=transpose(fractionate(message,inv),width)
                controls.append({'page':page,'key':keyword,'width':width,'exact_roundtrip':defractionate(exact_inverse(encoded,width),alpha)==message,'source_roundtrip':defractionate(source_inverse(encoded,width),alpha)==message})
            direct=defractionate(coords,alpha); m=measurements(direct,sizes)
            rows.append({'page':page,'key':keyword,'route':'direct','status':'scored',**m,'source_gate':m['score']>20 or m['raw_ioc']>1.3})
            for mode in ('sub','add'):
                key=gp(keyword); moved=[(v+(-1 if mode=='sub' else 1)*key[i%len(key)])%(6 if i%2==0 else 5) for i,v in enumerate(coords)]
                plain=defractionate(moved,alpha); m=measurements(plain,sizes)
                rows.append({'page':page,'key':keyword,'route':'coordinate:'+mode,'status':'scored',**m,'source_gate':m['score']>20 or m['raw_ioc']>1.3})
    assert len(rows)==(5+14+1+2)*14*6
    assert all(x['exact_roundtrip'] for x in controls)
    summary={'schema':'liberpedia-wulfic-fractionation-v1','plan_sha256':digest(HERE/'plan.json'),'inputs':inputs,'source_named_rows':sum(x['route'].split(':')[0]!='exact-column' for x in rows),'source_scored_rows':sum(x['route'].split(':')[0]!='exact-column' and x['status']=='scored' for x in rows),'source_gate_rows':sum(x['route'].split(':')[0]!='exact-column' and x['status']=='scored' and x['source_gate'] for x in rows),'exact_variant_rows':sum(x['route'].split(':')[0]=='exact-column' for x in rows),'exact_variant_gate_rows':sum(x['route'].split(':')[0]=='exact-column' and x['status']=='scored' and x['source_gate'] for x in rows),'planted_roundtrips':len(controls),'exact_roundtrip_failures':sum(not x['exact_roundtrip'] for x in controls),'source_roundtrip_failures':sum(not x['source_roundtrip'] for x in controls),'source_gate':'score > 20 or raw IoC > 1.3 (not a decryption criterion)'}
    for name,obj in [('inputs.json',inputs),('results.json',summary),('controls.json',controls)]:
        payload=json.dumps(obj,indent=2,ensure_ascii=False)+'\n'; path=HERE/name
        if a.check: assert path.read_text(encoding='utf-8')==payload,name
        else: path.write_text(payload,encoding='utf-8',newline='\n')
    payload=''.join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for x in rows)
    if a.check: assert (HERE/'cases.jsonl').read_text(encoding='utf-8')==payload
    else: (HERE/'cases.jsonl').write_text(payload,encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('inputs','source_gate')},indent=2))
if __name__=='__main__': main()
