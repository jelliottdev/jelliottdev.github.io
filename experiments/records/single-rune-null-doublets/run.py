"""Exhaust all 29 fixed single-rune null deletions on LP2 doublets."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def counts(streams):
    symbols = sum(map(len, streams))
    edges = sum(max(0, len(stream)-1) for stream in streams)
    doublets = sum(sum(a == b for a, b in zip(stream, stream[1:])) for stream in streams)
    expectation = sum((Fraction(sum(n*(n-1) for n in Counter(stream).values()), len(stream))
                       for stream in streams if stream), Fraction())
    return {'runes': symbols, 'edges': edges, 'doublets': doublets,
            'doublet_rate': str(Fraction(doublets, edges)),
            'fixed_count_shuffle_expectation': str(expectation),
            'fixed_count_shuffle_expectation_decimal': round(float(expectation), 6),
            'observed_to_expected': round(doublets / float(expectation), 6)}


def report():
    plan_bytes = (HERE/'plan.json').read_bytes()
    plan = json.loads(plan_bytes)
    for entry in plan['inputs']:
        assert sha((ROOT/entry['path']).read_bytes()) == entry['sha256'], entry['path']
    alphabet = json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']
    labels = {item['rune']: item['latin'] for item in alphabet}
    streams = []
    for n in range(56):
        raw = (ROOT/f'text/lp2-{n:02d}.txt').read_text(encoding='utf-8')
        unknown = {c for c in raw if '\u16a0' <= c <= '\u16ff'} - labels.keys()
        if unknown:
            raise ValueError(f'Unknown rune on LP2-{n:02d}: {ascii(unknown)}')
        streams.append(''.join(c for c in raw if c in labels))
    baseline = counts(streams)
    rows = []
    for item in alphabet:
        rune = item['rune']
        changed = [stream.replace(rune, '') for stream in streams]
        lost = sum(sum(a == b == rune for a, b in zip(stream, stream[1:])) for stream in streams)
        gained = 0
        for stream in streams:
            retained = [(i, symbol) for i, symbol in enumerate(stream) if symbol != rune]
            gained += sum(right_i > left_i+1 and left == right
                          for (left_i, left), (right_i, right) in zip(retained, retained[1:]))
        result = {'rune': rune, 'label': labels[rune],
                  'deleted': sum(stream.count(rune) for stream in streams),
                  'nonempty_pages_after': sum(bool(stream) for stream in changed),
                  'old_doublets_removed': lost, 'new_bridge_doublets': gained,
                  **counts(changed)}
        assert result['doublets'] == baseline['doublets'] - lost + gained
        rows.append(result)
    assert len(rows) == 29 and baseline['runes'] == 12956 and baseline['doublets'] == 86
    return {'schema': 'liberpedia-single-rune-null-doublets-v1',
            'plan_sha256': sha(plan_bytes), 'scope': 'LP2-00–55, headings included; within-page rune streams only.',
            'method': 'Remove every occurrence of each of the 29 alphabet runes, one rune type at a time. Preserve the surviving order and page boundaries; discard non-runes before counting adjacent equal pairs.',
            'comparison': 'For each retained page stream, the fixed-count shuffle expectation is sum over symbols f(f-1)/N. This is a descriptive expectation, not a p-value or English-language benchmark.',
            'baseline': baseline, 'variants': rows,
            'limitations': 'Only fixed deletion of all occurrences of exactly one rune type is exhausted. Position-specific nulls, multiple deleted types, deletion before another cipher, changed word boundaries, and language scoring are not tested.'}


def figure(data):
    rows = sorted(data['variants'], key=lambda row: (row['doublets'], row['label']))
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="650" height="750" viewBox="0 0 650 750" role="img" aria-labelledby="title desc">',
             '<title id="title">Adjacent equal-rune pairs after each single-type deletion</title>',
             '<desc id="desc">All 29 deletions leave more than 86 adjacent equal pairs. The smallest count is 92; the largest is 109. Page boundaries remain fixed.</desc>',
             '<rect width="650" height="750" fill="#faf9f5"/>',
             '<g font-family="Arial,sans-serif" fill="#263b45">',
             '<text x="24" y="32" font-size="21">Delete one rune type, everywhere</text>',
             '<text x="24" y="55" font-size="13">LP2-00–55 · within-page pairs · 29 fixed rules</text>',
             '<text x="24" y="78" font-size="13">Original: 86 equal pairs. Every deletion leaves more.</text>']
    for tick in (86, 100, 110):
        x = 140+(tick-80)*13
        parts += [f'<path d="M{x} 98V704" stroke="{chr(35)}b2bab8"/>',
                  f'<text x="{x}" y="722" font-size="12" text-anchor="middle">{tick}</text>']
    for i, row in enumerate(rows):
        y=101+i*20
        x=140+(row['doublets']-80)*13
        parts += [f'<text x="24" y="{y+13}" font-size="13">{row["label"]}</text>',
                  f'<path d="M218 {y+9}H{x}" stroke="#315f73" stroke-width="5"/>',
                  f'<circle cx="{x}" cy="{y+9}" r="4" fill="#315f73"/>',
                  f'<text x="{x+9}" y="{y+13}" font-size="12">{row["doublets"]}</text>']
    parts += ['<text x="325" y="742" font-size="12" text-anchor="middle">Adjacent equal-rune pairs after deletion</text>', '</g></svg>']
    return '\n'.join(parts)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    data=report(); chart=figure(data)
    if args.check:
        assert data == json.loads((HERE/'results.json').read_text(encoding='utf-8'))
        assert chart == (HERE/'single-rune-null-doublets.svg').read_text(encoding='utf-8')
        print('PASS: 29 fixed null rules, source hashes, counts and chart reproduce')
    else:
        (HERE/'results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        (HERE/'single-rune-null-doublets.svg').write_text(chart,encoding='utf-8',newline='\n')
        print(json.dumps({'baseline':data['baseline']['doublets'],
                          'min':min(row['doublets'] for row in data['variants']),
                          'max':max(row['doublets'] for row in data['variants'])}))


if __name__=='__main__':
    main()
