"""Separate post-target diagnostic of all retained terminal candidates."""
import hashlib
import json

import numpy as np

import engine as e
import run


def main():
    audit_plan=json.loads((e.HERE/'terminal-plan.json').read_text(encoding='utf8'))
    for item in audit_plan['inputs']:
        assert e.sha(e.ROOT/item['path'])==item['sha256'],item['path']
    plan=json.loads((e.HERE/'plan.json').read_text(encoding='utf8'))
    pages=dict(zip(plan['page_ids'],run.data(plan)))
    keys=e.keys()
    observer=e.terminal_observer()
    cases=json.loads((e.HERE/'cases.json').read_text(encoding='utf8'))
    rows=[]
    for r in cases:
        if not r['selected_full']:
            continue
        cipher=np.array(pages[r['page']],dtype=np.int64)
        if r['atbash']:
            cipher=28-cipher
        terminal=observer(cipher,np.array(keys[r['a'],r['b']],dtype=np.int64),1,0,len(cipher),200)
        chosen=max(terminal,key=lambda x:x[0])
        assert hashlib.sha256(bytes(chosen[3])).hexdigest()==r['full_sha256']
        assert abs(e.sweep.Q.score_norm(chosen[2])-r['full_score'])<1e-12
        scores=[e.sweep.Q.score_norm(x[2]) for x in terminal]
        rank=max(range(len(terminal)),key=lambda i:scores[i])
        best=terminal[rank]
        rows.append({k:r[k] for k in ['a','b','atbash','page','first_source_ordinal']}|{
            'terminal_hypotheses':len(terminal),'source_selected_score':r['full_score'],
            'best_normalized_terminal_score':scores[rank],
            'best_normalized_cumulative_rank_zero_based':rank,
            'strictly_better_normalized':scores[rank]>r['full_score']+1e-12,
            'source_gate_pass':r['source_gate_pass'],'terminal_gate_pass':scores[rank]>-5.5,
            'best_terminal_indices':list(best[3]),
            'best_terminal_sha256':hashlib.sha256(bytes(best[3])).hexdigest()})
    receipt={'schema':'fibonacci-retained-terminal-audit-v1','terminal_plan_sha256':e.sha(e.HERE/'terminal-plan.json'),
             'timing':'POST-TARGET diagnostic; original source outputs unchanged.',
             'canonical_full_settings':len(rows),'retained_hypotheses':sum(x['terminal_hypotheses'] for x in rows),
             'settings_with_better_normalized_terminal':sum(x['strictly_better_normalized'] for x in rows),
             'source_gate_passes':sum(x['source_gate_pass'] for x in rows),
             'terminal_gate_passes':sum(x['terminal_gate_pass'] for x in rows),
             'expanded_labeled_terminal_gate_passes':10*sum(x['terminal_gate_pass'] for x in rows),
             'new_gate_crossings':sum(x['terminal_gate_pass'] and not x['source_gate_pass'] for x in rows),
             'best_normalized_terminal':max(rows,key=lambda x:(x['best_normalized_terminal_score'],-x['first_source_ordinal'])) if rows else None,
             'rows':rows,'limit':'Only hypotheses retained by the original cumulative beam for strict screen survivors. No normalized intermediate reranking or rejected-screen full decode.'}
    e.write(e.HERE/'terminal-audit.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['rows','best_normalized_terminal']},indent=2),flush=True)


if __name__=='__main__':
    main()
