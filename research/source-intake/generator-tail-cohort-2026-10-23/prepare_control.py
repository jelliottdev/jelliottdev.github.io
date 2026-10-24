"""Bundle exact pinned source; run once during preparation, not needed to replay."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT.parent/'source-cache/dukotah-cicada3301'
OUT=ROOT/'experiments/records/r28-c-generator-port-controls'
(OUT/'source').mkdir(parents=True,exist_ok=True)
mapping={'grind28.c':'liber-primus/analysis/round28/L4/grind28.c','gen28.py':'liber-primus/analysis/round28/L4/gen28.py','gen_py27.py':'liber-primus/analysis/round19/G3/gen_py27.py','vectors.json':'liber-primus/analysis/round27/P0-spec/vectors.json','LICENSE':'LICENSE'}
rows=[]
for name,path in mapping.items():
    raw=(SRC/path).read_bytes(); (OUT/'source'/name).write_bytes(raw)
    rows.append({'path':'source/'+name,'upstream_path':path,'sha256':hashlib.sha256(raw).hexdigest()})
(OUT/'source-manifest.json').write_text(json.dumps({'commit':'f08b20b632d91209ddbaa747e8e2f23df0c78ba1','files':rows},indent=2)+'\n')
