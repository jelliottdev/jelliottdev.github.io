"""Exact length counts and explicit descriptive statistics for corpus prefixes.

This module does not infer language, remove headers, normalize symbols, or
interpret empirical tail fractions as calibrated hypothesis-test p-values.
"""
from collections import Counter
from fractions import Fraction
import math


def prefix(raw, size=2902):
    if not isinstance(size, int) or isinstance(size, bool) or size < 2:
        raise ValueError('Prefix size must be an integer of at least two')
    tokens = [t for t in raw.decode('utf-8').split(' ') if t]
    return [len(t) for t in tokens[:size]] if len(tokens) >= size else None


def summarize(lengths):
    if len(lengths) < 2 or any(type(n) is not int or n < 1 for n in lengths):
        raise ValueError('Need at least two positive integer lengths')
    n = len(lengths)
    ordered = sorted(lengths)
    mean = Fraction(sum(lengths), n)
    variance = sum((Fraction(x)-mean)**2 for x in lengths)/(n-1)
    def quantile(q):
        position = (n-1)*q
        low = position.numerator//position.denominator
        weight = position-low
        return ordered[low]*(1-weight)+ordered[min(low+1,n-1)]*weight
    return {'tokens': n, 'counted_units': sum(lengths),
            'histogram': {str(k): v for k,v in sorted(Counter(lengths).items())},
            'mean': float(mean), 'sample_variance': float(variance),
            'sample_std': math.sqrt(variance), 'median': float(quantile(Fraction(1,2))),
            'percentile_25': float(quantile(Fraction(1,4))),
            'percentile_75': float(quantile(Fraction(3,4))),
            'min': min(lengths), 'max': max(lengths)}


def tails(values, threshold):
    if not values:
        raise ValueError('Empty reference population')
    less = sum(x < threshold for x in values)
    equal = sum(x == threshold for x in values)
    greater = sum(x > threshold for x in values)
    return {'n': len(values), 'less': less, 'equal': equal, 'greater': greater,
            'inclusive_left_numerator': less+equal,
            'inclusive_right_numerator': greater+equal}
