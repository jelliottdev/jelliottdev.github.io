"""Exact binomial comparison for one declared uniform-additive-key model."""
import argparse
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PLAN = ROOT / 'experiments/plans/uniform-additive-doublets.json'
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def report():
    plan = json.loads(PLAN.read_bytes())
    for item in plan['inputs']:
        assert sha((ROOT / item['path']).read_bytes()) == item['sha256'], item['path']
    alphabet = {a['rune'] for a in json.loads((ROOT / 'data/index.json').read_bytes())['alphabet']}
    assert len(alphabet) == 29
    pages = []
    for number in range(56):
        page = f'lp2-{number:02}'
        stream = [c for c in (ROOT / f'text/{page}.txt').read_text(encoding='utf-8') if c in alphabet]
        pages.append({'page': page, 'runes': len(stream), 'edges': max(0, len(stream)-1),
                      'doublets': sum(a == b for a, b in zip(stream, stream[1:]))})
    edges = sum(p['edges'] for p in pages)
    observed = sum(p['doublets'] for p in pages)
    ledger = json.loads((ROOT / 'exports/unsolved-doublets.json').read_bytes())['page']
    assert (edges, observed) == (ledger['windows'], ledger['doublets'])
    numerator = sum(math.comb(edges, j) * 28**(edges-j) for j in range(observed+1))
    denominator = 29**edges
    with localcontext() as context:
        context.prec = 80
        probability = Decimal(numerator) / Decimal(denominator)
        # Fixed ten-count plotting bins; all remaining mass is retained as overflow.
        mass = (Decimal(28)/29)**edges
        bins = [Decimal(0)] * 66
        for j in range(edges+1):
            bins[min(j//10, 65)] += mass
            if j < edges:
                mass *= Decimal(edges-j) / Decimal((j+1)*28)
        assert abs(sum(bins)-1) < Decimal('1e-70')
        return {'plan_sha256': sha(PLAN.read_bytes()), 'input_sha256': {i['path']: i['sha256'] for i in plan['inputs']},
                'model': 'Independent uniform ciphertext on 29 symbols; fixed page lengths; within-page adjacency only.',
                'pages': pages, 'runes': sum(p['runes'] for p in pages),
                'nonempty_pages': sum(p['runes'] > 0 for p in pages),
                'edges': edges, 'observed_doublets': observed,
                'expected_doublets': str(Fraction(edges, 29)), 'variance': str(Fraction(edges*28, 29**2)),
                'inclusive_lower_tail': str(probability), 'decimal_precision': 80,
                'exact_tail': {'numerator_formula': 'sum(comb(E,j)*28**(E-j) for j in range(D+1))',
                               'denominator_formula': '29**E', 'integer_encoding': 'Python hex(integer), ASCII bytes including 0x prefix',
                               'numerator_sha256': sha(hex(numerator).encode('ascii')),
                               'denominator_sha256': sha(hex(denominator).encode('ascii'))},
                'plot_bins': [{'start': i*10, 'end_inclusive': i*10+9 if i < 65 else edges,
                               'probability': str(value)} for i, value in enumerate(bins)],
                'limits': 'Replication selected after the low count was known. Conditional model tail, not a language probability, proof of impossibility or adjustment for historical feature selection. No fixed-count shuffle or multiplicative-running-sum model is tested.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.check and args.write:
        parser.error('Choose --check or --write')
    result = report()
    target = HERE / 'results.json'
    if args.check:
        assert result == json.loads(target.read_bytes())
        print('PASS: input hashes, per-page recount, exact binomial tail and plotting bins reproduce')
    elif args.write:
        target.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8', newline='\n')
        print('Wrote results; independent check remains required')
    else:
        print(json.dumps(result, indent=2))
