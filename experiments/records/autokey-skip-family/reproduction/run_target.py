"""All source-defined autokey full-grid cases; no parameter selection or expected overwrites."""
import hashlib,json,time
from pathlib import Path
import numpy as np
import engine as e
from terminal_scores import normalized
from native_probe import definitions,LP
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(path,value):
    assert not path.exists(),path
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf8',newline='\n')
def main():
    protocol=json.loads((H/'target-protocol-frozen.json').read_bytes())
    for p,h in protocol['pins'].items():assert sha(H/p)==h,p
    assert not (H/'results.json').exists()
    env=dict(gp=e.gp,KRIS=str(LP/'data/krisyotam_runes.txt'));definitions(LP/'analysis/run_stats.py',['load_pages'],env);pages=env['load_pages']()[:-2];assert len(pages)==55
    primers=e.primers();assert len(primers)==45 and len({tuple(p) for _,p in primers})==45
    maxlen=max(map(len,pages));assert maxlen<6000
    shape=(55,45,2,2);scores=np.empty(shape);cumulative=np.empty(shape);pointers=np.empty(shape,np.int32);counts=np.empty(shape,np.int32);terminal_max=np.empty(shape);terminal_rank=np.empty(shape,np.int32)
    winner=np.full((*shape,maxlen),-1,np.int16);normalized_winner=np.full_like(winner,-1);lengths=np.asarray(list(map(len,pages)),np.int32)
    t=time.perf_counter();done=0
    for page,ct in enumerate(pages):
        for j,(label,primer) in enumerate(primers):
            for m,mode in enumerate(('P','C')):
                for s,sign in enumerate((-1,1)):
                    assert time.perf_counter()-t<protocol['runtime_limit_seconds'],'Resource time cap reached; partial data is not a completed result'
                    paths,cum,ptr,latin=e.terminals(ct,primer,sign,450,mode);norm=normalized(paths);best=int(np.argmax(norm));ix=(page,j,m,s)
                    assert paths.shape[1]==len(ct)
                    scores[ix]=norm[0];cumulative[ix]=cum[0];pointers[ix]=ptr[0];counts[ix]=len(paths);terminal_max[ix]=norm[best];terminal_rank[ix]=best+1;winner[ix][:len(ct)]=paths[0];normalized_winner[ix][:len(ct)]=paths[best];done+=1
        ix=np.unravel_index(int(np.argmax(scores[page])),scores[page].shape);print('Target page',page,'/54 cases',done,'best',float(scores[page][ix]),'sourcehits',int((scores[:page+1]>-5.5).sum()),'elapsed',round(time.perf_counter()-t,3),flush=True)
    assert done==9900
    dest=H/'measurements.npz';assert not dest.exists();np.savez_compressed(dest,scores=scores,cumulative=cumulative,pointers=pointers,terminal_count=counts,terminal_max=terminal_max,terminal_rank=terminal_rank,lengths=lengths,source_winner=winner,normalized_winner=normalized_winner)
    def witness(flat,kind='source'):
        ix=np.unravel_index(int(flat),shape);p,j,m,s=map(int,ix);arr=winner[ix] if kind=='source' else normalized_winner[ix];out=arr[:lengths[p]].astype(np.int64).tolist()
        return dict(page=p,physical_page=f'lp2-{p if p<50 else p+1:02d}',primer_index=j,primer_label=primers[j][0],primer=primers[j][1],mode=('P','C')[m],sign=(-1,1)[s],kind=kind,score=float(scores[ix] if kind=='source' else terminal_max[ix]),source_score=float(scores[ix]),terminal_count=int(counts[ix]),terminal_rank=1 if kind=='source' else int(terminal_rank[ix]),plain=out,translit=e.text(out))
    order=np.argsort(-scores.ravel(),kind='stable');source_hits=np.flatnonzero(scores.ravel()>-5.5);norm_hits=np.flatnonzero(terminal_max.ravel()>-5.5)
    save(H/'results.json',dict(protocol_sha256=sha(H/'target-protocol-frozen.json'),measurements_sha256=sha(dest),cases=done,source_hits=len(source_hits),normalized_terminal_hits=len(norm_hits),retained_terminal_hypotheses=int(counts.sum()),normalized_improvements=int((terminal_max>scores).sum()),global_best=witness(order[0]),top40=[witness(i) for i in order[:40]],source_hit_witnesses=[witness(i) for i in source_hits],normalized_hit_witnesses=[witness(i,'normalized') for i in norm_hits],page_array_sha256=[hashlib.sha256(np.asarray(p,dtype='<i8').tobytes()).hexdigest() for p in pages],source_page_lengths=lengths.tolist(),singleton_P_labels=3190,non_singleton_P_and_all_C_labels=6710,purpose=protocol['purpose'],seconds=time.perf_counter()-t))
    print('TARGET COMPLETE',done,round(time.perf_counter()-t,3),'seconds',flush=True)
if __name__=='__main__':main()
