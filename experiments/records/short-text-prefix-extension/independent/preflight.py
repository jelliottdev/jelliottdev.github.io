"""No target scoring: verify exact input membership/RNG and counter against scalar oracle."""
import sys,json,hashlib,argparse,datetime,ast
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
import direct as D
H=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser();p.add_argument('--inputs-root',required=True,type=Path);p.add_argument('--baseline-root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();assert not a.output.exists()
    baseline=a.baseline_root.resolve();manifest_path=baseline/'reproduction/inputs-frozen.json';manifest=json.loads(manifest_path.read_bytes());short=[r for r in manifest['corpus'] if r['words']<2928]
    assert len(short)==10 and len(manifest['corpus'])==94
    checked=[]
    for row in short:
        raw=(a.inputs_root/row['path']).read_bytes();assert D.sha(raw)==row['sha256'] and len(raw)==row['bytes']
        values=D.normalize(raw,row['path']);assert len(values)==row['words'] and D.ah(values)==row['lengths_sha256']
        checked.append(dict(name=row['name'],words=len(values),starts400=max(0,len(values)-399),starts120=max(0,len(values)-119),raw_sha256=D.sha(raw),normalized_sha256=D.ah(values)))
    assert sum(r['starts400'] for r in checked)==5378 and sum(r['starts120'] for r in checked)==8037
    m=manifest['manuscript'];raw=(a.inputs_root/m['path']).read_bytes();assert D.sha(raw)==m['sha256']
    source=baseline/'reproduction/source/liber-primus';obs,fc=D.manuscript(raw,source/'src/lp/gematria.py')
    assert len(obs)==2928 and D.ah(obs)==m['lengths_sha256'] and D.ah(fc)==m['fcounts_sha256']
    patterns=D.patterns(obs,fc);pattern_pins=[dict(name=name,width=len(o),observed_sha256=D.ah(o),fcounts_sha256=D.ah(f)) for name,(o,f) in patterns.items()]
    # Unseeded models are not inferred: test only the independent counter here.
    rng=np.random.default_rng(241024010);offsets=0;cases=0
    for w in [1,2,7,17]:
        for n in [w-1,w,w+1,3*w+2]:
            values=rng.integers(0,45,n,dtype=np.int16);o=rng.integers(0,45,w,dtype=np.int16);f=rng.integers(0,7,w,dtype=np.int16)
            actual=D.count(values,o,f);oracle=[]
            for start in range(max(0,n-w+1)):
                oracle.append(sum(1<=int(o[j])<=29 and max(1,int(o[j])-int(f[j]))<=int(values[start+j])<=min(40,int(o[j])) for j in range(w)))
            assert actual.tolist()==oracle;offsets+=len(oracle);cases+=1
    scanner=(source/'analysis/round10/L4-skeleton/scanner.py').read_text(encoding='utf-8')
    assert 'P = max(p.P for p in patterns)' in scanner and 'if M < P:' in scanner and 'if len(blk) < P:' in scanner
    r=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),direct_counter_sha256=D.sha((H/'direct.py').read_bytes()),preflight_script_sha256=D.sha((H/'preflight.py').read_bytes()),baseline_manifest_sha256=D.sha(manifest_path.read_bytes()),ten_inputs_verified=checked,manuscript_verified=True,prefix_patterns=pattern_pins,rng='np.random.default_rng(3301); consume4 permutations of2928, then2permutations of400, then2of120; actual observed/fcount pair hashes retained.',counter_scalar_oracle_cases=cases,counter_scalar_offsets=offsets,gate='Source P is maximum pattern width: separate three-pattern width400 and width120 batches are required; do not only modify the text-level comparison.',target_scores_computed=False)
    a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print('PASS exact10inputs,8/10membership,patternRNG,',cases,'scalar controls; no target scores')
if __name__=='__main__':main()
