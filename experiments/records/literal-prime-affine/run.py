"""All-modulus literal-prime affine palette test; Python standard library.

Without arguments write the report. --check recomputes and compares it.
No network, third-party code, language model or plaintext scoring.
"""
import argparse
import hashlib
import json
from math import isqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / 'exports/literal-prime-affine.json'


def divisors(n):
    result = set()
    for d in range(1, isqrt(n) + 1):
        if n % d == 0:
            result.update((d, n // d))
    return result


def measure():
    raw = (ROOT / 'data/index.json').read_bytes()
    palette = sorted(a['prime'] for a in json.loads(raw)['alphabet'])
    assert palette[:2] == [2, 3] and palette[-1] == 109 and len(set(palette)) == 29
    allowed = set(palette)
    rows, integer_maps, survivors = [], [], []
    for u in palette:
        for v in palette:
            if u == v:
                continue
            a, b = v-u, 3*u-2*v
            witness = next((p for p in palette if a*p+b not in allowed), None)
            if witness is None:
                integer_maps.append({'u': u, 'v': v, 'a': a, 'b': b})
                continue
            image = a*witness+b
            candidates = sorted({m for y in palette for m in divisors(abs(image-y)) if m > 109})
            for m in candidates:
                output = [(a*p+b) % m for p in palette]
                if set(output) == allowed:
                    survivors.append({'a': a % m, 'b': b % m, 'm': m, 'output': output})
            rows.append({'u': u, 'v': v, 'witness_input': witness,
                         'unreduced_image': image, 'candidate_moduli': candidates})
    assert integer_maps == [{'u': 2, 'v': 3, 'a': 1, 'b': 0}]
    return {'scope': 'Fixed literal-prime affine bijections of the full palette; every integer modulus >109',
            'input_sha256': hashlib.sha256(raw).hexdigest(), 'palette': palette,
            'anchor_pairs': len(rows)+len(integer_maps), 'finite_anchor_rows': rows,
            'candidate_maps_tested': sum(len(r['candidate_moduli']) for r in rows),
            'exact_integer_maps': integer_maps, 'nonidentity_survivors': survivors,
            'controls': {'constant': {'a': 0, 'b': 2, 'm': 110, 'distinct_outputs': 1},
                         'partial_palette': {'inputs': [2, 3], 'a': 109, 'b': 5, 'm': 110, 'outputs': [3, 2]}}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = measure()
    if args.check:
        assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    else:
        REPORT.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: result[k] for k in ['anchor_pairs', 'candidate_maps_tested', 'exact_integer_maps', 'nonidentity_survivors']}))
