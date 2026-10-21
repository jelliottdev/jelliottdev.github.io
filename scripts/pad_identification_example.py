"""Exhaustive mathematical illustration; no manuscript or generator identification."""
from collections import Counter
from itertools import product
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]


def example():
    words=list(product(range(3),repeat=2))
    repeated=[(k,k) for k in range(3)]
    cipher=(0,1)
    rows=[]
    for plain in words:
        counts=Counter(tuple((p+k)%3 for p,k in zip(plain,key)) for key in words)
        assert set(counts)==set(words) and set(counts.values())=={1}
        restricted=[tuple((p+k)%3 for p,k in zip(plain,key)) for key in repeated]
        # Each coordinate is uniform, but their difference is deterministic.
        for i in range(2):assert Counter(c[i] for c in restricted)==Counter({0:1,1:1,2:1})
        assert all((c[1]-c[0])%3==(plain[1]-plain[0])%3 for c in restricted)
        key=tuple((c-p)%3 for c,p in zip(cipher,plain))
        # Independent check: enumerate encryption matches instead of subtraction.
        matches=[k for k in words if tuple((plain[i]+k[i])%3 for i in range(2))==cipher]
        assert matches==[key]
        rows.append({'plaintext':list(plain),'required_key':list(key),'repeated_key_allowed':key in repeated})
    assert sum(r['repeated_key_allowed'] for r in rows)==3
    return {'alphabet_size':3,'length':2,'fixed_ciphertext':list(cipher),
            'full_key_count':9,'repeated_key_count':3,'encryption_pairs_checked':81,
            'rows':rows,'scope':'Exhaustive toy illustration, not an LP measurement or a test identifying a pad generator.'}


def figure(data):
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 535" role="img" aria-labelledby="title desc">',
           '<title id="title">One ciphertext, different allowed keys</title>',
           '<desc id="desc">For ciphertext zero one modulo three, all nine plaintext pairs fit when any two-symbol key is allowed. Only three fit a repeated one-symbol key.</desc>',
           '<rect width="360" height="535" fill="white"/>',
           '<style>text{font:14px Arial,sans-serif;fill:#253d49}.small{font-size:12px}.head{font-weight:bold}</style>',
           '<text x="14" y="25" class="head">Observed ciphertext: 0 1</text>',
           '<text x="14" y="48">C = P + K, coordinate by coordinate mod 3</text>',
           '<text x="14" y="85" class="head">Plaintext P</text>',
           '<text x="126" y="85" class="head">Required K</text>',
           '<text x="240" y="85" class="head">Repeated?</text>']
    for i,row in enumerate(data['rows']):
        y=100+i*38
        if row['repeated_key_allowed']:
            parts.append(f'<rect x="10" y="{y-3}" width="338" height="32" fill="#e8eff3"/>')
        p=' '.join(map(str,row['plaintext']));k=' '.join(map(str,row['required_key']))
        parts += [f'<text x="28" y="{y+18}">{p}</text>',f'<text x="143" y="{y+18}">{k}</text>',
                  f'<text x="260" y="{y+18}">{"Yes" if row["repeated_key_allowed"] else "No"}</text>']
    parts+=['<text x="14" y="467">Any two-symbol key: all 9 plaintexts fit.</text>',
            '<text x="14" y="490">Repeated one-symbol key: only 3 fit.</text>',
            '<text x="14" y="518" class="small">A mathematical example, not manuscript evidence.</text>','</svg>']
    return '\n'.join(parts)+'\n'


if __name__=='__main__':
    data=example()
    (ROOT/'exports/pad-identification-example.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'exports/figures/pad-identification-example.svg').write_text(figure(data),encoding='utf-8',newline='\n')
    print('Checked all 81 plaintext/key pairs, uniform coordinate marginals, and the repeated-key difference invariant.')
