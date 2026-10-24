"""Full fixed replay in temporary output, with external exact transcription; installs/fetches nothing."""
import argparse,hashlib,json,shutil,subprocess,sys,tempfile,time
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def compare(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        assert set(a)==set(b),path
        for k in a:
            if k!='seconds':compare(a[k],b[k],path+'/'+k)
    elif isinstance(a,list) and isinstance(b,list):
        assert len(a)==len(b),path
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i))
    else:assert a==b,path
def call(script,*args):subprocess.run([sys.executable,'-B',str(script),*map(str,args)],check=True)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--transcription',required=True,type=Path);a=p.parse_args();raw=a.transcription.read_bytes();manifest=read(H/'reproduction/source-inputs.json');pin=next(r for r in manifest['files'] if r['path']=='liber-primus/data/krisyotam_runes.txt')
    assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'External transcription differs'
    start=time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='d02-fixed-replay-') as temp:
        root=Path(temp)/'reproduction';shutil.copytree(H/'reproduction',root,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.nbc','*.nbi'))
        transcription=root/'source'/pin['path'];transcription.parent.mkdir(parents=True,exist_ok=True);transcription.write_bytes(raw)
        # Regenerate each immutable scientific output in a library-owned temporary copy.
        (root/'controls-results.json').rename(root/'expected-controls-results.json');call(root/'controls.py')
        compare(read(root/'controls-results.json'),read(root/'expected-controls-results.json'))
        # Original timing bytes are protocol-bound; restore only inside temporary stage.
        shutil.copyfile(root/'expected-controls-results.json',root/'controls-results.json')
        (root/'null-bank').rename(root/'expected-null-bank');call(root/'bank.py')
        compare(read(root/'null-bank/receipt.json'),read(root/'expected-null-bank/receipt.json'))
        with np.load(root/'null-bank/measurements.npz',allow_pickle=False) as x,np.load(root/'expected-null-bank/measurements.npz',allow_pickle=False) as y:
            assert x.files==y.files
            for k in x.files:assert np.array_equal(x[k],y[k]),k
        # Keep the frozen reference bytes for the authorization and reported comparison.
        shutil.copyfile(root/'expected-null-bank/receipt.json',root/'null-bank/receipt.json')
        (root/'observed.json').rename(root/'expected-observed.json');call(root/'evaluate_target.py','--transcription',transcription,'--output',root/'observed.json')
        compare(read(root/'observed.json'),read(root/'expected-observed.json'))
        call(root/'independent/audit_target.py','--producer-root',root,'--check-only')
    print('PASS: full synthetic control study, all1,000 reference runs, all26 target values and independent complete target reconstruction. Expected bundle files untouched. Seconds:',time.perf_counter()-start)
if __name__=='__main__':main()
