"""Independent source-versus-compiled ordered beam audit on synthetic inputs only."""
import argparse, ast, hashlib, importlib.util, json, random, sys, time
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--producer-root',type=Path,required=True);p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    plan=json.loads(a.plan.read_bytes());assert hashlib.sha256((a.producer_root/'engine.py').read_bytes()).hexdigest()==plan['engine_sha256']
    spec=importlib.util.spec_from_file_location('keyword_audited_engine',a.producer_root/'engine.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
    source=a.producer_root/'source/liber-primus/analysis/campaign18_skip/sweep.py'
    tree=ast.parse(source.read_text(encoding='utf8'));node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='beam');code=ast.unparse(node)
    assert code.count('return list(best[3])')==1
    env=dict(e.env);exec(compile(code.replace('return list(best[3])','return beams'),'<unchanged-source-terminal-return>', 'exec'),env);native=env['beam']
    start=time.perf_counter();checked=0;terminal_count=0;maximum_error=0.
    for row in plan['cases']:
        rng=random.Random(row['seed']);length=row['length'];width=row['width'];phase=row['phase'];sign=row['sign']
        if row['kind']=='constant':ct=[row['symbol']]*length;key=[row['key_symbol']]*(4*length+64)
        else:ct=[rng.randrange(29) for _ in range(length)];key=[rng.randrange(29) for _ in range(row['key_length'])]
        if row['atbash']:ct=[28-x for x in ct]
        ct=np.array(ct,np.int64);key=np.array(key,np.int64)
        exact=native(ct,key,sign,phase,length,width);paths,scores,pointers,latin=e.beam(ct,key,sign,phase,length,width,True)
        assert len(exact)==len(paths)==len(scores)==len(pointers)==len(latin),row
        for i,(score,pointer,text,path) in enumerate(exact):
            assert path==tuple(int(x) for x in paths[i]) and pointer==pointers[i] and len(text)==latin[i],(row,i)
            error=abs(score-scores[i]);assert error==0.,(row,i,error);maximum_error=max(maximum_error,error)
            assert text==e.text(path)
        terminal_count+=len(exact);checked+=1
        print('Independent synthetic ordered-beam case',checked,'/',len(plan['cases']),flush=True)
    out=dict(status='PASS',plan_sha256=hashlib.sha256(a.plan.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),engine_sha256=plan['engine_sha256'],source_beam_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),synthetic_cases=checked,all_ordered_terminal_hypotheses=terminal_count,maximum_cumulative_score_error=maximum_error,all_paths_pointers_latin_lengths_and_tie_order_exact=True,manuscript_loaded_or_scored=False,seconds=time.perf_counter()-start)
    a.output.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(out,indent=2))

if __name__=='__main__':main()
