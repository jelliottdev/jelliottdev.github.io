"""Canonical execution of the exact finite source Fibonacci skip grid."""
import hashlib
import json
import time

import numpy as np

import engine as e


def data(plan):
    from run_stats import load_pages
    pages=load_pages()[:-2]
    assert len(pages)==55 and max(map(len,pages))==277
    for page,indices in zip(plan['page_ids'],pages):
        text=(e.ROOT/'text'/f'{page}.txt').read_text(encoding='utf8')
        assert e.numeric.gp.runes_to_indices(text)==indices
    return pages


def main():
    plan=json.loads((e.HERE/'plan.json').read_text(encoding='utf8'))
    for item in plan['inputs']:
        assert e.sha(e.ROOT/item['path'])==item['sha256'],item['path']
    pages=data(plan)
    keys=e.keys()
    aliases=json.loads((e.HERE/'aliases.json').read_text(encoding='utf8'))
    by_pair={pair:[] for pair in keys}
    for alias in aliases:
        by_pair[alias['canonical_a'],alias['canonical_b']].append(alias)
    rows=[]
    short_paths=bytearray()
    started=time.perf_counter()
    for (a,b),values in keys.items():
        key=np.array(values,dtype=np.int64)
        for atbash in (0,1):
            for page_ordinal,cipher_values in enumerate(pages):
                cipher=np.array(cipher_values,dtype=np.int64)
                if atbash:
                    cipher=28-cipher
                short=e.sweep.beam(cipher,key,1,0,50,60)
                assert len(short)==50
                score=e.sweep.Q.score_norm(e.text(short))
                row={'a':a,'b':b,'atbash':atbash,'page':plan['page_ids'][page_ordinal],
                     'screen_score':score,'short_path_offset':len(short_paths),
                     'selected_full':score>-6.5}
                short_paths.extend(short)
                if row['selected_full']:
                    full=e.sweep.beam(cipher,key,1,0,len(cipher),200)
                    row.update(full_indices=full,full_score=e.sweep.Q.score_norm(e.text(full)),
                               full_sha256=hashlib.sha256(bytes(full)).hexdigest())
                    row['source_gate_pass']=row['full_score']>-5.5
                row['first_source_ordinal']=min(e.source_ordinal(x['a'],x['b'],x['sign'],atbash,page_ordinal,x['offset']) for x in by_pair[a,b])
                rows.append(row)
        if (a*29+b)%100==0:
            print('Completed canonical key',a,b,flush=True)
    assert len(rows)==92510 and len(short_paths)==4625500
    e.compact(e.HERE/'cases.json',rows)
    (e.HERE/'short-paths.bin').write_bytes(short_paths)
    # Expand aliases in the historical ordinal, preserving tied-label semantics.
    per_source={pair:{'a':pair[0],'b':pair[1],'screens':0,'full_confirmations':0,
                      'source_gate_passes':0,'best_screen':None} for pair in keys}
    labelled_hits=[]
    for row in rows:
        page_ordinal=plan['page_ids'].index(row['page'])
        for alias in by_pair[row['a'],row['b']]:
            label={k:alias[k] for k in ['a','b','sign','offset']}
            label.update(atbash=row['atbash'],page=row['page'],screen_score=row['screen_score'],
                         source_ordinal=e.source_ordinal(alias['a'],alias['b'],alias['sign'],row['atbash'],page_ordinal,alias['offset']))
            summary=per_source[alias['a'],alias['b']]
            summary['screens']+=1
            summary['full_confirmations']+=int(row['selected_full'])
            summary['source_gate_passes']+=int(row.get('source_gate_pass',False))
            previous=summary['best_screen']
            if previous is None or (label['screen_score'],-label['source_ordinal'])>(previous['screen_score'],-previous['source_ordinal']):
                summary['best_screen']=label
            if row.get('source_gate_pass',False):
                labelled_hits.append(label|{'full_score':row['full_score'],'full_sha256':row['full_sha256']})
    assert all(x['screens']==1100 for x in per_source.values())
    e.compact(e.HERE/'source-label-summary.json',list(per_source.values()))
    e.compact(e.HERE/'source-ordered-hits.json',sorted(labelled_hits,key=lambda x:x['source_ordinal']))
    full=[r for r in rows if r['selected_full']]
    result={'schema':'fibonacci-canonical-target-v1','plan_sha256':e.sha(e.HERE/'plan.json'),
            'canonical_screens':len(rows),'source_labeled_screens':len(rows)*10,
            'canonical_full_confirmations':len(full),'source_labeled_full_confirmations':len(full)*10,
            'canonical_source_gate_passes':sum(r['source_gate_pass'] for r in full),
            'source_labeled_gate_passes':len(labelled_hits),
            'best_screen':max(rows,key=lambda r:(r['screen_score'],-r['first_source_ordinal'])),
            'best_full':max(full,key=lambda r:(r['full_score'],-r['first_source_ordinal'])) if full else None,
            'best_labeled_screen':max((x['best_screen'] for x in per_source.values()),key=lambda r:(r['screen_score'],-r['source_ordinal'])),
            'cases_sha256':e.sha(e.HERE/'cases.json'),'short_paths_sha256':e.sha(e.HERE/'short-paths.bin'),
            'elapsed_seconds':time.perf_counter()-started,
            'limit':'Canonical computation represents exact aliases, not independent new methods. Only screen survivors were fully decoded; source score gates are not plaintext validation.'}
    e.write(e.HERE/'results.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['best_screen','best_full','best_labeled_screen']},indent=2),flush=True)


if __name__=='__main__':
    main()
