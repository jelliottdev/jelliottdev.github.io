"""Bundled source access for numeric2 Part C only."""
import ast
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
LP=HERE/'source/liber-primus'
sys.path[:0]=[str(LP/'analysis/campaign18_skip/armada2'),str(LP/'analysis/campaign18_skip'),str(LP/'analysis'),str(LP/'src')]
import numeric2_skip as source
import skipdecode as encoder
import sweep


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p,value):
    p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf8',newline='\n')


def text(indices):
    return encoder.idx_to_trans(indices)


def assignments():
    rows=[]
    for mode in ['prime','totient','3301xor']:
        for i in range(55):
            key=source.page_seeded_stream(i,1124,mode)
            intercept=key[0]
            slope=(key[1]-key[0])%29
            assert slope and key==[(intercept+slope*j)%29 for j in range(1124)]
            rows.append({'mode':mode,'source_index':i,'page':f'lp2-{i if i<50 else i+1:02d}',
                         'intercept':intercept,'slope':slope,'key_sha256':hashlib.sha256(bytes(key)).hexdigest()})
    return rows


def terminal_observer():
    node=next(n for n in ast.parse(Path(sweep.__file__).read_text(encoding='utf8')).body if isinstance(n,ast.FunctionDef) and n.name=='beam')
    code=ast.unparse(node)
    assert 'return list(best[3])' in code
    env=dict(sweep.__dict__)
    exec(compile(code.replace('return list(best[3])','return beams'),'<return-only-source-observer>','exec'),env)
    return env['beam']
