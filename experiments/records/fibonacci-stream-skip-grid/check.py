"""Independent complete score census, full-survivor decoding and alias recount."""
import hashlib
import json
from collections import Counter

import check_preflight
import engine as e
import independent as ind
import run


def admissible(cipher,key,plain):
    assert len(cipher)==len(plain) and (cipher[0]+key[0])%29==plain[0]
    pointers={0}
    for i in range(1,len(cipher)):
        next_pointers=set()
        for pointer in pointers:
            for skipped in range(4):
                position=pointer+1+skipped
                if position>=len(key) or (cipher[i]+key[position])%29!=plain[i]:
                    continue
                if all((plain[i]-key[j])%29==cipher[i-1] for j in range(pointer+1,position)):
                    next_pointers.add(position)
        pointers=next_pointers
        assert pointers


def main():
    plan=json.loads((e.HERE/'plan.json').read_text(encoding='utf8'))
    for item in plan['inputs']:
        assert e.sha(e.ROOT/item['path'])==item['sha256'],item['path']
    check_preflight.main()
    result=json.loads((e.HERE/'results.json').read_text(encoding='utf8'))
    assert result['plan_sha256']==e.sha(e.HERE/'plan.json')
    assert result['cases_sha256']==e.sha(e.HERE/'cases.json')
    assert result['short_paths_sha256']==e.sha(e.HERE/'short-paths.bin')
    cases=json.loads((e.HERE/'cases.json').read_text(encoding='utf8'))
    binary=(e.HERE/'short-paths.bin').read_bytes()
    pages=dict(zip(plan['page_ids'],run.data(plan)))
    keys=e.keys()
    identities=[(r['a'],r['b'],r['atbash'],r['page']) for r in cases]
    expected={(a,b,atbash,page) for a in range(29) for b in range(29) for atbash in (0,1) for page in plan['page_ids']}
    assert len(identities)==len(set(identities))==92510 and set(identities)==expected
    assert len(binary)==92510*50
    aliases=json.loads((e.HERE/'aliases.json').read_text(encoding='utf8'))
    by_pair={pair:[] for pair in keys}
    for alias in aliases:
        by_pair[alias['canonical_a'],alias['canonical_b']].append(alias)
    assert all(len(v)==10 for v in by_pair.values())
    for index,r in enumerate(cases):
        assert r['short_path_offset']==index*50
        short=list(binary[index*50:index*50+50])
        assert abs(ind.score(e.text(short))-r['screen_score'])<1e-10
        assert r['selected_full']==(r['screen_score']>-6.5)
        page_index=plan['page_ids'].index(r['page'])
        ordinal=min((((((x['a']*29+x['b'])*2+(x['sign']==1))*2+r['atbash'])*55+page_index)*5+x['offset']) for x in by_pair[r['a'],r['b']])
        assert ordinal==r['first_source_ordinal']
    full=[r for r in cases if r['selected_full']]
    assert len(full)==result['canonical_full_confirmations']
    checks=[(r,True) for r in full]
    checks += [(r,False) for r in sorted(cases,key=lambda r:(r['screen_score'],-r['first_source_ordinal']),reverse=True)[:10]]
    best_checks=[]
    for count,(r,whole) in enumerate(checks):
        cipher=[28-c if r['atbash'] else c for c in pages[r['page']]]
        plain,text,used=ind.decode(cipher,keys[r['a'],r['b']],1,0,len(cipher) if whole else 50,200 if whole else 60,e.numeric.gp.IDX_TO_TRANS)
        if whole:
            assert plain==r['full_indices']
            assert hashlib.sha256(bytes(plain)).hexdigest()==r['full_sha256']
            assert abs(ind.score(text)-r['full_score'])<1e-10
            assert r['source_gate_pass']==(ind.score(text)>-5.5)
        else:
            offset=r['short_path_offset']
            assert bytes(plain)==binary[offset:offset+50]
            assert abs(ind.score(text)-r['screen_score'])<1e-10
            best_checks.append({'a':r['a'],'b':r['b'],'atbash':r['atbash'],'page':r['page'],
                                'score':ind.score(text),'first12_indices':plain[:12],
                                'first12_key_positions':used[:12]})
        if count%100==0:
            print('Independent full/top reconstruction',count,'/',len(checks),flush=True)
    labels=json.loads((e.HERE/'source-label-summary.json').read_text(encoding='utf8'))
    hits=json.loads((e.HERE/'source-ordered-hits.json').read_text(encoding='utf8'))
    assert len(labels)==841 and sum(x['screens'] for x in labels)==925100
    assert all(x['screens']==1100 for x in labels)
    assert sum(x['full_confirmations'] for x in labels)==len(full)*10==result['source_labeled_full_confirmations']
    assert sum(x['source_gate_passes'] for x in labels)==len(hits)==10*sum(r['source_gate_pass'] for r in full)
    assert hits==sorted(hits,key=lambda x:x['source_ordinal'])
    assert result['best_screen']==max(cases,key=lambda r:(r['screen_score'],-r['first_source_ordinal']))
    assert result['best_full']==(max(full,key=lambda r:(r['full_score'],-r['first_source_ordinal'])) if full else None)
    assert result['best_labeled_screen']==max((x['best_screen'] for x in labels),key=lambda r:(r['screen_score'],-r['source_ordinal']))
    terminal_count=0
    if (e.HERE/'terminal-audit.json').exists():
        terminal=json.loads((e.HERE/'terminal-audit.json').read_text(encoding='utf8'))
        assert terminal['terminal_plan_sha256']==e.sha(e.HERE/'terminal-plan.json')
        assert len(terminal['rows'])==len(full)
        for r in terminal['rows']:
            cipher=[28-c if r['atbash'] else c for c in pages[r['page']]]
            key=keys[r['a'],r['b']]
            witness=r['best_terminal_indices']
            assert hashlib.sha256(bytes(witness)).hexdigest()==r['best_terminal_sha256']
            assert abs(ind.score(e.text(witness))-r['best_normalized_terminal_score'])<1e-10
            admissible(cipher,key,witness)
            assert r['terminal_gate_pass']==(ind.score(e.text(witness))>-5.5)
            terminal_count+=1
        assert terminal['terminal_gate_passes']==sum(x['terminal_gate_pass'] for x in terminal['rows'])
    receipt={'schema':'fibonacci-target-independent-check-v1','canonical_settings_recounted':92510,
             'expanded_source_labels_recounted':925100,'all_short_outputs_independently_rescored':92510,
             'all_full_survivors_independently_decoded':len(full),'best_short_paths_independently_decoded':10,
             'source_gate_passes':sum(r['source_gate_pass'] for r in full),
             'terminal_best_witnesses_independently_rescored_and_admissible':terminal_count,
             'alias_counts_and_original_tied_label_order_match':True,'best_short_checks':best_checks,
             'limit':'Verifies this bounded source computation and alias expansion; no plaintext or global statistical calibration.'}
    e.write(e.HERE/'independent-check.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='best_short_checks'},indent=2),flush=True)


if __name__=='__main__':
    main()
