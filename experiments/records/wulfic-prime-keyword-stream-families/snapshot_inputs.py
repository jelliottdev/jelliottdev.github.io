"""Extract finite source inputs from a pinned Wulfic checkout, without importing old code."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
COMMIT = 'bf89d3d13aad2b8f2c95ab195cf1b092f250775c'
PAGE_IDS = sorted(set(range(21, 31)) | {28, 53, 24, 39, 29, 30, 34, 51, 21, 33, 45})
KEYWORD_ONLY_PAGES = list(range(21, 31))
PRIME_PAGES = [21, 22, 24, 26, 27, 28, 29, 30]
STEPPED_PAGES = [28, 53, 24, 39, 29, 30, 34, 51, 21, 33, 45]
SOURCE_RUNE_ORDER = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
GP = {r: i for i, r in enumerate(SOURCE_RUNE_ORDER)}
KW_DIGRAPHS = {'TH':2,'EO':12,'NG':21,'OE':22,'AE':25,'IA':27,'EA':28}
KW_SINGLE = {'F':0,'U':1,'V':1,'O':3,'R':4,'C':5,'K':5,'G':6,'W':7,'H':8,
             'N':9,'I':10,'J':11,'P':13,'X':14,'S':15,'T':16,'B':17,'E':18,
             'M':19,'L':20,'D':23,'A':24,'Y':26}


def git_show(repo, path):
    return subprocess.check_output(['git','show',f'{COMMIT}:{path}'],cwd=repo)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source_literal(tree, target):
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == target for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(target)


def parse_keyword(word):
    result=[];i=0;word=word.upper()
    while i<len(word):
        pair=word[i:i+2]
        if pair in KW_DIGRAPHS:
            result.append(KW_DIGRAPHS[pair]);i+=2
        else:
            if word[i] in KW_SINGLE:result.append(KW_SINGLE[word[i]])
            i+=1
    return result


def singletons(text, separators):
    result=[];position=0;start=0;length=0
    for ch in text:
        if ch in GP:
            if length==0:start=position
            length+=1;position+=1
        elif ch in separators and length:
            if length==1:result.append(start)
            length=0
    if length==1:result.append(start)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    index=json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))
    assert ''.join(x['rune'] for x in index['alphabet'])==SOURCE_RUNE_ORDER
    keyword_only_raw=git_show(args.repo,'tools/legacy/p21_30_keyword_sweep.py')
    stepped_raw=git_show(args.repo,'tools/legacy/keyword_stepped_stream.py')
    keyword_only_tree=ast.parse(keyword_only_raw.decode('utf-8'))
    stepped_tree=ast.parse(stepped_raw.decode('utf-8'))
    # The source's P63 words are literal labels in its KEYWORDS declaration.
    keyword_only_names=[]
    for node in ast.walk(keyword_only_tree):
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='KEYWORDS' for t in node.targets):
            keyword_only_names=[k.value for k in node.value.keys]
    assert len(keyword_only_names)==18
    stepped=source_literal(stepped_tree,'ALL_KEYWORDS')
    assert len(stepped)==20
    pages={}
    for source_page in PAGE_IDS:
        source_path=f'pages/page_{source_page:02d}/runes.txt'
        raw=git_show(args.repo,source_path)
        text=raw.decode('utf-8')
        values=[GP[ch] for ch in text if ch in GP]
        site_path=f'text/lp2-{source_page-17:02d}.txt'
        site_raw=(ROOT/site_path).read_bytes()
        site_values=[GP[ch] for ch in site_raw.decode('utf-8') if ch in GP]
        assert values and values==site_values, source_page
        pages[str(source_page)]={
            'site_page':f'lp2-{source_page-17:02d}',
            'source_path':source_path,
            'source_sha256':sha(raw),
            'site_path':site_path,
            'site_sha256':sha(site_raw),
            'gp_sha256':sha(bytes(values)),
            'runes':values,
            'keyword_singletons':singletons(text,set('.-• \n')),
            'prime_singletons':singletons(text,set('-.\n /&$%•"')),
            'stepped_singletons':singletons(text,set('-\n /%.&$')),
        }
        assert all(0<=p<len(values) for key in ('keyword_singletons','prime_singletons','stepped_singletons') for p in pages[str(source_page)][key])
    output={
        'schema':'liberpedia-wulfic-prime-keyword-source-inputs-v1',
        'source_commit':COMMIT,
        'source_script_sha256':{
            'p21_30_keyword_sweep.py':sha(keyword_only_raw),
            'keyword_stepped_stream.py':sha(stepped_raw),
            'prime_stream_solver.py':sha(git_show(args.repo,'tools/legacy/prime_stream_solver.py')),
        },
        'alphabet':SOURCE_RUNE_ORDER,
        'keyword_only':{name:parse_keyword(name) for name in keyword_only_names},
        'stepped_keywords':stepped,
        'source_page_groups':{'keyword_only':KEYWORD_ONLY_PAGES,'prime_stream':PRIME_PAGES,'keyword_stepped':STEPPED_PAGES},
        'pages':pages,
    }
    target=HERE/'inputs.json'
    text=json.dumps(output,ensure_ascii=False,indent=2)+'\n'
    if args.check:
        assert target.read_text(encoding='utf-8')==text
    else:
        target.write_text(text,encoding='utf-8',newline='\n')
    print(f'PASS: {len(pages)} pinned, nonempty source/site rune streams; 18 + 20 keyword vectors')


if __name__=='__main__':main()
