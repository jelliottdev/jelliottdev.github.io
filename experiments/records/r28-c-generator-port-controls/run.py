"""Offline finite C-port parity; source generator region is compiled unchanged."""
import hashlib,importlib.util,json,os,shutil,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
SEEDS=[0,1,777,3301,4294967295,2147483648,123456789,2147483647]
MODES=['random29','grb5_mod','grb5_rej','shuffle29','php_mt_scale','php_mt_mod','php_php_scale','php_php_mod','glibc_mod']
DRAWS=2000
def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/'source'/f'{name}.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def source_region():
    text=(HERE/'source/grind28.c').read_text()
    return text[text.index('typedef struct { uint32_t mt[624]'):text.index('/* ------------------------------------------------------------------ global model data */')]
def compiled_streams(cases):
    harness='#include <stdint.h>\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#define NRUNE 29\n'+source_region()+r'''
int main(void) {
 unsigned int w; int reducer,n;
 while(scanf("%u %d %d",&w,&reducer,&n)==3) {
  MT m; PhpMT p; GlibcR g; uint8_t *out=malloc(n);
  if(reducer<4) { mt_init_word(&m,w); reduce_stream(&m,reducer,out,n); }
  else if(reducer<8) {php_init(&p,w,reducer>=6);for(int i=0;i<n;i++) {uint32_t x=php_rand31(&p);out[i]=(reducer%2==0)?php_badscale(x):x%29u;} }
  else {glibc_init(&g,w);for(int i=0;i<n;i++)out[i]=glibc_next31(&g)%29u;}
  for(int i=0;i<n;i++)printf("%s%u",i?",":"",out[i]); puts("");free(out);
 }
 return 0;
}
'''
    with tempfile.TemporaryDirectory() as td:
        c=Path(td)/'harness.c';exe=Path(td)/('harness.exe' if os.name=='nt' else 'harness')
        c.write_text(harness)
        subprocess.run(['gcc','-O2','-std=c17','-ffp-contract=off','-o',str(exe),str(c)],check=True,capture_output=True)
        request=''.join(f'{s} {MODES.index(m)} {n}\n' for m,s,n in cases)
        result=subprocess.run([str(exe)],input=request,text=True,capture_output=True,check=True)
    return [[int(v) for v in line.split(',')] for line in result.stdout.splitlines()]
def python_stream(mode,seed,n):
    if mode in MODES[:4]:
        g=load('gen_py27');r=g.MT19937();r.init_by_array([seed]);return g.REDUCERS[mode](r,n)
    return load('gen28').CELL_GENS[mode](seed,n)
def generate():
    for item in json.loads((HERE/'source-manifest.json').read_text())['files']:
        assert hashlib.sha256((HERE/item['path']).read_bytes()).hexdigest()==item['sha256']
    cases=[(m,s,DRAWS) for m in MODES for s in SEEDS]
    vectors=json.loads((HERE/'source/vectors.json').read_text())['seed_vectors']
    cases += [('random29',v['seed'],128) for v in vectors]
    streams=compiled_streams(cases);assert len(streams)==len(cases)
    rows=[]
    for (mode,seed,n),values in zip(cases,streams):
        assert values==python_stream(mode,seed,n),(mode,seed)
        rows.append({'mode':mode,'seed':seed,'draws':n,'sha256':hashlib.sha256(bytes(values)).hexdigest()})
    for values,v in zip(streams[72:],vectors):assert values==v['ks128']
    # Wrong-twist and wrong-initializer discrimination, not a manuscript search.
    differences={}
    for seed in SEEDS:
        a=streams[MODES.index('php_mt_mod')*8+SEEDS.index(seed)]
        b=streams[MODES.index('php_php_mod')*8+SEEDS.index(seed)]
        differences[str(seed)]=sum(x!=y for x,y in zip(a,b));assert differences[str(seed)]>0
    return {'schema':'finite-generator-c-port-v1','source_commit':'f08b20b632d91209ddbaa747e8e2f23df0c78ba1','grid_streams':72,'grid_symbols':144000,'archived_r27_vectors':64,'archived_r27_symbols':8192,'all_exact':True,'twist_mode_differing_symbols':differences,'rows':rows,'interpretation':'Finite compiled source-generator parity only. No source scorer, decoder, native PHP/glibc runtime or LP2 search is replayed.'}
if __name__=='__main__':
    result=generate();(HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: 72 x 2000 C/model symbols and 64 x 128 archived R27 vectors')
