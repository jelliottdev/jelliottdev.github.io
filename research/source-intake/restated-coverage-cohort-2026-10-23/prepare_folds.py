import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT.parent/'source-cache/dukotah-cicada3301'
OUT=ROOT/'experiments/records/r21-fold-tail-scope-controls'
files=['liber-primus/analysis/round19/I1/driftbeam.py','liber-primus/analysis/round20/HITFN/hitfn20.py','liber-primus/analysis/round21/L1-seal-realmode-proxy/hitfn21_folds.py','liber-primus/analysis/campaign18_skip/skipdecode.py','liber-primus/src/lp/gematria.py','liber-primus/src/lp/score.py','liber-primus/data/english_quadgrams.txt','LICENSE']
pins=[]
for name in files:
    target=OUT/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);raw=(SRC/name).read_bytes();target.write_bytes(raw)
    pins.append({'path':'source/'+name,'sha256':hashlib.sha256(raw).hexdigest(),'upstream_path':name})
plain=json.loads((ROOT/'experiments/records/c2-extension-generator-controls/fixtures.json').read_text())['cases'][0]['plain']
(OUT/'plain.json').write_text(json.dumps({'origin':'c2-extension-generator-controls/fixtures.json, first case A1_bash seed 3301; plaintext only, no old ciphertext reused','plain_idx':plain},indent=2)+'\n')
(OUT/'source-manifest.json').write_text(json.dumps({'commit':'f08b20b632d91209ddbaa747e8e2f23df0c78ba1','files':pins},indent=2)+'\n')
(OUT/'plan.json').write_text(json.dumps({'length':240,'seeds':[3301,3302,3303],'suppression':[0.0,0.83],'fold_counts':[2,3,4,5,6],'rules':['min','mean','frac_pass'],'beam_width':400,'preset':'exact','sign':-1,'key_symbols':2000,'reference_checks':['unchanged full decode','first 40 indices incremented modulo 29','all indices incremented modulo 29'],'claim':'Measure fold-helper right-tail scope on six known-key plants; no source full audit or no-oracle catch-rate claim.'},indent=2)+'\n')
