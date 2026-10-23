"""Run unchanged pinned Test8/9 in a temporary tree with exact Git page blobs."""
import argparse,hashlib,json,os,pathlib,re,subprocess,sys,tempfile
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2]
DEFAULT=ROOT.parent/'source-archives'/'Wulfic-Cicada3301-Liber_Primus'
def sha(b):return hashlib.sha256(b).hexdigest()
def get(src,p,path,want):
    b=subprocess.check_output(['git','-C',str(src),'show',p['source_revision']+':'+path]);assert sha(b)==want,path;return b
def replay(src):
    p=json.loads((H/'plan.json').read_text(encoding='utf8'))
    with tempfile.TemporaryDirectory() as d:
        base=pathlib.Path(d);script=base/'tools/legacy/session17_clean_solve.py';script.parent.mkdir(parents=True)
        script.write_bytes(get(src,p,p['source_script'],p['source_script_sha256']))
        for q in p['pages']:
            path=base/'tools/pages'/f"page_{q['source_page']:02d}"/'runes.txt';path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(get(src,p,q['source_path'],q['source_sha256']))
        env=os.environ.copy();env['PYTHONIOENCODING']='utf-8'
        process=subprocess.run([sys.executable,str(script),'8','9'],capture_output=True,env=env)
        assert process.returncode==0,process.stderr.decode('utf8',errors='replace')[-2000:]
        out=process.stdout.decode('utf8',errors='replace')
    # Parse each printed page block independently.
    chunks=re.split(r'\n  P(\d+) \(\d+ runes\)',out)
    flagged=[int(chunks[i]) for i in range(1,len(chunks),2) if '[!!! POSSIBLE PERIOD' in chunks[i+1]]
    observed=json.loads((H/'results.json').read_text(encoding='utf8'))
    expected=[z['source_page'] for z in observed['test9']['flagged']]
    assert flagged==expected,(flagged,expected)
    assert ('No strong periodicity found' in out)==(observed['summary']['test8_reported_unique']==0)
    return {'schema':'wulfic-session17-original-execution-v1','source_revision':p['source_revision'],
            'stdout_sha256_lf_utf8':sha(out.replace('\r\n','\n').encode('utf8')),'source_flagged_pages':flagged,
            'test8_no_strong_report':'No strong periodicity found' in out,
            'source_script_sha256':p['source_script_sha256']}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=pathlib.Path,default=DEFAULT);ap.add_argument('--check',action='store_true');a=ap.parse_args()
    result=replay(a.source_root);dest=H/'source-replay.json';s=json.dumps(result,indent=2)+'\n'
    if a.check:assert dest.read_text(encoding='utf8')==s;print('PASS unchanged source Test8/9 output')
    else:dest.write_text(s,encoding='utf8',newline='\n');print('PASS',len(result['source_flagged_pages']),'source Test9 flags')
