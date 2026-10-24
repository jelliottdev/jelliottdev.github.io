"""External-input adapter for the frozen C-01 replay; no implicit network calls."""
import argparse, hashlib, importlib.util, json, os, subprocess, sys, tempfile, time
from pathlib import Path, PurePosixPath
sys.dont_write_bytecode=True
import numpy as np
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'source'
BASE=SOURCE/'liber-primus/analysis/round10/L4-skeleton'
KJV_URL='https://www.gutenberg.org/files/10/10-0.txt'
def read(name):return json.loads((HERE/name).read_text(encoding='utf-8'))
def digest(b):return hashlib.sha256(b).hexdigest()
def array_digest(a):return digest(a.astype('<i2').tobytes())
def git_environment():
    env=os.environ.copy()
    # A partial clone must not silently fetch missing objects or prompt for login.
    env.update(GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0')
    return env
def safe_path(root,relative):
    p=PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0]!='liber-primus':raise ValueError('Invalid input path')
    target=(root/Path(*p.parts)).resolve()
    if not target.is_relative_to(root.resolve()):raise ValueError('Input path escapes root')
    return target
def check_bytes(raw,item):
    if ('bytes' in item and len(raw)!=item['bytes']) or digest(raw)!=item['sha256']:
        raise ValueError('Input bytes do not match frozen pin: '+item['path'])
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m);return m
def checked_sources():
    manifest=read('inputs-frozen.json')
    for item in manifest['source_files']:check_bytes(safe_path(SOURCE,item['path']).read_bytes(),item)
    check_bytes((SOURCE/'LICENSE').read_bytes(),dict(path='LICENSE',sha256=read('publication-assessment.json')['license']['sha256']))
    return manifest
def modules(input_root):
    manifest=checked_sources();sys.path.insert(0,str(BASE))
    skel=load_module('portable_skel',BASE/'skel.py')
    # Map the unchanged loader's original relative glob rules to external inputs.
    skel.SOURCES=[(str(input_root/Path(p).relative_to(SOURCE)),tag) for p,tag in skel.SOURCES]
    skel.ROOT=str(input_root/'liber-primus')
    scanner=load_module('portable_scanner',BASE/'scanner.py')
    return skel,scanner,manifest
def validate_inputs(input_root):
    input_root=Path(input_root).resolve();skel,scanner,manifest=modules(input_root)
    for item in manifest['corpus']+[manifest['manuscript']]:check_bytes(safe_path(input_root,item['path']).read_bytes(),item)
    corpus,meta=skel.load_corpus(verbose=False)
    expected=manifest['corpus']
    if list(corpus)!=[x['name'] for x in expected]:raise ValueError('Loader membership/order differs from frozen corpus')
    for item in expected:
        a=corpus[item['name']]
        if len(a)!=item['words'] or array_digest(a)!=item['lengths_sha256']:raise ValueError('Normalized array mismatch: '+item['name'])
    if meta!=[(x['name'],'ok',x['words']) for x in expected]:raise ValueError('Loader metadata differs')
    lp,fc=skel.lp2_words();m=manifest['manuscript']
    if len(lp)!=m['words'] or array_digest(lp)!=m['lengths_sha256'] or array_digest(fc)!=m['fcounts_sha256']:raise ValueError('Manuscript array mismatch')
    return skel,scanner,corpus,meta
def download_kjv(expected):
    # Only this explicit public URL, bounded to expected bytes; never a substitute.
    import urllib.request
    with urllib.request.urlopen(KJV_URL,timeout=30) as response:
        if response.url!=KJV_URL:raise ValueError('Unexpected redirect; obtain and validate local bytes instead')
        raw=response.read(expected['bytes']+1)
    check_bytes(raw,expected);return raw
def setup_inputs(git_root,destination,kjv_file=None,download=False):
    manifest=checked_sources();destination=Path(destination).resolve()
    if destination.exists():raise ValueError('Setup destination must not exist')
    if bool(kjv_file)==bool(download):raise ValueError('Choose exactly one explicit KJV file or download option')
    kjv=next(x for x in manifest['corpus'] if x['name']=='data/kjv.txt')
    raw_kjv=download_kjv(kjv) if download else Path(kjv_file).read_bytes();check_bytes(raw_kjv,kjv)
    revision=manifest['revision'];git_root=Path(git_root).resolve()
    subprocess.check_call(['git','-C',str(git_root),'cat-file','-e',revision+'^{commit}'],stdout=subprocess.DEVNULL,env=git_environment())
    destination.parent.mkdir(parents=True,exist_ok=True)
    # The temporary directory is created in the explicit destination's parent;
    # cleanup is limited to that library-owned directory on failure.
    with tempfile.TemporaryDirectory(prefix='c01-inputs-',dir=destination.parent) as temp:
        stage=Path(temp)/'inputs';stage.mkdir()
        for item in manifest['corpus']+[manifest['manuscript']]:
            raw=raw_kjv if item['path']==kjv['path'] else subprocess.check_output(['git','-C',str(git_root),'show',revision+':'+item['path']],env=git_environment())
            check_bytes(raw,item);p=safe_path(stage,item['path']);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        validate_inputs(stage)
        stage.rename(destination)
    return dict(files=len(manifest['corpus'])+1,corpus_texts=len(manifest['corpus']),destination=str(destination),network_used=bool(download))
def parity(input_root,original_root):
    skel,scanner,C,meta=validate_inputs(input_root)
    original_root=Path(original_root).resolve();oldbase=original_root/'liber-primus/analysis/round10/L4-skeleton'
    oldskel=load_module('original_skel',oldbase/'skel.py');oldscanner=load_module('original_scanner',oldbase/'scanner.py')
    for item in read('inputs-frozen.json')['source_files']:check_bytes(safe_path(original_root,item['path']).read_bytes(),item)
    oldC,oldmeta=oldskel.load_corpus(verbose=False)
    assert list(C)==list(oldC) and meta==oldmeta
    assert all(np.array_equal(a,oldC[k]) for k,a in C.items())
    assert all(np.array_equal(a,b) for a,b in zip(skel.lp2_words(),oldskel.lp2_words()))
    rng=np.random.default_rng(330120261025);a=rng.integers(1,16,5000,dtype=np.int16);rows=[]
    for W in [120,400,2928]:
        obs=a[2048:2048+W]+rng.integers(0,4,W,dtype=np.int16);fc=obs-a[2048:2048+W]
        def patterns(sk,sc):return [sc.Pattern('exact',sk.groups_slack(obs,0),W,8192),sc.Pattern('slack1',sk.groups_slack(obs,1),W,8192),sc.Pattern('interval',sk.groups_interval(obs,fc),W,8192)]
        p,q=patterns(skel,scanner),patterns(oldskel,oldscanner)
        x=scanner.scan_block(a,p,8192);y=oldscanner.scan_block(a,q,8192)
        bx,tx=scanner.scan_corpus({'fixture':a},p,4096,8192);by,ty=oldscanner.scan_corpus({'fixture':a},q,4096,8192)
        assert bx==by and tx==ty and all(np.array_equal(x[k],y[k]) for k in x)
        rows.append(dict(window=W,matchers=3,offsets_per_matcher=len(a)-W+1,bit_identical=True))
    return dict(corpus_arrays_equal=94,manuscript_arrays_equal=2,fixture_cases=rows,fixture_offset_values=sum(r['offsets_per_matcher']*3 for r in rows),blocked_maxima_equal=True,target_rerun=False,numpy=np.__version__,adapters=['External ROOT/SOURCES path binding only; source glob rules and loader unchanged','Source output HERE redirected only for explicit run command'])
def run(input_root,stage,output):
    if np.__version__!='2.5.4':raise ValueError('Canonical replay requires NumPy2.5.4')
    skel,scanner,C,meta=validate_inputs(input_root);output=Path(output).resolve()
    if output.exists():raise ValueError('Run output directory must not exist')
    output.mkdir(parents=True);sys.modules['skel']=skel;sys.modules['scanner']=scanner
    name='positive_control' if stage=='t0' else 'run_scan';m=load_module('portable_'+name,BASE/(name+'.py'));m.HERE=str(output)
    sys.argv=[name+'.py']+(['T0'] if stage=='t0' else []);start=time.perf_counter();m.main()
    return dict(stage=stage,seconds=time.perf_counter()-start,numpy=np.__version__,output=str(output),source_main_unchanged=True)
def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    v=sub.add_parser('verify');v.add_argument('--inputs',required=True)
    s=sub.add_parser('setup');s.add_argument('--git',required=True);s.add_argument('--destination',required=True);g=s.add_mutually_exclusive_group(required=True);g.add_argument('--kjv-file');g.add_argument('--download-kjv',action='store_true')
    q=sub.add_parser('parity');q.add_argument('--inputs',required=True);q.add_argument('--original',required=True)
    t=sub.add_parser('run');t.add_argument('--inputs',required=True);t.add_argument('--stage',choices=['t0','target'],required=True);t.add_argument('--output',required=True)
    args=p.parse_args()
    if args.command=='verify':
        _,_,C,_=validate_inputs(args.inputs);result=dict(validated_texts=len(C),words=sum(map(len,C.values())),eligible_texts=sum(len(a)>=2928 for a in C.values()),network_used=False)
    elif args.command=='setup':result=setup_inputs(args.git,args.destination,args.kjv_file,args.download_kjv)
    elif args.command=='parity':result=parity(args.inputs,args.original)
    else:result=run(args.inputs,args.stage,args.output)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
