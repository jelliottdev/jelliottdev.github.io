"""Post-observation LP2-only readout of the already specified shared null."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from run import candidates,load,np_score_page

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def build():
    spec=json.loads((HERE/"diagnostic-plan.json").read_text(encoding="utf-8"))
    assert spec["source_results_sha256"]==sha(HERE/"results.json")
    plan,pages=load();rows=candidates(plan)
    original=json.loads((HERE/"results.json").read_text(encoding="utf-8"))
    lp2=[x for x in original["sweep"] if x["page"].startswith("lp2")]
    observed_max=max(x["ioc"] for x in lp2);observed_hits=sum(x["gate"] for x in lp2)
    rng=np.random.default_rng(plan["null"]["seed"])
    null=[]
    for t in range(plan["null"]["trials"]):
        maximum=0.0;hits=0
        for pg in pages:
            perm=rng.permutation(pg["indices"])
            if pg["site_page"].startswith("lp1") or len(perm)<20:continue
            vals=np_score_page(perm,rows)
            maximum=max(maximum,max(vals));hits+=sum(x>1.25 for x in vals)
        null.append({"trial":t,"max_ioc":round(maximum,10),"gate_hits":hits})
    return {"schema":"wulfic-p08-lp2-posthoc-diagnostic-v1","diagnostic_plan_sha256":sha(HERE/"diagnostic-plan.json"),"observed_lp2_case_count":len(lp2),"observed_lp2_max_ioc":observed_max,"observed_lp2_gate_hits":observed_hits,"null":null,"summary":{"null_max_at_least_observed":sum(x["max_ioc"]>=observed_max for x in null),"null_hits_at_least_observed":sum(x["gate_hits"]>=observed_hits for x in null),"null_gate_hit_range":[min(x["gate_hits"] for x in null),max(x["gate_hits"] for x in null)]}}

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--check",action="store_true");args=ap.parse_args()
    value=build();dest=HERE/"diagnostic-results.json"
    if args.check:
        assert json.loads(dest.read_text(encoding="utf-8"))==value
        print("PASS LP2-only diagnostic")
    else:
        dest.write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8",newline="\n")
        print(value["summary"])
