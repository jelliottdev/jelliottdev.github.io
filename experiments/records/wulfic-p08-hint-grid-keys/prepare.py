"""Freeze exact Wulfic P08 source inputs before evaluating candidate keys."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "source-archives" / "Wulfic-Cicada3301-Liber_Primus"
REV = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
R1 = ["TL","BE","IE","OV","UT","HT","RE","ID","TS","EO","ST","PO","SO","YR"]
R2 = ["SL","BT","II","IY","T4","DG","UQ","IM","NU","44","2I","15","33","9M"]
L = {'A':24,'B':17,'C':5,'D':23,'E':18,'F':0,'G':6,'H':8,'I':10,'J':11,'K':5,'L':20,'M':19,'N':9,'O':3,'P':13,'Q':5,'R':4,'S':15,'T':16,'U':1,'V':1,'W':7,'X':14,'Y':26,'Z':15, **{str(i):i for i in range(10)}}

def obj(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

def main():
    source_bytes = subprocess.check_output(["git","show",f"{REV}:tools/legacy/p08_grid_analysis.py"],cwd=SOURCE)
    pages = []
    for n in range(8,55):
        rel=f"pages/page_{n:02d}/runes.txt"
        b=subprocess.check_output(["git","show",f"{REV}:{rel}"],cwd=SOURCE)
        raw=b.decode("utf-8")
        pages.append({"source_page":n,"site_page": f"lp1-{n:02d}" if n<=16 else f"lp2-{n-17:02d}","git_path":rel,"git_blob":subprocess.check_output(["git","rev-parse",f"{REV}:{rel}"],cwd=SOURCE,text=True).strip(),"sha256":hashlib.sha256(b).hexdigest(),"raw":raw,"indices":[RUNES.index(c) for c in raw if c in RUNES]})
    obj(HERE/"source-pages.json",{"schema":"wulfic-p08-source-pages-v1","revision":REV,"pages":pages})
    r1=[L[c] for pair in R1 for c in pair];r2=[L[c] for pair in R2 for c in pair]
    a=[(y-x)%29 for x,y in zip(r1,r2)];bb=[(x-y)%29 for x,y in zip(r1,r2)]
    keys={"KEY_A_28":a,"KEY_B_28":bb,"KEY_C_sum14":[(a[2*i]+a[2*i+1])%29 for i in range(14)],"KEY_C_d1_14":a[::2],"KEY_C_d2_14":a[1::2],"KEY_R1_raw":r1,"KEY_R2_raw":r2}
    solved=json.loads((ROOT/"data/evidence/known-readings.json").read_text(encoding="utf-8"))
    controls=[]
    for item in solved["controls"]:
        for pg in item["decoded_pages"]:
            vals=pg["rune_indices"]
            if len(vals)>=50:
                controls.append({"id":pg["page"],"indices":vals})
    obj(HERE/"plan.json",{"schema":"wulfic-p08-grid-keys-plan-v1","timing":"retrospective source-grid replay; source hypothesis and published records inspected before this replay","source_revision":REV,"source_script_sha256":hashlib.sha256(source_bytes).hexdigest(),"source_page_snapshot_sha256":hashlib.sha256((HERE/"source-pages.json").read_bytes()).hexdigest(),"known_readings_sha256":hashlib.sha256((ROOT/"data/evidence/known-readings.json").read_bytes()).hexdigest(),"source_grid":{"row1":R1,"row2":R2,"latin_to_gp":L,"keys":keys},"source_page_numbers":[8,54],"source_fixed_keys":list(keys),"source_sweep_keys":["KEY_A_28","KEY_B_28","KEY_C_sum14","KEY_R1_raw","KEY_R2_raw"],"modes":["sub","add","beau"],"offsets":"all 0..key_length-1 for sweep; 0 for fixed","ioc":"29 sum(f(f-1))/(n(n-1))","source_fixed_gate":"IoC>1.3 OR (IoC>1.15 AND all visible singleton words decode to GP I or A)","source_sweep_gate":"IoC>1.25","positive_controls":controls,"null":{"kind":"within-page independent rune-position shuffle, preserving each page's unigram counts and length; same shuffled corpus per trial for all candidate keys","seed":805408,"trials":199,"statistic":"maximum sweep IoC across full source page×key×offset×mode grid and count above source 1.25 gate"},"excluded":"source's bigram substitution, raw-rune P08, Koan running-key and arithmetic descriptions are separate hypotheses; no all-LP2 or all-hint-key claim; original script path resolves tools/pages, so source Git blobs are loaded via corrected path"})
    print("Frozen",len(pages),"source pages and",len(controls),"solved-reading controls")

if __name__=="__main__":main()
