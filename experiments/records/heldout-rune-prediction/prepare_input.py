"""Extract only the exact external transcription from an explicit local Git repository."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--git',required=True,type=Path);p.add_argument('--destination',required=True,type=Path);a=p.parse_args()
    m=json.loads((H/'reproduction/source-inputs.json').read_bytes());r=next(x for x in m['files'] if x['path']=='liber-primus/data/krisyotam_runes.txt')
    env=os.environ.copy();env.update(GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0')
    raw=subprocess.check_output(['git','-C',str(a.git),'show',m['revision']+':'+r['path']],env=env)
    assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256']
    with a.destination.open('xb') as out:out.write(raw)
    print('Prepared one exact external transcription; no network or installation.')
