"""Independent output/control audit; --checkout also checks the pinned original source."""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RUNES=[0x16A0,0x16A2,0x16A6,0x16A9,0x16B1,0x16B3,0x16B7,0x16B9,0x16BB,0x16BE,0x16C1,0x16C4,0x16C7,0x16C8,0x16C9,0x16CB,0x16CF,0x16D2,0x16D6,0x16D7,0x16DA,0x16DD,0x16DF,0x16DE,0x16AA,0x16AB,0x16A3,0x16E1,0x16E0]
LOOKUP={x:i for i,x in enumerate(RUNES)}
SEPS=set('-. \n\r\t\u2022/')

def parse(text):
    words=[]; word=[]
    for c in text:
        if ord(c) in LOOKUP: word.append(LOOKUP[ord(c)])
        elif c in SEPS and word: words.append(word); word=[]
    if word: words.append(word)
    return sum(words,[]),[len(w) for w in words]

def inv_exact(seq,width):
    n=len(seq); cut=0; columns=[]
    for col in range(width):
        z=len(range(col,n,width)); columns.append(seq[cut:cut+z]); cut+=z
    assert cut==n
    return [columns[c][r] for r in range((n+width-1)//width) for c in range(width) if r<len(columns[c])]

def digest(seq): return hashlib.sha256(bytes(x+1 for x in seq)).hexdigest()

def verify_source(checkout, plan, inputs, rows):
    checkout=Path(checkout)
    def blob(path):
        return subprocess.check_output(['git','rev-parse',f"{plan['source_revision']}:{path}"],cwd=checkout,text=True).strip()
    assert blob(plan['source_file'])==plan['source_git_blob']
    source=subprocess.check_output(['git','show',f"{plan['source_revision']}:{plan['source_file']}"],cwd=checkout,text=True,encoding='utf-8')
    tree=ast.parse(source)
    names={'load_runes','ioc','text_to_gp','make_polybius_table','fractionate','defractionate','columnar_transpose','reverse_columnar','score_plain'}
    funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    scope={'Counter':Counter,'RUNE_TO_IDX':{chr(x):i for i,x in enumerate(RUNES)},'IDX_TO':['F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S','T','B','E','M','L','NG','OE','D','A','AE','Y','IO','EA'],'SEPARATORS':SEPS}
    exec(compile(ast.Module(body=funcs,type_ignores=[]),'<pinned-source-functions>','exec'),scope)
    by={(r['page'],r['key'],r['route']):r for r in rows}
    verified=0
    def verify_row(page,key,route,plain,sizes):
        nonlocal verified
        r=by[(page,key,route)]
        assert r['status']=='scored' and r['output_sha256']==digest(plain)
        assert r['invalid']==plain.count(-1)
        assert r['score']==scope['score_plain'](plain,sizes)[0]
        assert abs(r['raw_ioc']-scope['ioc'](plain))<1e-15
        assert r['source_gate']==(r['score']>20 or r['raw_ioc']>1.3)
        verified+=1
    for item in inputs:
        page=item['page']; number=int(page[-2:]); raw=subprocess.check_output(['git','show',f"{plan['source_revision']}:pages/page_{number+17}/runes.txt"],cwd=checkout).decode('utf-8')
        site=json.loads((ROOT/'data'/'pages'/f'{page}.json').read_text(encoding='utf-8'))['raw']
        assert parse(raw)==parse(site)
        flat,sizes=parse(raw)
        for key in plan['keywords']:
            keycode=scope['text_to_gp'](key)
            table,inv,alpha=scope['make_polybius_table'](keycode)
            coords=scope['fractionate'](flat,inv)
            assert len(coords)==2*len(flat)
            verify_row(page,key,'direct',scope['defractionate'](coords,table),sizes)
            for mode in ('sub','add'):
                z=[(v+(-1 if mode=='sub' else 1)*keycode[i%len(keycode)])%(6 if i%2==0 else 5) for i,v in enumerate(coords)]
                verify_row(page,key,'coordinate:'+mode,scope['defractionate'](z,table),sizes)
            for label,pt in [('n',len(flat)),('n-5',len(flat)-5),('n+5',len(flat)+5),('n//2',len(flat)//2),('2*n//3',2*len(flat)//3)]:
                pairs=list(zip(coords[:pt],coords[pt:][:pt]))
                plain=[table[r][c] if 0<=r<6 and 0<=c<5 and table[r][c] is not None else -1 for r,c in pairs]
                row=by[(page,key,'split:'+label)]
                if len(plain)!=len(flat):
                    assert row['status']=='source-skipped' and row['output_length']==len(plain)
                else: verify_row(page,key,'split:'+label,plain,sizes)
            for width in plan['source_named_routes']['columnar_widths']:
                src=scope['reverse_columnar'](coords,width)
                # Original source and independently transcribed rule agree on all targeted cells.
                n=len(coords); rows=(n+width-1)//width; cols={}; pos=0
                for c in range(width):
                    cols[c]=coords[pos:pos+rows]; pos+=rows
                    if pos>n: cols[c]=cols[c][:n-pos+rows]; break
                alt=[cols[c][r] for r in range(rows) for c in range(width) if c in cols and r<len(cols[c])]
                assert src==alt
                assert scope['columnar_transpose'](inv_exact(coords,width),width)==coords
                verify_row(page,key,f'source-column:{width}',scope['defractionate'](src,table),sizes)
                verify_row(page,key,f'exact-column:{width}',scope['defractionate'](inv_exact(coords,width),table),sizes)
    assert verified==1512
    print(f'PASS: pinned source blob, six historical page mappings, {verified} scored route outcomes')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--checkout'); a=ap.parse_args()
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    inputs=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    rows=[json.loads(line) for line in (HERE/'cases.jsonl').read_text(encoding='utf-8').splitlines()]
    controls=json.loads((HERE/'controls.json').read_text(encoding='utf-8'))
    assert result['plan_sha256']==hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest()
    assert len(rows)==1848 and len(controls)==588
    assert result['source_named_rows']==1260 and result['source_scored_rows']==924
    assert result['source_gate_rows']==2 and result['exact_variant_gate_rows']==2
    assert result['source_roundtrip_failures']==sum(not c['source_roundtrip'] for c in controls)==476
    assert result['exact_roundtrip_failures']==sum(not c['exact_roundtrip'] for c in controls)==0
    by={(r['page'],r['key'],r['route']):r for r in rows}
    assert len(by)==len(rows)
    for item in inputs:
        path=ROOT/'data'/'pages'/f"{item['page']}.json"
        assert hashlib.sha256(path.read_bytes()).hexdigest()==item['site_json_sha256']
        flat,sizes=parse(json.loads(path.read_text(encoding='utf-8'))['raw'])
        assert len(flat)==item['runes'] and len(sizes)==item['words']
        n=len(flat)
        for key in plan['keywords']:
            direct=by[(item['page'],key,'direct')]
            assert direct['invalid']==0 and direct['output_sha256']==digest(flat)
            for label in ('n-5','n+5','n//2','2*n//3'):
                assert by[(item['page'],key,'split:'+label)]['status']=='source-skipped'
            for width in plan['source_named_routes']['columnar_widths']:
                row=by[(item['page'],key,f'exact-column:{width}')]
                assert row['status']=='scored' and row['raw_ioc']<=1
    if a.checkout: verify_source(a.checkout,plan,inputs,rows)
    print('PASS: 1,848 distinct route rows, six inputs, 588 planted controls, source gate counts')
if __name__=='__main__': main()
