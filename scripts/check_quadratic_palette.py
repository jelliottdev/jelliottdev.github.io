"""Independent certificate audit; does not import the producer.

Divisors are built from prime factorization. Coefficients are recovered by
integer lifts of 6a, without modular inverses. Every candidate is evaluated.
"""
import argparse
import hashlib
import itertools
import json
from math import gcd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def factored_divisors(n):
    assert n > 0
    values, p = [1], 2
    while p*p <= n:
        power, powers = 1, []
        while n % p == 0:
            n //= p
            power *= p
            powers.append(power)
        base = list(values)
        values.extend(d*q for d in base for q in powers)
        p = 3 if p == 2 else p+2
    if n > 1:
        values += [d*n for d in values]
    return values


def lifted_coefficients(u,v,w,m):
    residue = (2*u-3*v+w) % m
    for k in range(6):
        numerator = residue+k*m
        if numerator % 6:
            continue
        a = numerator//6
        b = (v-u-5*a) % m
        c = (u-4*a-2*b) % m
        assert tuple((a*x*x+b*x+c)%m for x in (2,3,5)) == (u%m,v%m,w%m)
        yield a,b,c


def audit(path):
    raw = path.read_bytes()
    report = json.loads(raw)
    plan_path = ROOT/'experiments/plans/literal-prime-quadratic.json'
    assert report['plan_sha256'] == hashlib.sha256(plan_path.read_bytes()).hexdigest()
    for item in json.loads(plan_path.read_bytes())['inputs']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest() == item['sha256']
    palette = sorted(item['prime'] for item in json.loads((ROOT/'data/index.json').read_bytes())['alphabet'])
    assert report['palette'] == palette
    allowed = set(palette)
    counts = {k: {'moduli':0, 'coefficients':0} for k in ('coprime','singular')}
    exact, survivors, row_index = [], [], 0
    for u,v,w in itertools.permutations(palette,3):
        def q(x):
            return 2*u*(x-3)*(x-5)-3*v*(x-2)*(x-5)+w*(x-2)*(x-3)
        witnesses = [x for x in palette if q(x) % 6 or q(x)//6 not in allowed]
        if not witnesses:
            exact.append([u,v,w])
            continue
        row = report['finite_branches'][row_index]
        row_index += 1
        x = witnesses[0]
        candidates = sorted({d for y in palette for d in factored_divisors(abs(q(x)-6*y)) if d>109})
        assert row == {'anchors':[u,v,w], 'witness':x, 'Q':q(x), 'moduli':candidates}
        for m in candidates:
            bucket = counts['coprime' if gcd(m,6)==1 else 'singular']
            bucket['moduli'] += 1
            for a,b,c in lifted_coefficients(u,v,w,m):
                bucket['coefficients'] += 1
                output = [(a*x*x+b*x+c)%m for x in palette]
                if sorted(output) == palette:
                    survivors.append({'m':m,'coefficients':[a,b,c],'outputs':output})
    assert row_index == len(report['finite_branches'])
    assert report['anchor_triples'] == row_index+len(exact) == 21924
    assert report['counts'] == counts
    assert report['exact_branches'] == exact
    assert report['finite_survivors'] == survivors
    assert report['exact_branch_requires_further_analysis'] == (exact != [[2,3,5]])
    bounded, identities = [], 0
    if exact == [[2,3,5]]:
        # Exhaust a directly stated 6a congruence in the bounded branch.
        for m in range(110,322):
            for a in range(m):
                if 6*a % m:
                    continue
                b,c = (1-5*a)%m, (6*a)%m
                output = [(a*x*x+b*x+c)%m for x in palette]
                if sorted(output) == palette:
                    if output == palette:
                        identities += 1
                    else:
                        bounded.append({'m':m,'coefficients':[a,b,c],'outputs':output})
    assert report['bounded_exact_branch_survivors'] == bounded
    assert report['bounded_identity_coefficient_expressions'] == identities
    return {'status':'finite certificate independently checked; mathematical scope and human review remain explicit',
            'report_sha256':hashlib.sha256(raw).hexdigest(),
            'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'anchor_triples':row_index+len(exact), 'counts':counts,
            'exact_branches':exact, 'nonidentity_survivor_count':len(survivors)+len(bounded)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    if args.receipt.exists():
        parser.error('Receipt already exists')
    receipt = audit(args.report)
    args.receipt.write_text(json.dumps(receipt,indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(receipt))
