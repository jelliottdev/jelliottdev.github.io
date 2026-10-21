"""Independent regex recount, exact integer recurrence and finite controls."""
from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def check():
    report = json.loads((HERE / 'results.json').read_bytes())
    for path, digest in report['input_sha256'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    alphabet = ''.join(a['rune'] for a in json.loads((ROOT / 'data/index.json').read_bytes())['alphabet'])
    counts = []
    for n in range(56):
        page = f'lp2-{n:02}'
        stream = ''.join(re.findall('['+re.escape(alphabet)+']', (ROOT / f'text/{page}.txt').read_text(encoding='utf-8')))
        counts.append({'page': page, 'runes': len(stream), 'edges': max(len(stream)-1, 0),
                       'doublets': len(re.findall(r'(?=(.)\1)', stream))})
    assert counts == report['pages']
    e = sum(p['edges'] for p in counts)
    d = sum(p['doublets'] for p in counts)
    assert e == report['edges'] and d == report['observed_doublets']
    assert sum(p['runes'] for p in counts) == report['runes']
    assert sum(p['runes'] > 0 for p in counts) == report['nonempty_pages']
    assert Fraction(report['expected_doublets']) == Fraction(e, 29)
    assert Fraction(report['variance']) == Fraction(e*28, 841)
    # Integer mass recurrence, rather than comb() and powers for every tail term.
    mass, total = 28**e, 0
    bin_integers = [0] * 66
    for j in range(e+1):
        bin_integers[min(j//10, 65)] += mass
        if j <= d:
            total += mass
        if j < e:
            mass, remainder = divmod(mass*(e-j), (j+1)*28)
            assert remainder == 0
    denominator = 29**e
    assert sum(bin_integers) == denominator
    for name, value in [('numerator', total), ('denominator', denominator)]:
        assert hashlib.sha256(hex(value).encode('ascii')).hexdigest() == report['exact_tail'][name+'_sha256']
    with localcontext() as context:
        context.prec = 80
        assert str(Decimal(total)/Decimal(denominator)) == report['inclusive_lower_tail']
        assert len(report['plot_bins']) == 66
        for i, (saved, integer) in enumerate(zip(report['plot_bins'], bin_integers)):
            assert saved['start'] == i*10 and saved['end_inclusive'] == (i*10+9 if i < 65 else e)
            assert abs(Decimal(saved['probability'])-Decimal(integer)/Decimal(denominator)) < Decimal('1e-70')
    # Exhaust overlapping edges, separate anchors and empty/singleton pages.
    controls = 0
    for q in (2, 3):
        for lengths in ((0,), (1,), (4,), (2, 2), (0, 3, 1), (3, 2)):
            edges = sum(max(0, n-1) for n in lengths)
            actual = Counter()
            for symbols in itertools.product(range(q), repeat=sum(lengths)):
                offset, matches = 0, 0
                for length in lengths:
                    page = symbols[offset:offset+length]
                    matches += sum(page[i] == page[i+1] for i in range(max(0, length-1)))
                    offset += length
                actual[matches] += 1
            for k in range(edges+1):
                assert Fraction(actual[k], q**sum(lengths)) == Fraction(math.comb(edges, k)*(q-1)**(edges-k), q**edges)
            controls += 1
    # Nonuniform iid binary symbols: overlapping equality indicators are dependent.
    p = Fraction(3, 4)
    marginal = p*p+(1-p)**2
    joint = p**3+(1-p)**3
    assert (marginal, joint, marginal*marginal) == (Fraction(5, 8), Fraction(7, 16), Fraction(25, 64))
    assert joint != marginal*marginal
    return {'pages_checked': len(counts), 'finite_distribution_controls': controls,
            'binomial_bins_checked': 66, 'exact_tail_hashes_match': True,
            'nonuniform_counterexample': {'single_match': str(marginal), 'two_overlapping_matches': str(joint), 'product_of_marginals': str(marginal*marginal)}}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
