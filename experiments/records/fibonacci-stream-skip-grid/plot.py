"""A concrete recurrence alias and the measured finite search funnel."""
import json

import engine as e


def main():
    result=json.loads((e.HERE/'results.json').read_text(encoding='utf8'))
    terminal=json.loads((e.HERE/'terminal-audit.json').read_text(encoding='utf8'))
    original=e.numeric.ks_fibonacci(4,19,10)
    canonical=e.numeric.ks_fibonacci(13,7,7)
    assert original[3:]==canonical
    best=result['best_full']
    assert (best['a'],best['b'])==(13,7)
    receipt={'example_original_seeds':[4,19],'original_sign':1,'original_offset':3,
             'example_canonical_seeds':[13,7],'canonical_sign':1,'canonical_offset':0,
             'example_original_values':original,'same_aligned_values':canonical,
             'selection':'An actual alias of the best returned full setting, selected only to illustrate the algebra; Atbash unchanged.',
             'canonical_screens':result['canonical_screens'],'source_labeled_screens':result['source_labeled_screens'],
             'canonical_full_confirmations':result['canonical_full_confirmations'],
             'source_gate_passes':result['canonical_source_gate_passes'],
             'retained_terminal_hypotheses':terminal['retained_hypotheses'],
             'terminal_gate_passes':terminal['terminal_gate_passes'],
             'limit':'Equal key values explain duplicated labels; no candidate plaintext is certified.'}
    e.write(e.HERE/'figure-receipt.json',receipt)
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="580" height="710" viewBox="0 0 580 710" role="img" aria-labelledby="title desc">
<title id="title">Fibonacci keys with conditional skips</title>
<desc id="desc">Seed4,19 shifted three places equals seed13,7. The exact alias reduction turns925,100source labels into92,510distinct canonical screens.900whole-page checks and160,613retained terminal hypotheses produce zero final score-gate passes.</desc>
<rect width="580" height="710" fill="white"/>
<g font-family="Arial,sans-serif" fill="#252525">
<text x="20" y="35" font-size="25">Fibonacci keys with conditional skips</text>
<text x="20" y="68" font-size="20">Each next value adds the previous two, mod 29.</text>
<rect x="20" y="92" width="540" height="157" rx="6" fill="#eeeeee"/>
<text x="35" y="125" font-size="21">Seed (4,19), start at its fourth value:</text>
<text x="35" y="161" font-size="24">4, 19, 23 → 13, 7, 20, 27, 18…</text>
<text x="35" y="195" font-size="21">Seed (13,7), start at its first value:</text>
<text x="35" y="230" font-size="24">13, 7, 20, 27, 18…</text>
<text x="20" y="286" font-size="21">Shift and sign become a different seed pair.</text>
<text x="20" y="319" font-size="22">925,100 labels → 92,510 canonical screens</text>
<rect x="20" y="347" width="540" height="58" rx="6" fill="#eeeeee"/>
<text x="36" y="384" font-size="25">92,510 short screens</text>
<text x="280" y="435" font-size="24">↓</text>
<rect x="20" y="450" width="540" height="58" rx="6" fill="#eeeeee"/>
<text x="36" y="487" font-size="25">900 whole-page checks</text>
<text x="280" y="538" font-size="24">↓</text>
<rect x="20" y="553" width="540" height="58" rx="6" fill="#dddddd"/>
<text x="36" y="590" font-size="25">0 pass the final source score gate</text>
<text x="20" y="647" font-size="20">160,613 retained terminal alternatives:</text>
<text x="20" y="678" font-size="20">none crosses the gate; no plaintext certified.</text>
</g></svg>'''
    (e.HERE/'fibonacci-alias-and-search.svg').write_text(svg+'\n',encoding='utf8',newline='\n')
    print('Figure: actual recurrence alias and measured source/terminal gates')


if __name__=='__main__':
    main()
