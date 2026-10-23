"""Pin archived autokey source values and exact, nonempty current page streams."""
import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
COMMIT='bf89d3d13aad2b8f2c95ab195cf1b092f250775c'
ALPHABET='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
GP={ch:i for i,ch in enumerate(ALPHABET)}
SEPARATORS=set('-\n /%.&$')


def git_show(repo,path):
    return subprocess.check_output(['git','show',f'{COMMIT}:{path}'],cwd=repo)


def literal(tree,name):
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(name)


def singleton_positions(text):
    positions=[];pos=0;start=0;length=0
    for ch in text:
        if ch in GP:
            if length==0:start=pos
            pos+=1;length+=1
        elif ch in SEPARATORS and length:
            if length==1:positions.append(start)
            length=0
    if length==1:positions.append(start)
    return positions


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=args.repo,text=True).strip()==COMMIT
    index=json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))
    assert ''.join(item['rune'] for item in index['alphabet'])==ALPHABET
    a_raw=git_show(args.repo,'tools/legacy/autokey_comprehensive.py')
    b_raw=git_show(args.repo,'tools/legacy/p21_30_autokey_solver.py')
    a=literal(ast.parse(a_raw.decode('utf-8')),'ALL_KEYWORDS')
    b=literal(ast.parse(b_raw.decode('utf-8')),'ALL_KEYWORDS')
    assert len(a)==22 and len(b)==18
    same={name:values for name,values in b.items() if a.get(name)==values}
    different={name:values for name,values in b.items() if a.get(name)!=values}
    assert len(same)==17 and different=={'DEOR':[23,18,3,4]}
    pages={}
    for old in range(21,55):
        source_path=f'pages/page_{old:02d}/runes.txt'
        raw=git_show(args.repo,source_path)
        body=raw.decode('utf-8').strip()
        runes=[GP[ch] for ch in body if ch in GP]
        current=f'text/lp2-{old-17:02d}.txt'
        site_raw=(ROOT/current).read_bytes()
        site=[GP[ch] for ch in site_raw.decode('utf-8') if ch in GP]
        assert runes and runes==site,(old,len(runes),len(site))
        singles=singleton_positions(body)
        assert all(0<=p<len(runes) for p in singles)
        pages[str(old)]={'page':f'lp2-{old-17:02d}',
                         'source_path':source_path,'source_sha256':hashlib.sha256(raw).hexdigest(),
                         'site_path':current,'site_sha256':hashlib.sha256(site_raw).hexdigest(),
                         'runes':runes,'singletons':singles}
    reading=json.loads((ROOT/'data/evidence/known-readings.json').read_text(encoding='utf-8'))
    warning=next(x for x in reading['controls'] if x['id']=='warning')
    lp1=warning['decoded_pages'][0]['rune_indices']
    assert len(lp1)>100 and all(0<=v<29 for v in lp1)
    output={'schema':'liberpedia-wulfic-autokey-inputs-v1','source_commit':COMMIT,
            'source_scripts':{'autokey_comprehensive.py':hashlib.sha256(a_raw).hexdigest(),
                              'p21_30_autokey_solver.py':hashlib.sha256(b_raw).hexdigest()},
            'alphabet':ALPHABET,'comprehensive_keywords':a,'p21_keywords':b,
            'p21_same_keyword_count':17,'p21_distinct_keyword_vectors':different,
            'known_warning_gp':lp1,'known_warning_source_sha256':hashlib.sha256((ROOT/'data/evidence/known-readings.json').read_bytes()).hexdigest(),
            'pages':pages}
    target=HERE/'inputs.json'
    text=json.dumps(output,ensure_ascii=False,indent=2)+'\n'
    if args.check:assert target.read_text(encoding='utf-8')==text
    else:target.write_text(text,encoding='utf-8',newline='\n')
    print(f'PASS: {len(pages)} source/site page matches; 22 source keywords and one distinct P21–30 Deor array')


if __name__=='__main__':main()
