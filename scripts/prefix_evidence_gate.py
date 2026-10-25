"""Pure finite-prefix evidence helpers; no target decoding or file access."""
from math import gcd


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def inverse_affine_prefix(expected, a, b, modulus=29):
    """Return the unique preimage of a fixed prefix under a*x+b modulo m."""
    if not all(_integer(v) for v in (a, b, modulus)) or modulus < 2 or gcd(a, modulus) != 1:
        raise ValueError('An invertible integer affine mapping is required')
    if not isinstance(expected, (list, tuple)) or not expected or any(not _integer(v) or not 0 <= v < modulus for v in expected):
        raise ValueError('Expected a nonempty canonical prefix')
    inv = pow(a, -1, modulus)
    return [(inv * (v-b)) % modulus for v in expected]


def first_mismatch(observed, expected):
    """Locate a witnessed mismatch; a truncated agreeing prefix proves nothing."""
    return next((i for i, (a, b) in enumerate(zip(observed, expected)) if a != b), None)


def reset_prefix_compatibility(mismatch, first_changed_reset):
    """A mismatch excludes a variant only strictly before its first change."""
    if mismatch is None:
        return False
    if not _integer(mismatch) or mismatch < 0:
        raise ValueError('Mismatch must be a nonnegative rune offset')
    if first_changed_reset is not None and (not _integer(first_changed_reset) or first_changed_reset < 0):
        raise ValueError('Reset must be a nonnegative rune offset')
    return first_changed_reset is None or mismatch < first_changed_reset
