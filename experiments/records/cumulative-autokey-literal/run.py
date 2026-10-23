"""Replay the literal cumulative plaintext sum, resetting at each page."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
READINGS = ('warning', 'first-koan', 'second-koan', 'some-wisdom',
            'loss-of-divinity', 'instruction', 'welcome')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    alphabet_path = ROOT / 'data/index.json'
    letters = json.loads(alphabet_path.read_text(encoding='utf-8'))['alphabet']
    lookup = {item['rune']: i for i, item in enumerate(letters)}
    sources = {'data/index.json': sha(alphabet_path)}
    pages = []
    for n in range(56):
        path = ROOT / 'text' / f'lp2-{n:02d}.txt'
        pages.append([lookup[c] for c in path.read_text(encoding='utf-8') if c in lookup])
        sources[str(path.relative_to(ROOT)).replace('\\', '/')]=sha(path)
    solved = []
    for name in READINGS:
        path = ROOT / 'exports/readings' / f'{name}.csv'
        with path.open(encoding='utf-8', newline='') as handle:
            solved.extend(int(row['output_index']) for row in csv.DictReader(handle)
                          if row['output_index'].strip())
        sources[str(path.relative_to(ROOT)).replace('\\', '/')]=sha(path)
    return pages, solved, sources


def wilson(k, n):
    z = 1.95996398454
    p = k / n
    d = 1 + z*z/n
    mid = (p + z*z/(2*n)) / d
    half = z*((p*(1-p)/n + z*z/(4*n*n))**0.5)/d
    return [round(mid-half, 6), round(mid+half, 6)]


def profile(values):
    counts = Counter(values)
    return {'runes': len(values), 'counts': [counts[i] for i in range(29)],
            'f_rate': round(counts[0]/len(values), 6),
            'f_wilson_95': wilson(counts[0],len(values)),
            'entropy_bits': round(-sum((n/len(values))*math.log2(n/len(values))
                                       for n in counts.values()), 6),
            'index_of_coincidence': round(sum(n*(n-1) for n in counts.values())
                                          /(len(values)*(len(values)-1)), 6)}


def make():
    pages, solved, sources = load()
    decoded=[]; first_positions=[]; doublets=0
    for n, cipher in enumerate(pages):
        if not cipher:
            continue
        first_positions.append({'page':f'lp2-{n:02d}', 'cipher_index':cipher[0]})
        plain=[cipher[0]] + [(cipher[i]-cipher[i-1])%29 for i in range(1,len(cipher))]
        assert all((sum(plain[:i+1])%29)==cipher[i] for i in range(len(cipher)))
        doublets+=sum(cipher[i]==cipher[i-1] for i in range(1,len(cipher)))
        decoded+=plain
    assert len(decoded)==sum(map(len,pages))==12956
    assert len(first_positions)==55 and doublets==86
    assert sum(1 for x in decoded if x==0)==doublets+sum(x['cipher_index']==0 for x in first_positions)
    return {'schema':'liberpedia-cumulative-autokey-literal-v1', 'input_sha256':sources,
            'rule':'P[0]=C[0]; P[k]=(C[k]-C[k-1]) mod 29 for k>0; page-local reset',
            'page_count':56,'nonempty_pages':55,'within_page_doublets':doublets,
            'first_positions':first_positions,'candidate':profile(decoded),
            'solved_lp1_control':profile(solved),
            'raw_lp2_control':profile([x for p in pages for x in p])}


def svg(report):
    rows=[('Literal cumulative inverse',report['candidate']),
          ('Known LP1 readings',report['solved_lp1_control']),
          ('Raw LP2 ciphertext',report['raw_lp2_control'])]
    lines=['<svg xmlns="http://www.w3.org/2000/svg" width="390" height="270" viewBox="0 0 390 270" role="img" aria-labelledby="t d">',
           '<title id="t">F rune rates under three streams</title>',
           '<desc id="d">The literal cumulative inverse contains fewer F runes than the raw LP2 stream. This is a descriptive comparison, not a cipher test.</desc>',
           '<rect width="390" height="270" fill="#f5f6f7"/>',
           '<g font-family="Arial,sans-serif" fill="#263740">',
           '<text x="18" y="32" font-size="18" font-weight="bold">How often is the output F?</text>',
           '<text x="18" y="56" font-size="12">Zero-index rune · page-local cumulative rule</text>']
    colors=['#315f78','#647c88','#87939c']
    for j,(name,p) in enumerate(rows):
        y=90+j*59; rate=p['f_rate']; w=round(rate*4500,1)
        lines += [f'<text x="18" y="{y}" font-size="13">{name}</text>',
                  f'<rect x="18" y="{y+10}" width="270" height="16" fill="#dfe3e6"/>',
                  f'<rect x="18" y="{y+10}" width="{min(270,w)}" height="16" fill="{colors[j]}"/>',
                  f'<text x="298" y="{y+24}" font-size="14">{100*rate:.2f}%</text>']
    lines += ['<text x="18" y="250" font-size="12">Different corpora; bars are observations, not probabilities.</text>','</g>','</svg>']
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(); p.add_argument('--check',action='store_true'); args=p.parse_args()
    result=make(); image=svg(result)
    path=HERE/'results.json'; figure=HERE/'f-rate.svg'
    if args.check:
        assert json.loads(path.read_text(encoding='utf-8'))==result
        assert figure.read_text(encoding='utf-8')==image
        print('PASS cumulative autokey literal')
    else:
        path.write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
        figure.write_bytes(image.encode('utf-8'))
        print(json.dumps({k:result[k] for k in ('candidate','solved_lp1_control','raw_lp2_control')},indent=2))

if __name__=='__main__': main()
