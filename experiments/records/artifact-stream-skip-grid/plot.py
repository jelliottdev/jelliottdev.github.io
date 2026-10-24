"""Show the finite screen funnel and one actual selected-path skip constraint."""
import json
from pathlib import Path

import check
import run

HERE = Path(__file__).resolve().parent


def main():
    result = json.loads((HERE / 'results.json').read_text(encoding='utf8'))
    best = result['best_full']
    source, _, _, streams, pages = run.load()
    keys = {x['name']: x['key'] for x in streams}
    page_map = dict(zip(run.PLAN['page_ids'], pages))
    cipher = [(28-c if best['atbash'] else c) for c in page_map[best['page']]]
    key = keys[best['stream']]
    plain, _, used = check.decode(cipher, key, best['sign'], best['offset'], len(cipher), 300, source.gp.IDX_TO_TRANS)
    assert plain == best['full_indices']
    i = next(i for i in range(1, len(used)) if used[i] > used[i-1]+1)
    rejected_position = used[i-1]+1
    rejected = key[rejected_position]
    accepted = key[used[i]]
    assert (plain[i] - best['sign']*rejected) % 29 == cipher[i-1]
    assert (plain[i] - best['sign']*accepted) % 29 == cipher[i]
    receipt = {'selection':'Highest normalized complete-page score among the 194 source-selected confirmations; first skip in its selected path.',
               'setting':{k:best[k] for k in ['stream','page','sign','atbash','offset']},
               'rune_position_zero_based':i, 'candidate_plain_index':plain[i],
               'previous_transformed_cipher_index':cipher[i-1], 'current_transformed_cipher_index':cipher[i],
               'rejected_key_position':rejected_position,'rejected_key_value':rejected,
               'accepted_key_position':used[i],'accepted_key_value':accepted,
               'complete_page_score':best['full_score'], 'source_final_threshold':-5.5,
               'limit':'An admissible candidate path, not certified plaintext or an inferred real skip.'}
    (HERE/'figure-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n')
    # These runs use sign +1, so the inverse encryption equation is C=P-K.
    assert best['sign'] == 1 and best['atbash'] == 0
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="580" height="620" viewBox="0 0 580 620" role="img" aria-labelledby="title desc">
<title id="title">Twenty-one fixed numeric streams with conditional key skips</title>
<desc id="desc">23,100 short screens yield 194 whole-page checks and zero final score-gate passes. An actual selected path illustrates a rejected key value reproducing the previous ciphertext index. It is not certified plaintext.</desc>
<rect width="580" height="620" fill="white"/>
<g font-family="Arial, sans-serif" fill="#252525">
<text x="20" y="34" font-size="24">21 numeric keys, conditional skips</text>
<text x="20" y="65" font-size="20">55 pages · two signs · Atbash · offsets 0–4</text>
<rect x="20" y="86" width="540" height="62" rx="6" fill="#eeeeee"/>
<text x="36" y="124" font-size="25">23,100 short screens</text>
<text x="280" y="175" font-size="24">↓</text>
<rect x="20" y="190" width="540" height="62" rx="6" fill="#eeeeee"/>
<text x="36" y="228" font-size="25">194 whole-page checks</text>
<text x="280" y="279" font-size="24">↓</text>
<rect x="20" y="294" width="540" height="62" rx="6" fill="#dddddd"/>
<text x="36" y="332" font-size="25">0 pass the final source score gate</text>
<text x="20" y="394" font-size="21">How one admissible skip works</text>
<text x="20" y="424" font-size="20">Top complete path: LP2-49, tiled primes ≤109</text>
<text x="20" y="454" font-size="20">Candidate P={plain[i]}; decode rule P=C+K (mod 29)</text>
<text x="20" y="487" font-size="21">Reject K={rejected}: C={plain[i]}−{rejected}={cipher[i-1]} mod 29</text>
<text x="20" y="515" font-size="20" fill="#555555">This repeats the previous ciphertext index.</text>
<text x="20" y="548" font-size="21">Accept K={accepted}: C={plain[i]}−{accepted}={cipher[i]} mod 29</text>
<text x="20" y="590" font-size="20">Candidate path only; no plaintext certified.</text>
</g></svg>'''
    (HERE/'screen-and-skip.svg').write_text(svg+'\n',encoding='utf8',newline='\n')
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__':
    main()
