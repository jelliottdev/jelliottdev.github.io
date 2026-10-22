"""Independently verify the saved LP2-15 Mobius panel by square-divisor search."""
import json
from math import isqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def is_prime(n):
    if n < 2:
        return False
    return all(n % d for d in range(2, isqrt(n) + 1))


def independent_mobius(n):
    for candidate in range(2, isqrt(n) + 1):
        if is_prime(candidate) and n % (candidate * candidate) == 0:
            return 0
    distinct = sum(n % candidate == 0 for candidate in range(2, n + 1) if is_prime(candidate))
    return -1 if distinct % 2 else 1


def main():
    numbers = json.loads((ROOT / 'data/pages/lp2-15.json').read_text(encoding='utf-8'))['numbers']
    saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    assert saved['numbers'] == numbers
    assert len(saved['cells']) == 16
    for row in range(4):
        for col in range(4):
            n = numbers[row][col]
            cell = saved['cells'][4 * row + col]
            mu = independent_mobius(n)
            assert (cell['row'], cell['column'], cell['printed'], cell['mobius']) == (row + 1, col + 1, n, mu)
            assert saved['mobius_matrix'][row][col] == mu
            assert n == __import__('math').prod(p ** k for p, k in cell['factorization'])
            assert all(is_prime(p) for p, _ in cell['factorization'])
    assert saved['counts'] == {str(v): sum(independent_mobius(n) == v for row in numbers for n in row) for v in (-1, 0, 1)}
    print('Independent square-divisor and prime-factor check passed for all 16 cells.')


if __name__ == '__main__':
    main()
