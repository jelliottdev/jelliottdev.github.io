"""Synthetic-only timing of the exact existing three-arm English scorer."""
import importlib.util,json,sys,time
from pathlib import Path
import numpy as np
from numba import njit
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
path=ROOT/'experiments/records/lp2-page-pair-english/run.py'
spec=importlib.util.spec_from_file_location('prior_page_english',path);prior=importlib.util.module_from_spec(spec);sys.modules[spec.name]=prior;spec.loader.exec_module(prior)
score_pair=prior.score_pair
@njit
def shifted_grid(pages,lengths,symbols,sizes,frequencies):
    best=-1e300;alignments=0;runes=0
    for i in range(len(lengths)):
        for j in range(i+1,len(lengths)):
            na,nb=lengths[i],lengths[j]
            if min(na,nb)<120:continue
            for lag in range(-(nb-120),na-120+1):
                sa=max(lag,0);sb=max(-lag,0);n=min(na-sa,nb-sb)
                scores,quads=score_pair(pages[i,sa:sa+n],pages[j,sb:sb+n],symbols,sizes,frequencies)
                alignments+=1;runes+=n
                for arm in range(3):
                    if scores[arm]>best:best=scores[arm]
    return best,alignments,runes
def main():
    # All rune contents and model values are synthetic; no manuscript scoring.
    rng=np.random.default_rng(330120261024)
    lengths=np.array([262,266,201,217,261],dtype=np.int64)
    pages=rng.integers(0,29,(len(lengths),277),dtype=np.int64)
    labels=[a['latin'] for a in json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']]
    symbols=np.zeros((29,2),dtype=np.int64);sizes=np.array(list(map(len,labels)),dtype=np.int64)
    for i,label in enumerate(labels):
        for j,c in enumerate(label):symbols[i,j]=ord(c)-65
    freq=rng.uniform(-9,-3,26**4)
    shifted_grid(pages,lengths,symbols,sizes,freq) # compile excluded
    times=[]
    for _ in range(3):
        start=time.perf_counter();_,cells,runes=shifted_grid(pages,lengths,symbols,sizes,freq);times.append(time.perf_counter()-start)
    median=sorted(times)[1];full=median*60392906/runes
    out={'synthetic_only':True,'scorer_source':str(path.relative_to(ROOT)),'operations':['A+B','A-B','B-A'],'synthetic_page_lengths':lengths.tolist(),'synthetic_alignments':cells,'synthetic_rune_positions_all_arms':runes,'timings_seconds':times,'estimated_full_target_grid_seconds':full,'estimated_target_plus128_nulls_minutes':full*129/60,'estimated_target_plus64_nulls_minutes':full*65/60,'model_values':'Synthetic random table; only scoring shape and arithmetic match. Exact pinned English model loaded after plan freeze.'}
    (Path(__file__).parent/'benchmark.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
