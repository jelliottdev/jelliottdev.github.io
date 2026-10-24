"""Source gate and fixed synthetic runtime probe; never opens manuscript input."""
import ast,hashlib,importlib.util,json,random,time
from pathlib import Path
H=Path(__file__).resolve().parent;LP=H/'source/liber-primus'
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def definitions(path,names,env):
    nodes=[n for n in ast.parse(path.read_text(encoding='utf8')).body if isinstance(n,ast.FunctionDef) and n.name in names or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)]
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(path),'exec'),env)
def load():
    gp=module('ak_gp',LP/'src/lp/gematria.py');sc=module('ak_score',LP/'src/lp/score.py');q=sc.Quadgram(str(LP/'data/english_quadgrams.txt'))
    env=dict(gp=gp,N=29,Q=q,_QD=q.d,_QF=q.floor,_TR=gp.IDX_TO_TRANS,random=random)
    definitions(LP/'analysis/campaign18_skip/skipdecode.py',['_ALIAS','eng_to_idx','idx_to_trans'],env)
    definitions(LP/'analysis/campaign18_skip/armada2/autokey_skip.py',['encipher_autokey','_qdelta','beam_decode_ctautokey','beam_decode_ptautokey','rigid_autokey','gate'],env)
    return env
def main():
    plan=json.loads((H/'native-probe-plan-frozen.json').read_bytes())
    for p,h in plan['pins'].items():assert hashlib.sha256((H/p).read_bytes()).hexdigest()==h,p
    env=load();start=time.perf_counter();gate=env['gate'](verbose=False);rows=[]
    for length in plan['lengths']:
        for word in plan['primers']:
            rng=random.Random(plan['seed']+length+len(word));ct=[rng.randrange(29) for _ in range(length)];primer=env['eng_to_idx'](word)
            for mode in ('P','C'):
                dec=env['beam_decode_ptautokey' if mode=='P' else 'beam_decode_ctautokey'];t=time.perf_counter();out=dec(ct,primer,sign=-1,beam_w=450,max_skip=3)
                rows.append(dict(length=length,primer=word,primer_indices=primer,mode=mode,seconds=time.perf_counter()-t,output_length=len(out['plain_idx']),score=out['score'],pointer=out['ptr_end']))
                print('Synthetic native',length,word,mode,round(rows[-1]['seconds'],5),'seconds output',len(out['plain_idx']),flush=True)
    primers=[[i] for i in range(29)]+[env['eng_to_idx'](w) for w in plan['full_primer_words']]
    out=dict(stage='Synthetic only; manuscript never opened',plan_sha256=hashlib.sha256((H/'native-probe-plan-frozen.json').read_bytes()).hexdigest(),original_gate=gate,labelled_primers=len(primers),distinct_encoded_primers=len({tuple(x) for x in primers}),primer_lengths=[len(x) for x in primers],target_labels=55*len(primers)*2*2,benchmarks=rows,rough_native_projection_seconds=9900*max(x['seconds'] for x in rows),seconds=time.perf_counter()-start)
    dest=H/'native-probe-results.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n')
if __name__=='__main__':main()
