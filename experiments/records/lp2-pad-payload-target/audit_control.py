"""Independent raw-table scorer and beam/truth audit of the one failed plant."""
import sys,math,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
import replay as r
def quad_table():
    counts={};total=0
    for line in (r.LP/'data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        gram,count=line.split();counts[gram]=int(count);total+=int(count)
    logtotal=math.log10(total)
    return {g:math.log10(n)-logtotal for g,n in counts.items()},math.log10(.01)-logtotal
def score(text,d,floor):
    values=[d.get(text[i:i+4],floor) for i in range(len(text)-3)]
    return sum(values),sum(values)/len(values)
def beam_trace(C,K,sign,labels,truth,used):
    d,floor=quad_table();p=(C[0]+sign*K[0])%29;beams=[(0.,0,labels[p],(p,))];ranks=[0]
    for i in range(1,len(C)):
        nxt=[]
        for cumulative,last,text,indices in beams:
            for skipped in range(4):
                j=last+1+skipped
                p=(C[i]+sign*K[j])%29
                if any((p-sign*K[k])%29!=C[i-1] for k in range(last+1,j)):continue
                expanded=text+labels[p]
                delta=sum(d.get(expanded[k:k+4],floor) for k in range(max(0,len(text)-3),len(expanded)-3))
                nxt.append((cumulative+delta,j,expanded,indices+(p,)))
        nxt.sort(key=lambda row:row[0],reverse=True);beams=nxt[:400]
        matches=[j for j,row in enumerate(beams) if row[1]==used[i] and row[3]==tuple(truth[:i+1])]
        ranks.append(min(matches) if matches else None)
    return beams,ranks
def main():
    m,V,_,_=r.instrument();base=m.sk.eng_to_idx(r.source_plain());P=(base*((256+len(base)-1)//len(base)))[:256];K=V['lp2_rev'];sign=1
    C,skips,used=m.sk.encipher_keyskip(P,K,sign=sign,supp=.83,seed=3301)
    source=m.sk.beam_decode(C,K,sign=sign,o=0,beam_w=400,max_skip=3)
    labels=[m.gp.IDX_TO_TRANS[i] for i in range(29)];beams,ranks=beam_trace(C,K,sign,labels,P,used)
    assert list(beams[0][3])==source['plain_idx'] and beams[0][1]==source['ptr_end']
    assert abs(beams[0][0]-source['beam_score'])<1e-8
    table,floor=quad_table();truth_text=''.join(labels[i] for i in P)
    truth_total,truth_norm=score(truth_text,table,floor);chosen_total,chosen_norm=score(source['translit'],table,floor)
    assert abs(chosen_norm-source['score'])<1e-10
    truth_rows=[(i,row) for i,row in enumerate(beams) if row[3]==tuple(P) and row[1]==used[-1]]
    assert truth_rows
    truth_rank,true=truth_rows[0];assert abs(true[0]-truth_total)<1e-8
    mismatch=[dict(position_zero=i,position_one=i+1,expected_index=a,chosen_index=b,expected_label=labels[a],chosen_label=labels[b]) for i,(a,b) in enumerate(zip(P,source['plain_idx'])) if a!=b]
    best_normalized=max(enumerate(beams),key=lambda pair:score(pair[1][2],table,floor)[1])
    result=dict(control_results_sha256=r.sha((r.H/'control-results.json').read_bytes()),case=dict(key_variant='lp2_rev',sign=1),mismatches=mismatch,true_plaintext_sha256=r.ih(P),chosen_plaintext_sha256=r.ih(source['plain_idx']),true_path_admissible=True,true_max_skipped=max(skips),true_ptr_end=used[-1],chosen_ptr_end=source['ptr_end'],true_prefix_survived_every_step=all(x is not None for x in ranks),truth_retained_rank_zero_based=ranks,terminal_beam_count=len(beams),truth_terminal_rank_zero_based=truth_rank,chosen_cumulative=chosen_total,truth_cumulative=truth_total,chosen_normalized=chosen_norm,truth_normalized=truth_norm,selected_strictly_higher_cumulative=chosen_total>truth_total,selected_strictly_higher_normalized=chosen_norm>truth_norm,cumulative_tie=abs(chosen_total-truth_total)<1e-10,best_normalized_terminal_cumulative_rank=best_normalized[0],best_normalized_terminal_score=score(best_normalized[1][2],table,floor)[1],interpretation='The valid true path survives; source cumulative-score preference selects a different3rune output. This is not an invalid key/skip plant, tie or pruning loss. Exact recovery gate remains failed; source English-score bar still passes.',method='Rawquadgram file parsed independently; independent state expansion preserves source admissibility, stable cumulative ordering and beam400. No T5targetdecode or frozen-byte change.')
    r.write('control-failure-audit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['truth_retained_rank_zero_based']},ensure_ascii=True,indent=2))
if __name__=='__main__':main()
