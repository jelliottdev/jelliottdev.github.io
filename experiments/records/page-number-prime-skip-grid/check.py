"""Independent complete small grid, source formula/mapping and gate checks."""
import hashlib
import json

import check_controls
import engine as e
import independent as ind
import run


def primes():
    out=[]
    for n in range(2,110):
        if all(n%d for d in range(2,int(n**.5)+1)):
            out.append(n)
    assert len(out)==29
    return out


def phi(n):
    import math
    return sum(math.gcd(n,k)==1 for k in range(1,n+1))


def main():
    plan=json.loads((e.HERE/'plan.json').read_text(encoding='utf8'))
    for item in plan['inputs']:
        assert e.sha(e.ROOT/item['path'])==item['sha256'],item['path']
    check_controls.main()
    pages=dict(zip(plan['page_ids'],run.pages(plan)))
    cases=json.loads((e.HERE/'cases.json').read_text(encoding='utf8'))
    result=json.loads((e.HERE/'results.json').read_text(encoding='utf8'))
    assert result['plan_sha256']==e.sha(e.HERE/'plan.json') and result['cases_sha256']==e.sha(e.HERE/'cases.json')
    ids=[(r['mode'],r['source_index'],r['sign'],r['atbash']) for r in cases]
    assert len(ids)==len(set(ids))==660
    assert set(ids)=={(m,i,s,a) for m in ['prime','totient','3301xor'] for i in range(55) for s in (-1,1) for a in (0,1)}
    full=[]
    for r in cases:
        i=r['source_index']
        assert r['page']==f'lp2-{i if i<50 else i+1:02d}'
        intercept=primes()[i%29] if r['mode']=='prime' else phi(i+2) if r['mode']=='totient' else i
        step=24 if r['mode']=='3301xor' else 1
        expected=[(intercept+step*j)%29 for j in range(1124)]
        assert hashlib.sha256(bytes(expected)).hexdigest()==r['key_sha256']
        assert (r['signed_slope'],r['signed_intercept'])==(r['sign']*step%29,r['sign']*intercept%29)
        cipher=[28-c if r['atbash'] else c for c in pages[r['page']]]
        short,text,used=ind.decode(cipher,r['signed_slope'],r['signed_intercept'],50,60,e.source.gp.IDX_TO_TRANS)
        assert short==r['screen_indices'] and abs(ind.score(text)-r['screen_score'])<1e-10
        assert r['selected_full']==(r['screen_score']>-6.5)
        if r['selected_full']:
            plain,text,used=ind.decode(cipher,r['signed_slope'],r['signed_intercept'],len(cipher),300,e.source.gp.IDX_TO_TRANS)
            assert plain==r['full_indices'] and hashlib.sha256(bytes(plain)).hexdigest()==r['full_sha256']
            assert abs(ind.score(text)-r['full_score'])<1e-10 and r['source_gate_pass']==(r['full_score']>-5.5)
            full.append(r)
    assert len(full)==result['full_confirmations'] and sum(r['source_gate_pass'] for r in full)==result['source_gate_passes']
    assert max(cases,key=lambda r:r['screen_score'])==result['best_screen']
    assert (max(full,key=lambda r:r['full_score']) if full else None)==result['best_full']
    terminal=json.loads((e.HERE/'terminal-audit.json').read_text(encoding='utf8'))
    assert terminal['terminal_plan_sha256']==e.sha(e.HERE/'terminal-plan.json')
    assert terminal['full_settings']==len(full)
    assert all(r['ordered_independent_terminal_parity'] for r in terminal['rows'])
    report={'schema':'page-ramp-independent-target-v1','independent_short_reconstructions':660,
            'independent_full_reconstructions':len(full),'source_key_formula_and_page_mapping_checks':660,
            'source_gate_passes':result['source_gate_passes'],
            'retained_terminal_hypotheses_independently_reconstructed':terminal['retained_terminal_hypotheses'],
            'atbash_off_rigid_overlap':330,'atbash_on_rigid_overlap_not_established_by_progressive_record':330,
            'limit':'Verifies finite source gates/paths; no correct-reading or complete-search statistical inference.'}
    e.write(e.HERE/'independent-check.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
