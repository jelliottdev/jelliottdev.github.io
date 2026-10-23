"""Pin the source page and literal scoring table from one archived Git revision."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=HERE.parents[3]/'source-archives/Wulfic-Cicada3301-Liber_Primus'
COMMIT='bf89d3d13aad2b8f2c95ab195cf1b092f250775c'


def git_bytes(path):
    return subprocess.check_output(['git','show',f'{COMMIT}:{path}'],cwd=SOURCE)


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip()==COMMIT
    page_path='pages/page_24/runes.txt'
    page_bytes=git_bytes(page_path)
    script_paths=['tools/legacy/p24_char_tests.py','tools/legacy/p24_prime0_post.py']
    scripts={p:git_bytes(p) for p in script_paths}
    source=ast.parse(scripts[script_paths[1]].decode('utf-8'))
    table=next(ast.literal_eval(node.value) for node in source.body
               if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='COMMON_3GRAMS' for target in node.targets))
    alphabet='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
    runes=[alphabet.index(c) for c in page_bytes.decode('utf-8') if c in alphabet]
    site_path='text/lp2-07.txt'
    site=(ROOT/site_path).read_bytes()
    assert runes==[alphabet.index(c) for c in site.decode('utf-8') if c in alphabet]
    assert len(runes)==208
    record={'schema':'liberpedia-wulfic-p24-inputs-v1','source_commit':COMMIT,
            'source_page_path':page_path,'source_page_sha256':hashlib.sha256(page_bytes).hexdigest(),
            'source_scripts':{p:hashlib.sha256(content).hexdigest() for p,content in scripts.items()},
            'site_page':'lp2-07','site_path':site_path,'site_sha256':hashlib.sha256(site).hexdigest(),
            'alphabet':alphabet,'runes':runes,'trigram_weights':table}
    (HERE/'inputs.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS: pinned page_24 = LP2-07, 208 GP runes, source table extracted')


if __name__=='__main__':main()
