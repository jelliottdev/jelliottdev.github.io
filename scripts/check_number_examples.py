"""Exact arithmetic examples for reference articles; not a cipher search."""
from math import isqrt
import json

def prime(n):
    return n >= 2 and all(n % d for d in range(2, isqrt(n) + 1))

def main():
    primes = [n for n in range(2, 100000) if prime(n)]
    square = [[272,138,341,131,151], [366,199,130,320,18],
              [226,245,91,245,226], [18,320,130,199,366],
              [151,131,341,138,272]]
    lines = [sum(row) for row in square]
    lines += [sum(row[c] for row in square) for c in range(5)]
    lines += [sum(square[i][i] for i in range(5)),
              sum(square[i][4-i] for i in range(5))]
    assert set(lines) == {1033}
    assert primes[3299-1] == 30557
    assert primes[9467-1] == 98597
    positions = {str(n): primes.index(n) + 1 for n in (3299, 7649, 9467, 30557, 98597)}
    assert positions == {"3299": 463, "7649": 971, "9467": 1173,
                         "30557": 3299, "98597": 9467}
    assert prime(7649) and prime(9467)
    assert 98597*30557 == 3012828529
    assert 9857*30557 == 301200349
    print(json.dumps({
        "prime_index_convention": "one-based: p_1 = 2",
        "p_3299": primes[3298], "p_9467": primes[9466],
        "prime_value_to_one_based_position": positions,
        "7649_and_decimal_reverse_are_prime": True,
        "98597_times_30557": 98597*30557,
        "9857_times_30557": 9857*30557,
        "historical_square_line_sums": lines,
        "scope": "Arithmetic and cited historical square only; no decryption claim."
    }, indent=2))

if __name__ == "__main__":
    main()
