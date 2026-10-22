"""Audit the absorbing-zero invariant of literal multiplicative ciphertext autokey."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
MOD=29


def report():
    index_raw=(ROOT/'data/index.json').read_bytes()
    index=json.loads(index_raw)
    lookup={row['rune']:row['index'] for row in index['alphabet']}
    assert len(lookup)==MOD and index['alphabet'][0]['latin']=='F'
    hashes={'data/index.json':hashlib.sha256(index_raw).hexdigest()}
    pages=[]
    for number in range(56):
        path=f'text/lp2-{number:02d}.txt'
        raw=(ROOT/path).read_bytes()
        source=raw.decode('utf-8')
        unknown={c for c in source if '\u16a0'<=c<='\u16ff'}-lookup.keys()
        if unknown:raise ValueError(f'Unknown rune in {path}: {unknown!r}')
        stream=[lookup[c] for c in source if c in lookup]
        expected=next(p['rune_count'] for p in index['pages'] if p['id']==f'lp2-{number:02d}')
        assert len(stream)==expected
        incompatible=[i for i,(left,right) in enumerate(zip(stream,stream[1:]),start=1)
                      if left==0 and right!=0]
        ordinary_doublets=[i for i,(left,right) in enumerate(zip(stream,stream[1:]),start=1)
                           if left==right!=0]
        pages.append({'page':f'lp2-{number:02d}','runes':len(stream),'zero_ciphertext_runes':stream.count(0),
                      'zero_to_nonzero_positions_one_based':incompatible,
                      'nonzero_doublet_positions_one_based':ordinary_doublets})
        hashes[path]=hashlib.sha256(raw).hexdigest()
    assert sum(p['runes'] for p in pages)==12956
    total=sum(len(p['zero_to_nonzero_positions_one_based']) for p in pages)
    assert total==450
    # Positive control: a nonzero start and any plaintext sequence remains
    # at zero after the first plaintext zero; no observed zero->nonzero edge.
    plain=[2,1,0,7,3,4]
    synthetic=[]; previous=5
    for value in plain:
        previous=value*previous%MOD
        synthetic.append(previous)
    assert synthetic==[10,10,0,0,0,0]
    return {'schema':'liberpedia-multiplicative-ciphertext-autokey-v1',
            'input_sha256':hashes,
            'model':'c[i] = p[i] * c[i-1] mod 29 for every rune after a page start; no skips, resets, changed alphabet, or inserted tokens.',
            'zero_rune':'F, index 0 in the archived 29-rune order',
            'invariant':'If c[i-1] is 0, then c[i] must also be 0 for every plaintext p[i]. A zero state is absorbing.',
            'runes':sum(p['runes'] for p in pages),
            'zero_ciphertext_runes':sum(p['zero_ciphertext_runes'] for p in pages),
            'incompatible_zero_to_nonzero_edges':total,
            'nonempty_pages':sum(bool(p['runes']) for p in pages),
            'nonempty_pages_with_incompatible_edge':sum(bool(p['zero_to_nonzero_positions_one_based']) for p in pages),
            'nonzero_doublets':sum(len(p['nonzero_doublet_positions_one_based']) for p in pages),
            'synthetic_positive_control':{'plaintext':plain,'start_ciphertext':5,'ciphertext':synthetic},
            'pages':pages,
            'scope_limit':'Rejects only the literal uninterrupted multiplicative ciphertext feedback recurrence in this rune order. A rule that skips zero, resets, uses a keyed offset, or transforms symbols is a different model and must be specified separately.'}


def figure(data):
    values=[('Ciphertext zeroes',data['zero_ciphertext_runes']),
            ('Zero → nonzero edges',data['incompatible_zero_to_nonzero_edges'])]
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 610 210" role="img" aria-labelledby="title desc">',
           '<title id="title">Literal multiplicative feedback encounters 450 impossible transitions</title>',
           '<desc id="desc">The LP2 transcription has 458 zero-index runes and 450 zero-to-nonzero transitions. The literal recurrence cannot leave zero.</desc>',
           '<rect width="610" height="210" fill="white"/>',
           '<g font-family="system-ui,sans-serif" fill="#27343c">',
           '<text x="18" y="27" font-size="18" font-weight="600">Zero is absorbing under multiplication</text>',
           '<text x="18" y="48" font-size="12">LP2-00–55 · F is rune index 0 · page boundaries retained</text>']
    for n,(label,value) in enumerate(values):
        y=85+n*48
        parts += [f'<text x="18" y="{y}" font-size="14">{label}</text>',
                  f'<rect x="205" y="{y-17}" width="{value/500*310:.1f}" height="21" fill="{chr(35)}255f79"/>',
                  f'<text x="530" y="{y}" font-size="14">{value}</text>']
    parts += ['<text x="18" y="190" font-size="12">Each zero → nonzero edge contradicts the uninterrupted recurrence.</text>',
              '</g></svg>']
    return '\n'.join(parts)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--write',action='store_true')
    group.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=report(); payload=json.dumps(result,ensure_ascii=False,indent=2)+'\n'; visual=figure(result)
    if args.write:
        (HERE/'results.json').write_text(payload,encoding='utf-8',newline='\n')
        (HERE/'zero-state.svg').write_text(visual,encoding='utf-8',newline='\n')
    if args.check:
        assert payload==(HERE/'results.json').read_text(encoding='utf-8')
        assert visual==(HERE/'zero-state.svg').read_text(encoding='utf-8')
        print('PASS: zero-state contradiction and source hashes')
    print(result['incompatible_zero_to_nonzero_edges'], 'incompatible transitions on',
          result['nonempty_pages_with_incompatible_edge'],'nonempty pages')


if __name__=='__main__':main()
