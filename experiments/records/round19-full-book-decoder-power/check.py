"""Independent row and gate recount for Round 19's full-book control."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

H=Path(__file__).resolve().parent


def keyed(rows):
    return {(x['mode'],x['seed'],x['wrong_key']):x for x in rows}


def main():
    plan=json.loads((H/'plan.json').read_text(encoding='utf-8'))
    for rel,expected in plan['source_files_sha256'].items():
        assert hashlib.sha256((H/'source'/rel).read_bytes()).hexdigest()==expected,rel
    source=json.loads((H/'source'/plan['archived_output']).read_text(encoding='utf-8'))
    fresh=json.loads((H/'replayed-out_book.json').read_text(encoding='utf-8'))
    assert source['stage']==fresh['stage']=='book'
    assert source['L']==fresh['L']==plan['grid']['length']
    assert source['reference_round18_L2']==fresh['reference_round18_L2']
    expected={(m,s,False) for m in plan['grid']['decoder_modes']
              for s in plan['grid']['correct_seeds']}
    expected|={(m,plan['grid']['wrong_key_seed'],True) for m in plan['grid']['decoder_modes']}
    archived,frozen=keyed(source['rows']),keyed(fresh['rows'])
    assert set(archived)==set(frozen)==expected
    for index in expected:
        a,b=archived[index],frozen[index]
        assert {k:v for k,v in a.items() if k!='secs'}=={k:v for k,v in b.items() if k!='secs'},index
        assert all(isinstance(x.get('secs'),(int,float)) and x['secs']>0 for x in (a,b))
    summary=[]
    for mode in plan['grid']['decoder_modes']:
        plants=[frozen[(mode,s,False)] for s in plan['grid']['correct_seeds']]
        wrong=frozen[(mode,plan['grid']['wrong_key_seed'],True)]
        passed=[x['score']>=plan['source_gate']['score_at_least'] and
                x['recovery']>=plan['source_gate']['rune_recovery_at_least'] for x in plants]
        summary.append({'mode':mode,'correct_seeds':len(plants),'all_correct_keys_pass_source_gate':all(passed),
                        'median_correct_score':statistics.median(x['score'] for x in plants),
                        'median_correct_recovery':statistics.median(x['recovery'] for x in plants),
                        'wrong_key_score':wrong['score'],'wrong_key_recovery':wrong['recovery'],
                        'median_correct_skips':statistics.median(x['n_skips_inferred'] for x in plants),
                        'wrong_key_skips':wrong['n_skips_inferred']})
    assert all(x['all_correct_keys_pass_source_gate'] for x in summary)
    result={'schema':'liberpedia-round19-i1-fullbook-check-v1',
            'plan_sha256':hashlib.sha256((H/'plan.json').read_bytes()).hexdigest(),
            'source_id':'I1-08','length':source['L'],'rows_exact_non_timing_match':len(expected),
            'modes':summary,
            'limits':'Synthetic known-plaintext/key decoder power only; no LP2 key exclusion or language-model generalization.'}
    path=H/'results.json'
    if path.exists():
        assert result==json.loads(path.read_text(encoding='utf-8'))
    else:
        path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS',len(expected),'exact non-timing source rows,',len(summary),'mode gates')


if __name__=='__main__':
    main()
