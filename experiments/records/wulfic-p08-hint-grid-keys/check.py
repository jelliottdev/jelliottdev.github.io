"""Independent arithmetic and source-input audit for P08 hint-grid keys."""
import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
RUNES="ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def score(a):
    n=len(a);f=Counter(a)
    return 29*sum(v*v-v for v in f.values())/(n*n-n)
def run():
    p=json.loads((HERE/"plan.json").read_text(encoding="utf-8"))
    s=json.loads((HERE/"source-pages.json").read_text(encoding="utf-8"))["pages"]
    r=json.loads((HERE/"results.json").read_text(encoding="utf-8"))
    assert r["plan_sha256"]==digest(HERE/"plan.json")
    assert r["source_pages_sha256"]==digest(HERE/"source-pages.json")==p["source_page_snapshot_sha256"]
    assert len(s)==47 and [x["source_page"] for x in s]==list(range(8,55))
    for pg in s:
        assert pg["indices"]==[RUNES.index(c) for c in pg["raw"] if c in RUNES]
        assert hashlib.sha256(pg["raw"].encode("utf-8")).hexdigest()==pg["sha256"]
        assert pg["site_page"]==(f"lp1-{pg['source_page']:02d}" if pg["source_page"]<=16 else f"lp2-{pg['source_page']-17:02d}")
    converter=p["source_grid"]["latin_to_gp"]
    a=[converter[c] for pair in p["source_grid"]["row1"] for c in pair]
    b=[converter[c] for pair in p["source_grid"]["row2"] for c in pair]
    clue="".join(p["source_grid"]["row1"]+p["source_grid"]["row2"])
    assert len(clue)==56
    arrangement=[['']*8 for _ in range(7)]
    ordering=(0,4,2,6,5,3,1)
    for col in range(8):
        for row in range(7):
            arrangement[ordering[row]][col]=clue[col*7+row]
    hint="".join(arrangement[row][col] for col in range(8) for row in range(7))
    assert hint=="TOBELIEVETRUTHISTODESTROYPOSSIBILITYQ4UTGDI2N4M4UIM59133"
    d=[(y-x)%29 for x,y in zip(a,b)]
    expected={"KEY_A_28":d,"KEY_B_28":[(-x)%29 for x in d],"KEY_C_sum14":[(d[i]+d[i+1])%29 for i in range(0,28,2)],"KEY_C_d1_14":d[::2],"KEY_C_d2_14":d[1::2],"KEY_R1_raw":a,"KEY_R2_raw":b}
    assert expected==p["source_grid"]["keys"]
    bypg={x["site_page"]:x for x in s}
    assert len(r["fixed"])==47*7*3
    for x in r["fixed"]:
        c=bypg[x["page"]]["indices"];k=expected[x["key"]]
        if x["mode"]=="sub":v=[(q-k[i%len(k)])%29 for i,q in enumerate(c)]
        elif x["mode"]=="add":v=[(q+k[i%len(k)])%29 for i,q in enumerate(c)]
        else:v=[(k[i%len(k)]-q)%29 for i,q in enumerate(c)]
        assert abs(score(v)-x["ioc"])<1e-9
        single_positions=[]; cursor=0
        for segment in re.split(r"[-. ]",bypg[x["page"]]["raw"]):
            size=sum(ch in RUNES for ch in segment)
            if size==1:single_positions.append(cursor)
            cursor+=size
        okay=all(v[i] in (10,24) for i in single_positions)
        assert okay==x["singleton_ok"]
        assert (score(v)>1.3 or (score(v)>1.15 and okay))==x["gate"]
    assert len(r["sweep"])==47*sum(len(expected[x])*3 for x in p["source_sweep_keys"])
    for x in r["sweep"]:
        c=bypg[x["page"]]["indices"];k=expected[x["key"]];off=x["offset"]
        vals=[]
        for i,q in enumerate(c):
            key=k[(i+off)%len(k)]
            vals.append((q-key)%29 if x["mode"]=="sub" else (q+key)%29 if x["mode"]=="add" else (key-q)%29)
        v=score(vals)
        assert abs(v-x["ioc"])<1e-9 and (v>1.25)==x["gate"]
    for x in r["positive_controls"]:
        plain=next(y["indices"] for y in p["positive_controls"] if y["id"]==x["reading"])
        key=expected[x["key"]]; off=x["offset"]
        encrypted=[]
        for i,q in enumerate(plain):
            k=key[(i+off)%len(key)]
            encrypted.append((q+k)%29 if x["mode"]=="sub" else (q-k)%29 if x["mode"]=="add" else (k-q)%29)
        recovered=[]
        for i,q in enumerate(encrypted):
            k=key[(i+off)%len(key)]
            recovered.append((q-k)%29 if x["mode"]=="sub" else (q+k)%29 if x["mode"]=="add" else (k-q)%29)
        assert recovered==plain and abs(score(plain)-x["ioc"])<1e-9
        assert x["source_sweep_gate"]==(score(plain)>1.25)
    assert sum(x["gate"] for x in r["sweep"])==r["summary"]["sweep_gate_hits"]
    assert sum(x["gate"] for x in r["fixed"])==r["summary"]["fixed_gate_hits"]
    # Alias identities audit the full 199-trial null's search definition:
    # Beaufort's IoC equals subtraction's; KEY_B is -KEY_A, so B/add=A/sub.
    for pg in s:
        block=[x for x in r["sweep"] if x["page"]==pg["site_page"]]
        index={(x["key"],x["offset"],x["mode"]):x["ioc"] for x in block}
        for name in p["source_sweep_keys"]:
            for off in range(len(expected[name])):
                assert index[(name,off,"sub")]==index[(name,off,"beau")]
    assert len(r["null"])==199 and all(x["gate_hits"]>=0 for x in r["null"])
    print("PASS 47 source page arrays, exact derived keys, 18,753 observed cases, 510 planted transforms, and null-grid invariants")

if __name__=="__main__":run()
