"""Compare literal additive, Beaufort and subtractive ciphertext feedback."""
import argparse
from collections import Counter
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
    assert len(lookup)==MOD
    hashes={'data/index.json':hashlib.sha256(index_raw).hexdigest()}
    counts={name:Counter() for name in ('additive','beaufort','subtractive')}
    pages=[]
    for number in range(56):
        path=f'text/lp2-{number:02d}.txt'
        raw=(ROOT/path).read_bytes()
        source=raw.decode('utf-8')
        unknown={c for c in source if '\u16a0'<=c<='\u16ff'}-lookup.keys()
        if unknown:raise ValueError(f'Unknown rune in {path}: {unknown!r}')
        stream=[lookup[c] for c in source if c in lookup]
        assert len(stream)==next(p['rune_count'] for p in index['pages'] if p['id']==f'lp2-{number:02d}')
        row={name:Counter() for name in counts}
        doublets=0
        for previous,current in zip(stream,stream[1:]):
            values={'additive':(current-previous)%MOD,
                    'beaufort':(previous-current)%MOD,
                    'subtractive':(current+previous)%MOD}
            assert (values['additive']+values['beaufort'])%MOD==0
            doublets+=previous==current
            for name,value in values.items():
                counts[name][value]+=1
                row[name][value]+=1
        assert row['additive'][0]==row['beaufort'][0]==doublets
        pages.append({'page':f'lp2-{number:02d}','edges':max(0,len(stream)-1),
                      'ciphertext_doublets':doublets,
                      'zero_outputs':{name:row[name][0] for name in counts}})
        hashes[path]=hashlib.sha256(raw).hexdigest()
    assert sum(p['edges'] for p in pages)==12901
    assert sum(p['ciphertext_doublets'] for p in pages)==86
    frequency={name:[counter[i] for i in range(MOD)] for name,counter in counts.items()}
    assert all(frequency['additive'][i]==frequency['beaufort'][(-i)%MOD] for i in range(MOD))
    # An ordinary two-rune control shows the differing zero conditions.
    control=[(4,4),(4,25)]
    control_rows=[{'previous':x,'current':y,'additive':(y-x)%MOD,
                   'beaufort':(x-y)%MOD,'subtractive':(x+y)%MOD} for x,y in control]
    return {'schema':'liberpedia-linear-ciphertext-feedback-v1','input_sha256':hashes,
            'models':{
                'additive':'c[i] = p[i] + c[i-1] mod 29; inverse p[i] = c[i] - c[i-1].',
                'beaufort':'c[i] = c[i-1] - p[i] mod 29; inverse p[i] = c[i-1] - c[i].',
                'subtractive':'c[i] = p[i] - c[i-1] mod 29; inverse p[i] = c[i] + c[i-1].'},
            'scope':'LP2-00–55; every within-page adjacent rune pair, headings retained, non-runes removed.',
            'pages':pages,'edge_count':12901,'ciphertext_doublets':86,
            'zero_output_counts':{name:counter[0] for name,counter in counts.items()},
            'output_frequencies':frequency,'synthetic_control':control_rows,
            'invariant':'Additive and Beaufort inverses are negatives of each other modulo 29; their zero-output positions are exactly the ciphertext doublet positions. Subtractive output is zero when adjacent ciphertext values sum to zero, not necessarily when they are equal.',
            'limits':'The inverse streams are only candidate plaintext under the literal no-key recurrences. Zero counts alone cannot identify a cipher, exclude an added key or interruption, or establish readable English.'}


def figure(data):
    entries=[('Additive',data['zero_output_counts']['additive']),
             ('Beaufort',data['zero_output_counts']['beaufort']),
             ('Subtractive',data['zero_output_counts']['subtractive'])]
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 610 240" role="img" aria-labelledby="title desc">',
           '<title id="title">Zero outputs under three literal ciphertext-feedback inverses</title>',
           '<desc id="desc">Additive and Beaufort inverses both yield 86 zeroes, exactly the ciphertext doublet positions. Subtractive yields 437 zeroes at a different set of positions.</desc>',
           '<rect width="610" height="240" fill="white"/>',
           '<g font-family="system-ui,sans-serif" fill="#27343c">',
           '<text x="18" y="27" font-size="18" font-weight="600">Different rules, different zero conditions</text>',
           '<text x="18" y="48" font-size="12">12,901 within-page pairs · LP2-00–55</text>']
    for n,(label,value) in enumerate(entries):
        y=83+n*43
        parts += [f'<text x="18" y="{y}" font-size="14">{label}</text>',
                  f'<rect x="140" y="{y-16}" width="{value/450*360:.1f}" height="20" fill="#255f79"/>',
                  f'<text x="520" y="{y}" font-size="14">{value}</text>']
    parts += ['<text x="18" y="225" font-size="12">A zero count is a structural check, not a plaintext reading.</text>',
              '</g></svg>']
    return '\n'.join(parts)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--write',action='store_true')
    group.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=report(); payload=json.dumps(result,ensure_ascii=False,indent=2)+'\n';visual=figure(result)
    if args.write:
        (HERE/'results.json').write_text(payload,encoding='utf-8',newline='\n')
        (HERE/'zero-outputs.svg').write_text(visual,encoding='utf-8',newline='\n')
    if args.check:
        assert payload==(HERE/'results.json').read_text(encoding='utf-8')
        assert visual==(HERE/'zero-outputs.svg').read_text(encoding='utf-8')
        print('PASS: three feedback inverses and exact zero-position identities')
    print(result['zero_output_counts'])


if __name__=='__main__':main()
