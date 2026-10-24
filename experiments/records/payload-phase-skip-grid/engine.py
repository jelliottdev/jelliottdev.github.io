"""Load bundled source; never run source main or manuscript calls on import."""
import ast,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;LP=HERE/'source/liber-primus'
sys.path[:0]=[str(LP/'analysis/campaign18_skip/armada2'),str(LP/'analysis/campaign18_skip'),str(LP/'analysis'),str(LP/'src')]
import numeric2_skip as numeric
import skipdecode as encoder
import sweep
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def keys():
 raw=numeric.load_payload_bytes()
 return {name:[int(v)%29 for v in values]*7 for name,values in raw.items()}
def validate(plan):
 for item in plan['inputs']:assert sha(HERE/item['path'])==item['sha256'],item['path']
 assert keys()==json.loads((HERE/'streams.json').read_text())
def terminal_observer():
 node=next(n for n in ast.parse(Path(sweep.__file__).read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='beam')
 text=ast.unparse(node);assert text.count('return list(best[3])')==1
 env=dict(sweep.__dict__);exec(text.replace('return list(best[3])','return beams'),env);return env['beam']
