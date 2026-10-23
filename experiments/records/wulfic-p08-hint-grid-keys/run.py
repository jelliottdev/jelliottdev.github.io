"""Corrected-path replay of Wulfic's finite P08 hint-key scan."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
RUNES="ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load():
    p=json.loads((HERE/"plan.json").read_text(encoding="utf-8"))
    s=json.loads((HERE/"source-pages.json").read_text(encoding="utf-8"))
    assert p["source_page_snapshot_sha256"]==sha(HERE/"source-pages.json")
    return p,s["pages"]

def ioc(vals):
    n=len(vals)
    if n<2:return 0.0
    h=Counter(vals)
    return 29*sum(v*(v-1) for v in h.values())/(n*(n-1))

def decrypt(cipher,key,mode):
    if mode=="sub":return [(c-key[i%len(key)])%29 for i,c in enumerate(cipher)]
    if mode=="add":return [(c+key[i%len(key)])%29 for i,c in enumerate(cipher)]
    return [(key[i%len(key)]-c)%29 for i,c in enumerate(cipher)]

def singleton_positions(raw):
    pos=[]; start=None; length=0; idx=0
    for ch in raw:
        if ch in RUNES:
            if start is None:start=idx
            length+=1;idx+=1
        elif ch in "-. ":
            if length==1:pos.append(start)
            start=None;length=0
    if length==1:pos.append(start)
    return pos

def candidates(plan):
    rows=[]
    for name in plan["source_sweep_keys"]:
        key=plan["source_grid"]["keys"][name]
        for offset in range(len(key)):
            for mode in plan["modes"]:
                rows.append((name,offset,mode,np.array((key[offset:]+key[:offset]),dtype=np.int16)))
    return rows

def np_score_page(cipher, rows):
    n=len(cipher); c=np.asarray(cipher,dtype=np.int16)
    k=np.stack([np.resize(row[3],n) for row in rows])
    modes=np.array([0 if row[2]=="sub" else 1 if row[2]=="add" else 2 for row in rows])[:,None]
    plain=np.where(modes==0,c-k,np.where(modes==1,c+k,k-c))%29
    encoded=(np.arange(len(rows),dtype=np.int32)[:,None]*29+plain).ravel()
    hist=np.bincount(encoded,minlength=len(rows)*29).reshape(len(rows),29)
    return (29*(hist*(hist-1)).sum(axis=1)/(n*(n-1))).tolist()

def evaluate(plan,pages,rows):
    fixed=[]; sweep=[]
    for pg in pages:
        c=pg["indices"]; raw=pg["raw"]
        if len(c)<20:continue
        singles=singleton_positions(raw)
        for name in plan["source_fixed_keys"]:
            key=plan["source_grid"]["keys"][name]
            for mode in plan["modes"]:
                plain=decrypt(c,key,mode)
                score=ioc(plain)
                fixed.append({"page":pg["site_page"],"source_page":pg["source_page"],"key":name,"mode":mode,"ioc":round(score,10),"singleton_ok":all(plain[i] in (10,24) for i in singles),"gate":score>1.3 or (score>1.15 and all(plain[i] in (10,24) for i in singles))})
        scores=np_score_page(c,rows)
        for j,score in enumerate(scores):
            name,offset,mode,_=rows[j]
            sweep.append({"page":pg["site_page"],"source_page":pg["source_page"],"key":name,"offset":offset,"mode":mode,"ioc":round(score,10),"gate":score>1.25})
    return fixed,sweep

def controls(plan):
    rows=[]
    for item in plan["positive_controls"]:
        p=item["indices"]
        for name in plan["source_sweep_keys"]:
            key=plan["source_grid"]["keys"][name]
            for offset in (0,len(key)//2):
                k=key[offset:]+key[:offset]
                for mode in plan["modes"]:
                    if mode=="sub":cipher=[(x+k[i%len(k)])%29 for i,x in enumerate(p)]
                    elif mode=="add":cipher=[(x-k[i%len(k)])%29 for i,x in enumerate(p)]
                    else:cipher=[(k[i%len(k)]-x)%29 for i,x in enumerate(p)]
                    assert decrypt(cipher,k,mode)==p
                    rows.append({"reading":item["id"],"length":len(p),"key":name,"offset":offset,"mode":mode,"ioc":round(ioc(p),10),"source_sweep_gate":ioc(p)>1.25})
    return rows

def null(plan,pages,rows):
    rng=np.random.default_rng(plan["null"]["seed"])
    out=[]
    for trial in range(plan["null"]["trials"]):
        maximum=0.0; hits=0
        for pg in pages:
            c=pg["indices"]
            if len(c)<20:continue
            shuffled=rng.permutation(c)
            scores=np_score_page(shuffled,rows)
            maximum=max(maximum,max(scores));hits+=sum(x>1.25 for x in scores)
        out.append({"trial":trial,"max_ioc":round(maximum,10),"gate_hits":hits})
    return out

def build():
    plan,pages=load();rows=candidates(plan)
    fixed,sweep=evaluate(plan,pages,rows)
    control=controls(plan)
    noise=null(plan,pages,rows)
    return {"schema":"wulfic-p08-grid-keys-results-v1","plan_sha256":sha(HERE/"plan.json"),"source_pages_sha256":sha(HERE/"source-pages.json"),"page_count":len(pages),"lp1_page_count":sum(x["site_page"].startswith("lp1") for x in pages),"lp2_page_count":sum(x["site_page"].startswith("lp2") for x in pages),"fixed":fixed,"sweep":sweep,"positive_controls":control,"null":noise,"summary":{"fixed_case_count":len(fixed),"fixed_gate_hits":sum(x["gate"] for x in fixed),"sweep_case_count":len(sweep),"sweep_gate_hits":sum(x["gate"] for x in sweep),"sweep_best":max(sweep,key=lambda x:x["ioc"]),"positive_control_count":len(control),"positive_control_gate_hits":sum(x["source_sweep_gate"] for x in control),"null_max_at_least_observed":sum(x["max_ioc"]>=max(y["ioc"] for y in sweep) for x in noise),"null_gate_hit_range":[min(x["gate_hits"] for x in noise),max(x["gate_hits"] for x in noise)]}}

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--check",action="store_true");args=ap.parse_args()
    value=build();p=HERE/"results.json"
    if args.check:
        assert json.loads(p.read_text(encoding="utf-8"))==value
        print("PASS source grid replay, controls and full conditional null")
    else:
        p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
        print(value["summary"])
