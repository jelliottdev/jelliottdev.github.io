"""Finite controls for phasewise affine equality; no manuscript exclusion.

The general proof uses invertibility of the multiplier. This exhaustive check
covers every multiplier, intercept and input pair for moduli 28 and 29.
"""
import argparse
import hashlib
import json
from math import gcd
from pathlib import Path


def pairs(values):
    return sum(x == y for i, x in enumerate(values) for y in values[:i])


def calculate():
    counts = []
    for modulus in (28, 29):
        maps, comparisons = 0, 0
        units = [a for a in range(modulus) if gcd(a, modulus) == 1]
        for a in units:
            inverse = pow(a, -1, modulus)
            for b in range(modulus):
                output = [(a*x+b) % modulus for x in range(modulus)]
                assert len(set(output)) == modulus
                assert all((inverse*(y-b)) % modulus == x for x, y in enumerate(output))
                for x in range(modulus):
                    for y in range(modulus):
                        assert (output[x] == output[y]) == (x == y)
                        comparisons += 1
                maps += 1
        counts.append({'modulus': modulus, 'unit_multipliers': units,
                       'affine_maps': maps, 'ordered_pair_checks': comparisons})
    # Period two, input ordinal starting at zero. Phase maps add 0 and 1.
    original = [0, 0, 1, 0, 1]
    transformed = [(x + i % 2) % 29 for i, x in enumerate(original)]
    phase_pairs = [pairs(original[r::2]) for r in range(2)]
    assert phase_pairs == [pairs(transformed[r::2]) for r in range(2)]
    assert (pairs(original), pairs(transformed)) == (4, 6)
    assert (2*0) % 28 == (2*14) % 28  # Nonzero is not sufficient modulo 28.
    return {'scope': __doc__, 'finite_checks': counts,
            'example': {'modulus': 29, 'period': 2, 'input': original, 'output': transformed,
                        'phase_maps': ['x', 'x+1 mod 29'],
                        'input_phase_streams': [original[r::2] for r in range(2)],
                        'output_phase_streams': [transformed[r::2] for r in range(2)],
                        'unordered_matching_pairs_by_phase': phase_pairs,
                        'whole_stream_matching_pairs_before_after': [4, 6],
                        'whole_stream_ioc_before_after': ['2/5', '3/5']},
            'nonunit_counterexample': {'modulus': 28, 'multiplier': 2, 'intercept': 0,
                                      'distinct_inputs': [0, 14], 'equal_outputs': [0, 0]},
            'limits': 'Invented inputs; no manuscript or period sweep. Fixed phases, fixed injective maps, no skipped slots. Finite checks are not a proof-assistant replay. General-modulus proof is algebraic.',
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = calculate()
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report['finite_checks']))
