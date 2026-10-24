"""Measured funnel and one actual admissible selected-path skip."""
import json

import engine as e
import independent as ind
import run


def main():
    result=json.loads((e.HERE/'results.json').read_text(encoding='utf8'))
    plan=json.loads((e.HERE/'plan.json').read_text(encoding='utf8'))
    pages=dict(zip(plan['page_ids'],run.pages(plan)))
    full=[r for r in json.loads((e.HERE/'cases.json').read_text(encoding='utf8')) if r['selected_full']]
    selected=None
    for row in sorted(full,key=lambda r:r['full_score'],reverse=True):
        cipher=[28-c if row['atbash'] else c for c in pages[row['page']]]
        plain,text,used=ind.decode(cipher,row['signed_slope'],row['signed_intercept'],len(cipher),300,e.source.gp.IDX_TO_TRANS)
        skip=next((i for i in range(1,len(used)) if used[i]>used[i-1]+1),None)
        if skip is not None:
            selected=(row,cipher,plain,used,skip)
            break
    assert selected is not None
    row,cipher,plain,used,i=selected
    assert (cipher[i-1]-cipher[i])%29==row['signed_slope']
    receipt={'selection':'Highest-scoring returned complete path containing a skip; first such skip. Illustration only.',
             'setting':{k:row[k] for k in ['mode','source_index','page','sign','atbash']},
             'rune_position_zero_based':i,'previous_transformed_cipher_index':cipher[i-1],
             'current_transformed_cipher_index':cipher[i],'signed_slope':row['signed_slope'],
             'key_pointer_before':used[i-1],'key_pointer_after':used[i],
             'candidate_plain_index':plain[i],'limit':'Admissible candidate path, not certified plaintext or inferred real skip.'}
    e.write(e.HERE/'figure-receipt.json',receipt)
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="580" height="650" viewBox="0 0 580 650" role="img" aria-labelledby="title desc">
<title id="title">Page-assigned ramps with conditional skips</title>
<desc id="desc">660short screens select7whole-page checks; none passes the source final gate. In an actual candidate path a single key can be rejected when the adjacent transformed ciphertext difference equals the signed ramp step. Controls distinguish score passage and exact recovery.</desc>
<rect width="580" height="650" fill="white"/>
<g font-family="Arial,sans-serif" fill="#252525">
<text x="20" y="35" font-size="24">Page-number ramps with conditional skips</text>
<text x="20" y="68" font-size="20">Three assigned rules · 55 pages · signs · Atbash</text>
<rect x="20" y="91" width="540" height="59" rx="6" fill="#eeeeee"/>
<text x="36" y="129" font-size="25">660 short screens</text>
<text x="280" y="180" font-size="24">↓</text>
<rect x="20" y="194" width="540" height="59" rx="6" fill="#eeeeee"/>
<text x="36" y="232" font-size="25">7 whole-page checks</text>
<text x="280" y="283" font-size="24">↓</text>
<rect x="20" y="297" width="540" height="59" rx="6" fill="#dddddd"/>
<text x="36" y="335" font-size="25">0 pass the final source score gate</text>
<text x="20" y="395" font-size="22">An admissible skip in a selected path</text>
<text x="20" y="428" font-size="20">{row['page'].upper()}, rune {i}: transformed indices {cipher[i-1]} → {cipher[i]}</text>
<text x="20" y="463" font-size="24">({cipher[i-1]} − {cipher[i]}) mod 29 = {row['signed_slope']}</text>
<text x="20" y="496" font-size="20">That equals the signed key step: one skip allowed.</text>
<text x="20" y="535" font-size="20">Controls: 98/112 exact; 112/112 pass score gates.</text>
<text x="20" y="567" font-size="20">These repeat eight step/known-reading situations.</text>
<text x="20" y="616" font-size="20">Candidate path only; no plaintext certified.</text>
</g></svg>'''
    (e.HERE/'page-ramp-search.svg').write_text(svg+'\n',encoding='utf8',newline='\n')
    print('Figure actual source-selected path',receipt)


if __name__=='__main__':
    main()
