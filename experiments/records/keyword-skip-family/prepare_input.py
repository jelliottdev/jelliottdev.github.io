"""Copy exact externally held manuscript bytes from an explicitly supplied local Git clone."""
import argparse,hashlib,os,subprocess
from pathlib import Path
REV='f08b20b632d91209ddbaa747e8e2f23df0c78ba1'
EXPECTED='5e0003aa7f7dde3b238d17c5f964790dbf6bf9db5edacc4a5ec0bad81c6f4bce'
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--git-source',required=True);p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output)
    assert not out.exists(),'Output must be new'
    env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0')
    data=subprocess.check_output(['git','-C',str(Path(a.git_source).resolve()),'show',REV+':liber-primus/data/krisyotam_runes.txt'],env=env)
    assert hashlib.sha256(data).hexdigest()==EXPECTED
    out.write_bytes(data);print('Prepared exact external manuscript:',out)
