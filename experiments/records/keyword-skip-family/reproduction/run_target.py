"""Fixed source-full keyword grid; creates new outputs, never overwrites evidence."""
import hashlib,json,time
from pathlib import Path
import numpy as np
import engine as e
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    assert not p.exists(),p
    p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf8',newline='\n')
def pages():
    env={'gp':e.gp,'KRIS':str(e.LP/'data/krisyotam_runes.txt')}
    e.definitions(e.LP/'analysis/run_stats.py',['load_pages'],env)
    return env['load_pages']()[:-2]
def main():
    protocol=json.loads((H/'target-protocol-frozen.json').read_bytes())
    for p,h in protocol['pins'].items():assert sha(H/p)==h,p
    assert not (H/'results.json').exists()
    source_pages=pages();assert len(source_pages)==55
    words=e.words();desc=[(j,label,sign,int(atb),off) for j,(label,key) in enumerate(words) for sign in (-1,1) for atb in (False,True) for off in range(len(key))]
    assert len(desc)==11256
    scores=np.empty((55,len(desc)),np.float64);selections=[];full=[];page_best=[]
    t=time.perf_counter()
    for page,raw in enumerate(source_pages):
        ct=np.asarray(raw,np.int64);cursor=[0]
        def capture(c,key,sign,offset,length,width):
            if width==300:
                ix=cursor[0];j,label,s,a,o=desc[ix];assert (s,o)==(sign,offset)
                out=e.beam(c,key,sign,offset,length,width)
                scores[page,ix]=e.Q.score_norm(e.text(out));cursor[0]+=1
                return out
            assert width==500
            j,label,s,a,_=desc[cursor[0]-1];assert s==sign
            paths,cumulative,ptr,latin=e.beam(c,key,sign,offset,length,width,True)
            norms=np.asarray([e.Q.score_norm(e.text(p)) for p in paths]);best=int(np.argmax(norms))
            full.append(dict(page=page,keyword_index=j,keyword=label,sign=sign,atbash=a,phase=int(offset),score=float(norms[0]),plain=paths[0].tolist(),source_gate=bool(norms[0]>-5.5),terminal_count=len(paths),terminal_scores=norms.tolist(),best_normalized_terminal_rank=best+1,best_normalized_terminal_score=float(norms[best]),best_normalized_terminal=paths[best].tolist(),best_normalized_gate=bool(norms[best]>-5.5)))
            return paths[0].astype(np.int64).tolist()
        e.env['beam']=capture
        hits,best=e.env['attack_page_keyword_fast'](ct,words)
        assert cursor[0]==len(desc)
        page_best.append(dict(page=page,length=len(raw),best_screen=best,source_hits=hits))
        ix=0
        for j,(label,key) in enumerate(words):
            for sign in (-1,1):
                for atb in (False,True):
                    block=scores[page,ix:ix+len(key)];phase=int(np.argmax(block));selections.append((phase,float(block[phase])));ix+=len(key)
        print('Target page',page,'/54 screens',cursor[0],'best',best,'fulls',len(full),'elapsed',round(time.perf_counter()-t,3),flush=True)
    assert scores.size==619080 and len(selections)==137060
    path=H/'screen-scores.npy';assert not path.exists();np.save(path,scores)
    path=H/'phase-selections.npy';assert not path.exists();np.save(path,np.asarray(selections,np.float64).reshape(55,623,2,2,2))
    save(H/'full-survivors.json',full)
    # Reconstruct the best screen output after selection as an independently checkable witness.
    flat=int(np.argmax(scores));page,ix=np.unravel_index(flat,scores.shape);j,label,sign,atb,off=desc[ix]
    ct=np.asarray(source_pages[page],np.int64);ct=28-ct if atb else ct;key=e.env['tile_key'](words[j][1],len(ct)*4+64);out=e.beam(ct,key,sign,off,min(90,len(ct)),300)
    save(H/'results.json',dict(protocol_sha256=sha(H/'target-protocol-frozen.json'),screens=int(scores.size),phase_selections=len(selections),full_promotions=len(full),source_hits=sum(x['source_gate'] for x in full),normalized_terminal_hits=sum(x['best_normalized_gate'] for x in full),page_results=page_best,best_screen=dict(page=int(page),keyword_index=j,keyword=label,sign=sign,atbash=atb,phase=off,score=float(scores[page,ix]),plain=out),page_array_sha256=[hashlib.sha256(np.asarray(p,dtype='<i8').tobytes()).hexdigest() for p in source_pages],artifacts={p:sha(H/p) for p in ('screen-scores.npy','phase-selections.npy','full-survivors.json')},seconds=time.perf_counter()-t,purpose=protocol['purpose']))
    print('TARGET COMPLETE',round(time.perf_counter()-t,3),'seconds',flush=True)
if __name__=='__main__':main()
