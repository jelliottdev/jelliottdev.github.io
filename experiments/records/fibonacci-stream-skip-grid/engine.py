"""Load bundled source without running its CLI or accessing manuscript pages."""
import ast
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LP = HERE / 'source/liber-primus'
sys.path[:0] = [str(LP/'analysis/campaign18_skip/armada'),
               str(LP/'analysis/campaign18_skip'), str(LP/'analysis'), str(LP/'src')]
import numeric_skip as numeric
import skipdecode as encoder
import sweep


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf8',newline='\n')


def compact(path, value):
    path.write_text(json.dumps(value,separators=(',',':'))+'\n',encoding='utf8',newline='\n')


def keys():
    return {(a,b): numeric.ks_fibonacci(a,b,1176) for a in range(29) for b in range(29)}


def text(indices):
    return encoder.idx_to_trans(indices)


def terminal_observer():
    # Only expose the original function's final list; all transitions/order unchanged.
    node=next(n for n in ast.parse(Path(sweep.__file__).read_text(encoding='utf8')).body
              if isinstance(n,ast.FunctionDef) and n.name=='beam')
    source=ast.unparse(node)
    assert 'return list(best[3])' in source
    source=source.replace('return list(best[3])','return beams')
    env=dict(sweep.__dict__)
    exec(compile(source,'<return-only-source-observer>','exec'),env)
    return env['beam']


def source_ordinal(a,b,sign,atbash,page_ordinal,offset):
    # numeric_skip: catalog seed order, sign, Atbash, page, then offset.
    return (((((a*29+b)*2+(0 if sign==-1 else 1))*2+atbash)*55+page_ordinal)*5+offset)
