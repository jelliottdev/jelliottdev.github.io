"""Synthetic ordered-native-terminal parity and causal frontier invariants."""
import argparse,ast,copy,hashlib,importlib.util,json,random,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np

def native_terminals(root,env):
    tree=ast.parse((root/'source/liber-primus/analysis/campaign18_skip/armada2/autokey_skip.py').read_text(encoding='utf8'));out={}
    for mode,name in [('P','beam_decode_ptautokey'),('C','beam_decode_ctautokey')]:
        node=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name));assert isinstance(node.body[-1],ast.Return)
        node.body[-1]=ast.Return(value=ast.Name(id='beams',ctx=ast.Load()));namespace=dict(env)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<source-terminal-return-only>','exec'),namespace);out[mode]=namespace[name]
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--producer-root',type=Path,required=True);p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();plan=json.loads(a.plan.read_bytes())
    assert hashlib.sha256((a.producer_root/'engine.py').read_bytes()).hexdigest()==plan['engine_sha256']
    sys.path.insert(0,str(a.producer_root.resolve()));spec=importlib.util.spec_from_file_location('independent_autokey_engine',a.producer_root/'engine.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e);natives=native_terminals(a.producer_root,e.env)
    start=time.perf_counter();terminals=0;rigid=0;maxskip=0;cases=0
    for row in plan['cases']:
        primer=row['primer'];length=row['length'];rng=random.Random(row['seed']);cipher=[row['constant']]*length if row['constant'] is not None else [rng.randrange(29) for _ in range(length)]
        exact=natives[row['mode']](cipher,primer,sign=row['sign'],beam_w=row['width'],max_skip=3)
        paths,scores,pointers,latin=e.terminals(cipher,primer,row['sign'],row['width'],row['mode']);assert len(exact)==len(paths)
        for i,t in enumerate(exact):
            assert tuple(int(x) for x in paths[i])==t[3] and pointers[i]==t[1] and scores[i]==t[0] and latin[i]==len(t[2]),(row,i)
            assert len(t[3])==length and e.text(t[3])==t[2]
            if row['mode']=='P':
                skip=t[1]-(length-1);assert 0<=skip<=len(primer)-1;maxskip=max(maxskip,skip)
        if row['mode']=='P' and len(primer)==1:
            expected=e.env['rigid_autokey'](cipher,primer,sign=row['sign'],mode='P');assert expected['plain_idx']==list(exact[0][3]) and len(exact)==1 and exact[0][1]==length-1;rigid+=1
        source=e.env['beam_decode_ptautokey' if row['mode']=='P' else 'beam_decode_ctautokey'](cipher,primer,sign=row['sign'],beam_w=row['width'],max_skip=3)
        assert source==e.decode(cipher,primer,row['sign'],row['width'],row['mode'])
        terminals+=len(exact);cases+=1
    result=dict(status='PASS',plan_sha256=hashlib.sha256(a.plan.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),engine_sha256=plan['engine_sha256'],synthetic_cases=cases,ordered_terminal_hypotheses=terminals,all_paths_pointers_latin_lengths_scores_and_stable_order_exact=True,all_source_return_dictionaries_exact=True,singleton_P_rigid_equal_cases=rigid,maximum_observed_P_cumulative_skips=maxskip,all_outputs_complete=True,manuscript_loaded_or_scored=False,seconds=time.perf_counter()-start)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
