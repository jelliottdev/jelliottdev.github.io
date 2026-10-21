"""Produce a finite certificate for the frozen full-palette quadratic plan.

Standard library only. Output is provisional until independently checked.
"""
import argparse
import hashlib
import itertools
import json
from math import gcd, isqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def divisors(n):
    assert n > 0
    result = set()
    for d in range(1, isqrt(n) + 1):
        if n % d == 0:
            result.update((d, n // d))
    return result


def coefficients(u, v, w, m):
    A = 2*u-3*v+w
    g = gcd(6, m)
    if A % g:
        return
    period = m // g
    start = (A // g * pow(6 // g, -1, period)) % period
    for k in range(g):
        a = start + k*period
        b = (v-u-5*a) % m
        c = (u-4*a-2*b) % m
        yield a, b, c


def produce():
    plan_path = ROOT/'experiments/plans/literal-prime-quadratic.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    for item in plan['inputs']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest() == item['sha256']
    palette = sorted(x['prime'] for x in json.loads((ROOT/'data/index.json').read_bytes())['alphabet'])
    assert len(palette) == 29 and palette[:3] == [2, 3, 5] and palette[-1] == 109
    allowed, scaled = set(palette), {6*x for x in palette}
    counts = {key: {'moduli': 0, 'coefficients': 0} for key in ('coprime', 'singular')}
    rows, exact, survivors = [], [], []
    for u, v, w in itertools.permutations(palette, 3):
        A, B, C = 2*u-3*v+w, -16*u+21*v-5*w, 30*u-30*v+6*w
        witness = next((x for x in palette if A*x*x+B*x+C not in scaled), None)
        if witness is None:
            exact.append([u, v, w])
            continue
        image = A*witness*witness+B*witness+C
        candidates = sorted({m for y in palette for m in divisors(abs(image-6*y)) if m > 109})
        rows.append({'anchors': [u,v,w], 'witness': witness, 'Q': image, 'moduli': candidates})
        for m in candidates:
            bucket = counts['coprime' if gcd(6,m) == 1 else 'singular']
            bucket['moduli'] += 1
            for a,b,c in coefficients(u,v,w,m):
                bucket['coefficients'] += 1
                output = [(a*x*x+b*x+c) % m for x in palette]
                if set(output) == allowed:
                    survivors.append({'m': m, 'coefficients': [a,b,c], 'outputs': output})
    bounded, aliases = [], 0
    if exact == [[2,3,5]]:
        for m in range(110,322):
            for a,b,c in coefficients(2,3,5,m):
                output = [(a*x*x+b*x+c) % m for x in palette]
                if set(output) == allowed:
                    if output == palette:
                        aliases += 1
                    else:
                        bounded.append({'m': m, 'coefficients': [a,b,c], 'outputs': output})
    return {'status': 'producer only; independent audit pending',
            'plan_sha256': hashlib.sha256(plan_path.read_bytes()).hexdigest(),
            'palette': palette, 'anchor_triples': len(rows)+len(exact),
            'counts': counts, 'finite_branches': rows, 'exact_branches': exact,
            'finite_survivors': survivors, 'bounded_exact_branch_survivors': bounded,
            'bounded_identity_coefficient_expressions': aliases,
            'exact_branch_requires_further_analysis': exact != [[2,3,5]]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; preserve earlier evidence.')
    result = produce()
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'finite_branches'}))
