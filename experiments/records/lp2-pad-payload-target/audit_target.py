"""Independent saved-witness validation; no source target sweep or shuffle rerun."""
import sys,json,math
from pathlib import Path
sys.dont_write_bytecode=True
import replay as r
from audit_control import quad_table,score,beam_trace

def verify_source():
    for item in r.read('inputs-frozen.json')['staged_source']:
        assert r.sha((r.H/item['path']).read_bytes())==item['sha256'],item['path']

def path_for(C,P,K,sign,end):
    assert P[0]==(C[0]+sign*K[0])%29
    states={0:[0]}
    for i,p in enumerate(P[1:],1):
        nxt={}
        for previous,trace in states.items():
            for skipped in range(4):
                j=previous+1+skipped
                if p!=(C[i]+sign*K[j])%29:continue
                if any((p-sign*K[k])%29!=C[i-1] for k in range(previous+1,j)):continue
                if j not in nxt:nxt[j]=trace+[j]
        assert nxt,(i,'no admissible path');states=nxt
    assert end in states
    return states[end]

def main():
    r.verify=verify_source
    m,V,_,C=r.instrument();result=r.read('target-results.json');table,floor=quad_table()
    labels=[m.gp.IDX_TO_TRANS[i] for i in range(29)];checks=[]
    for w in result['new_witnesses']:
        P=w['plain_idx'];assert len(P)==256 and ''.join(labels[p] for p in P)==w['translit']
        total,norm=score(w['translit'],table,floor)
        assert abs(total-w['beam_score'])<1e-8 and abs(norm-w['score'])<1e-10
        used=path_for(C,P,V[w['key_variant']],w['sign'],w['ptr_end'])
        checks.append(dict(key_variant=w['key_variant'],sign=w['sign'],length=len(P),indices_sha256=r.ih(P),accepted_key_indices=used,total_skips=used[-1]-255,raw_table_cumulative=total,raw_table_normalized=norm))
    groups={}
    for key in r.KEYS:
        for sign in r.SIGNS:groups.setdefault(r.ih([(sign*x)%29 for x in V[key]]),[]).append([key,sign])
    assert len(groups)==6
    for group in groups.values():
        matched=[w for w in result['new_witnesses'] if [w['key_variant'],w['sign']] in group]
        assert all(all(w[k]==matched[0][k] for k in ['plain_idx','score','beam_score','ptr_end','translit']) for w in matched)
    old=json.loads((r.LP/'analysis/round16/F-01/results.json').read_text())
    expected=[]
    for target in r.OLDTARGETS[:-1]+[r.TARGET,r.OLDTARGETS[-1]]:
        for key in r.KEYS:
            for sign in r.SIGNS:
                rows=result['new_labelled_rows'] if target==r.TARGET else old['results']
                row=next(w for w in rows if w['target']==target and w['key_variant']==key and w['sign']==sign)
                expected.append({k:row[k] for k in ['target','target_len','key_variant','sign','score','head','above_bar']})
    expected.sort(key=lambda row:-row['score'])
    assert len(expected)==48
    assert all(all(got[k]==want[k] for k in want) for got,want in zip(result['combined_labelled_rows'],expected))
    newpanels=[p for p in result['selected_null_panels'] if p['target']==r.TARGET]
    assert len(newpanels)==2 and newpanels[0]['null_scores']==newpanels[1]['null_scores']
    assert sum(p['actual_new_decodes'] for p in result['selected_null_panels'])==result['actual_new_null_decodes']==200
    for row,panel in zip(result['combined_labelled_rows'][:5],result['selected_null_panels']):
        if panel['target']==r.TARGET:
            values=panel['null_scores'];assert len(values)==200
            assert abs(sum(values)/200-row['null_mean'])<1e-10 and max(values)==row['null_max']
        else:
            oldrow=next(w for w in old['results'] if all(w[k]==row[k] for k in ['target','key_variant','sign']))
            assert all(row[k]==oldrow[k] for k in ['null_mean','null_max','beats_null_by','hit'])
        assert row['hit']==(row['score']>=-5.5 and row['score']>=row['null_max']+.5)
    assert not result['any_source_hit'] and not any(row['above_bar'] for row in result['new_labelled_rows'])
    best=max(result['new_witnesses'],key=lambda w:w['score']);trace=next(c['accepted_key_indices'] for c in checks if c['key_variant']==best['key_variant'] and c['sign']==best['sign'])
    beams,_=beam_trace(C,V[best['key_variant']],best['sign'],labels,best['plain_idx'],trace)
    assert list(beams[0][3])==best['plain_idx'] and beams[0][1]==best['ptr_end']
    bestnorm=max(enumerate(beams),key=lambda pair:score(pair[1][2],table,floor)[1])
    receipt=dict(target_results_sha256=r.sha((r.H/'target-results.json').read_bytes()),all_eight_witnesses_checked=True,witnesses=checks,signed_key_alias_groups=list(groups.values()),combined48_stable_order_verified=True,selected5_null_receipts_verified=True,actual_new_null_decodes=200,source_selected_best=dict(key_variant=best['key_variant'],sign=best['sign'],score=best['score']),post_target_best_case_terminal_audit=dict(retained_candidates=len(beams),best_normalized_cumulative_rank_zero=bestnorm[0],best_normalized_score=score(bestnorm[1][2],table,floor)[1],source_winner_reproduced=True),limits='This checks saved outputs, source ranking and admissible paths. It does not establish plaintext, exact decoder power or a whole-search significance level. Only the selected best new case receives the separate retained-terminal diagnostic.',source_verification='All frozen staged scientific bytes checked. Original external record metadata is historical provenance; its later family-only edit is not a scientific dependency.')
    r.write('independent-target-audit.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['witnesses']},indent=2))
if __name__=='__main__':main()
