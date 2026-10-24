"""Post-target source terminal audit, with independent linear-beam parity."""
import hashlib
import json

import numpy as np

import engine as e
import independent as ind
import run


def main():
    plan=json.loads((e.HERE/'terminal-plan.json').read_text(encoding='utf8'))
    for item in plan['inputs']:
        assert e.sha(e.ROOT/item['path'])==item['sha256'],item['path']
    target_plan=json.loads((e.HERE/'plan.json').read_text(encoding='utf8'))
    pages=dict(zip(target_plan['page_ids'],run.pages(target_plan)))
    cases=json.loads((e.HERE/'cases.json').read_text(encoding='utf8'))
    observer=e.terminal_observer()
    rows=[]
    for r in cases:
        if not r['selected_full']:
            continue
        cipher=[28-c if r['atbash'] else c for c in pages[r['page']]]
        key=e.source.page_seeded_stream(r['source_index'],1124,r['mode'])
        states=observer(np.array(cipher,dtype=np.int64),np.array(key,dtype=np.int64),r['sign'],0,len(cipher),300)
        reconstructed=ind.decode(cipher,r['signed_slope'],r['signed_intercept'],len(cipher),300,e.source.gp.IDX_TO_TRANS,terminal=True)
        assert len(states)==len(reconstructed)
        for source,check in zip(states,reconstructed):
            assert abs(source[0]-check[0])<1e-10 and source[1:]==check[1:4]
        chosen=max(states,key=lambda x:x[0])
        assert list(chosen[3])==r['full_indices']
        scores=[ind.score(x[2]) for x in states]
        rank=max(range(len(states)),key=lambda i:scores[i])
        best=states[rank]
        rows.append({k:r[k] for k in ['mode','source_index','page','sign','atbash']}|{
            'terminal_hypotheses':len(states),'ordered_independent_terminal_parity':True,
            'source_selected_score':r['full_score'],'best_normalized_terminal_score':scores[rank],
            'best_normalized_cumulative_rank_zero_based':rank,
            'strictly_better_normalized':scores[rank]>r['full_score']+1e-12,
            'terminal_gate_pass':scores[rank]>-5.5,'best_terminal_indices':list(best[3]),
            'best_terminal_sha256':hashlib.sha256(bytes(best[3])).hexdigest()})
    report={'schema':'page-ramp-terminal-audit-v1','terminal_plan_sha256':e.sha(e.HERE/'terminal-plan.json'),
            'timing':'POST-TARGET diagnostic; source-selected outputs unchanged.',
            'full_settings':len(rows),'retained_terminal_hypotheses':sum(r['terminal_hypotheses'] for r in rows),
            'settings_with_better_normalized_terminal':sum(r['strictly_better_normalized'] for r in rows),
            'terminal_gate_passes':sum(r['terminal_gate_pass'] for r in rows),
            'all_ordered_terminal_hypotheses_independently_reconstructed':True,
            'best_normalized_terminal':max(rows,key=lambda r:r['best_normalized_terminal_score']) if rows else None,
            'rows':rows,'limit':'Only retained terminal candidates of the7source-selected full decodes; no new ranking rule at intermediate steps or full decoding of rejected screens.'}
    e.write(e.HERE/'terminal-audit.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['rows','best_normalized_terminal']},indent=2))


if __name__=='__main__':
    main()
