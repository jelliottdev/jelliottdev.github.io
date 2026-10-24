"""Portable path adapter; source algorithms and frozen scientific expectations unchanged."""
import sys,json,argparse,hashlib,importlib.util,copy
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def verify():
    manifest=read(HERE/'inputs-frozen.json')
    for row in manifest['staged_source']:
        assert sha(HERE/row['path'])==row['sha256'],row['path']
    plan=read(HERE/'preflight-plan-frozen.json')
    assert sha(HERE/'replay.py')==plan['runner_sha256']
    assert sha(HERE/'inputs-frozen.json')==plan['inputs_sha256']
    target=read(HERE/'target-plan-frozen.json')
    for field,name in [('preflight_plan_sha256','preflight-plan-frozen.json'),('control_results_sha256','control-results.json'),('inputs_sha256','inputs-frozen.json'),('diagnostic_amendment_sha256','diagnostic-amendment-before-target.json')]:
        assert target[field]==sha(HERE/name),name
    assert read(HERE/'target-results.json')['target_plan_sha256']==sha(HERE/'target-plan-frozen.json')
    assert read(HERE/'independent-target-audit.json')['target_results_sha256']==sha(HERE/'target-results.json')
    assert read(HERE/'control-failure-audit.json')['control_results_sha256']==sha(HERE/'control-results.json')
    assert not read(HERE/'control-results.json')['target_power_gate_pass']
    assert read(HERE/'target-plan-frozen.json')['original_strict_power_gate_pass'] is False
    return manifest

def configured():
    verify();r=load('replay',HERE/'replay.py');r.verify=verify;r.PAYLOAD=HERE/'source/liber-primus/analysis/pp49_51/payload.bin';return r

def equivalent(got,want,path='root'):
    assert type(got)==type(want),(path,type(got),type(want))
    if isinstance(want,dict):
        assert got.keys()==want.keys(),(path,'fields differ')
        for k in want:equivalent(got[k],want[k],path+'.'+k)
    elif isinstance(want,list):
        assert len(got)==len(want),(path,'length')
        for i,(a,b) in enumerate(zip(got,want)):equivalent(a,b,path+f'[{i}]')
    elif isinstance(want,float):assert abs(got-want)<1e-10,(path,got,want)
    else:assert got==want,(path,got,want)

def normalized_controls(data):
    data=copy.deepcopy(data)
    for k in ['elapsed_seconds','synthetic_max_decode_seconds','conservative_1000null_seconds']:data.pop(k)
    for row in data['full256_controls']:row.pop('decode_seconds')
    return data

def compare(output):
    equivalent(normalized_controls(read(output/'control-results.json')),normalized_controls(read(HERE/'control-results.json')))
    got=read(output/'target-results.json');want=read(HERE/'target-results.json')
    for obj in (got,want):obj.pop('elapsed_seconds');obj.pop('target_plan_sha256')
    equivalent(got,want)
    print('PASS: all deterministic control and target fields match; only documented timing and fresh target-plan hash excluded.')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);parser.add_argument('--compare',type=Path);args=parser.parse_args()
    if args.compare:verify();compare(args.compare);return
    if args.output is None:parser.error('--output NEW_DIRECTORY is required')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    r=configured();r.H=output
    for name in ['inputs-frozen.json','preflight-plan-frozen.json']:(output/name).write_bytes((HERE/name).read_bytes())
    r.controls()
    equivalent(normalized_controls(read(output/'control-results.json')),normalized_controls(read(HERE/'control-results.json')))
    # The observed strict failure remains a failure. Replay proceeds under the immutable
    # pre-target diagnostic amendment, not by claiming the original power gate passed.
    plan=read(HERE/'target-plan-frozen.json');plan['control_results_sha256']=sha(output/'control-results.json')
    (output/'target-plan-frozen.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    r.target();compare(output)
if __name__=='__main__':main()
