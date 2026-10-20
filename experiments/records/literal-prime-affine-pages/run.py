"""All-modulus affine search on page-specific prime supports; standard library."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / 'exports/literal-prime-affine-pages.json'
divisors = runpy.run_path(str(ROOT / 'experiments/records/literal-prime-affine/run.py'))['divisors']


def measure():
    alphabet = json.loads((ROOT / 'data/index.json').read_bytes())['alphabet']
    prime = {a['rune']: a['prime'] for a in alphabet}
    palette = sorted(prime.values())
    allowed = set(palette)
    pages, groups = [], {}
    for n in range(56):
        name = f'lp2-{n:02d}'
        raw = (ROOT / f'text/{name}.txt').read_bytes()
        support = tuple(sorted({prime[c] for c in raw.decode('utf-8') if c in prime}))
        pages.append({'page': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'support': list(support)})
        if support:
            groups.setdefault(support, []).append(name)
    cases = []
    for support, members in sorted(groups.items()):
        assert support[:2] == (2, 3)
        rows, integer_maps, survivors = [], [], []
        for u in palette:
            for v in palette:
                if u == v:
                    continue
                a, b = v-u, 3*u-2*v
                witness = next((p for p in support if a*p+b not in allowed), None)
                if witness is None:
                    integer_maps.append({'a': a, 'b': b, 'output': [a*p+b for p in support]})
                    continue
                value = a*witness+b
                candidates = sorted({m for y in palette for m in divisors(abs(value-y)) if m>109})
                for m in candidates:
                    output = [(a*p+b)%m for p in support]
                    if len(set(output)) == len(support) and set(output) <= allowed:
                        survivors.append({'a': a%m, 'b': b%m, 'm': m, 'output': output})
                rows.append({'u': u, 'v': v, 'witness_input': witness, 'unreduced_image': value,
                             'candidate_moduli': candidates})
        cases.append({'pages': members, 'support': list(support), 'integer_maps': integer_maps,
                      'survivors': survivors, 'certificate': rows,
                      'candidate_maps_tested': sum(len(r['candidate_moduli']) for r in rows)})
    return {'palette': palette, 'pages': pages, 'cases': cases,
            'empty_pages': [p['page'] for p in pages if not p['support']],
            'scope': 'One fixed map per page; all integer m>109; injective on observed primes with outputs in full palette'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args=parser.parse_args()
    result=measure()
    if args.check:
        assert result == json.loads(REPORT.read_text())
    else:
        REPORT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    for case in result['cases']:
        print(len(case['support']), len(case['pages']), case['candidate_maps_tested'], case['survivors'])
    print('Empty:',result['empty_pages'])
