"""Exact arithmetic examples for reference articles; not a cipher search."""
from math import isqrt, gcd
from itertools import permutations
from bisect import bisect_right
import json
import re
import hashlib
from pathlib import Path

def prime(n):
    return n >= 2 and all(n % d for d in range(2, isqrt(n) + 1))

def report(root=Path(__file__).resolve().parents[1]):
    primes = [n for n in range(2, 100000) if prime(n)]
    square = [[272,138,341,131,151], [366,199,130,320,18],
              [226,245,91,245,226], [18,320,130,199,366],
              [151,131,341,138,272]]
    lines = [sum(row) for row in square]
    lines += [sum(row[c] for row in square) for c in range(5)]
    lines += [sum(square[i][i] for i in range(5)),
              sum(square[i][4-i] for i in range(5))]
    assert set(lines) == {1033}
    # Read the printed decimal rows from the shipped transcription, not rune values.
    mixed_bytes = (root / "data/pages/lp1-05.json").read_bytes()
    mixed_record = json.loads(mixed_bytes)
    alphabet_bytes = (root / "data/index.json").read_bytes()
    alphabet = {entry["rune"]: entry for entry in json.loads(alphabet_bytes)["alphabet"]}
    mixed_rows = [line.rstrip("/").split("-")
                  for line in mixed_record["raw"].splitlines()
                  if re.search(r"[0-9]", line)]
    assert len(mixed_rows) == 5 and all(len(row) == 5 for row in mixed_rows)
    cells = []
    converted = []
    for row_number, row in enumerate(mixed_rows, 1):
        values = []
        for column_number, token in enumerate(row, 1):
            value = int(token) if token.isdecimal() else sum(alphabet[rune]["prime"] for rune in token)
            values.append(value)
            if not token.isdecimal():
                cells.append({"row": row_number, "column": column_number,
                              "labels": [alphabet[rune]["latin"] for rune in token],
                              "prime_values": [alphabet[rune]["prime"] for rune in token],
                              "sum": value})
        converted.append(values)
    assert converted == square
    opposite_pairs = []
    for r in range(5):
        for c in range(5):
            if r * 5 + c >= 12:
                continue  # Count each opposite pair once; omit the fixed center.
            other_r, other_c = 4 - r, 4 - c
            left, right = mixed_rows[r][c], mixed_rows[other_r][other_c]
            def label(token):
                return token if token.isdecimal() else "".join(alphabet[ch]["latin"] for ch in token)
            opposite_pairs.append({
                "positions": [[r + 1, c + 1], [other_r + 1, other_c + 1]],
                "labels": [label(left), label(right)],
                "same_printed_token": left == right,
                "values": [converted[r][c], converted[other_r][other_c]],
            })
    assert all(pair["values"][0] == pair["values"][1] for pair in opposite_pairs)
    assert sum(not pair["same_printed_token"] for pair in opposite_pairs) == 5
    record_bytes = (root / "data/pages/lp1-16.json").read_bytes()
    record = json.loads(record_bytes)
    printed = [[int(value) for value in line.rstrip("/").split("-")]
               for line in record["raw"].splitlines()
               if re.fullmatch(r"[0-9]+(?:-[0-9]+){4}/", line)]
    assert len(printed) == 5
    printed_rows = [sum(row) for row in printed]
    printed_columns = [sum(row[c] for row in printed) for c in range(5)]
    printed_diagonals = [sum(printed[i][i] for i in range(5)),
                         sum(printed[i][4-i] for i in range(5))]
    assert printed_rows + printed_columns + printed_diagonals == [3301] * 12
    rotated = [list(reversed(row)) for row in reversed(printed)]
    assert printed == rotated
    assert primes[3299-1] == 30557
    assert primes[9467-1] == 98597
    positions = {str(n): primes.index(n) + 1 for n in (3299, 7649, 9467, 30557, 98597)}
    assert positions == {"3299": 463, "7649": 971, "9467": 1173,
                         "30557": 3299, "98597": 9467}
    assert prime(7649) and prime(9467)
    assert 98597*30557 == 3012828529
    assert 9857*30557 == 301200349
    panel_bytes = (root / "data/pages/lp2-15.json").read_bytes()
    panel_record = json.loads(panel_bytes)
    panel = panel_record["numbers"]
    assert len(panel) == 4 and all(len(row) == 4 for row in panel)
    differences = [[3301 - value for value in row] for row in panel]
    difference_primes = [[prime(value) for value in row] for row in differences]
    assert differences == [[43, 79, 149, 263], [23, 2, 3, 463],
                           [13, 7, 5, 829], [-1215, 2095, 2593, 1481]]
    assert sum(sum(row) for row in difference_primes) == 14
    assert 2095 == 5 * 419 and prime(419)
    # Audit a fixed supplied numerical chain; Q is constructed, not printed.
    q = [primes[i:i+4] for i in range(0, 16, 4)]
    determinant = 0
    for order in permutations(range(4)):
        inversions = sum(order[i] > order[j] for i in range(4) for j in range(i+1, 4))
        term = (-1) ** inversions
        for row, col in enumerate(order):
            term *= q[row][col]
        determinant += term
    trace = sum(q[i][i] for i in range(4))
    s16 = sum(map(sum, differences))
    s14 = sum(value for row in differences for value in row if prime(value))
    pi14, pi16 = bisect_right(primes, s14), bisect_right(primes, s16)
    totients = {str(n): sum(gcd(k, n) == 1 for k in range(1, n+1))
                for n in [880, s14, s16]}
    assert (s14, s16, s16-s14) == (5953, 6833, 880)
    assert prime(s14) and prime(s16)
    assert (pi14, pi16, pi16-pi14, determinant, trace) == (781, 880, 99, 880, 99)
    assert totients == {'880': 320, '5953': 5952, '6833': 6832}
    chain = {'constructed_first_16_primes_row_major': q,
             'determinant': determinant, 'trace': trace,
             'sum_14_prime_differences': s14, 'sum_all_16_differences': s16,
             'difference_between_sums': s16-s14,
             'prime_counting': {str(s14): pi14, str(s16): pi16},
             'prime_count_difference': pi16-pi14, 'totients': totients,
             'selection': 'Fixed supplied chain; no search of alternative constants, layouts or functions; no probability claim.'}
    product_digits = [int(digit) for digit in str(98597 * 30557)]
    digit_primes = primes[:len(product_digits)]
    digit_sums = [digit + value for digit, value in zip(product_digits, digit_primes)]
    assert digit_sums == [5, 3, 6, 9, 19, 15, 25, 24, 25, 38]
    return {
        "prime_index_convention": "one-based: p_1 = 2",
        "p_3299": primes[3298], "p_9467": primes[9466],
        "prime_value_to_one_based_position": positions,
        "7649_and_decimal_reverse_are_prime": True,
        "98597_times_30557": 98597*30557,
        "9857_times_30557": 9857*30557,
        "product_digit_prime_addition": {
            "rule": "Read product digits left to right; add consecutive primes starting at 2; no skips, resets or substitutions.",
            "digits": product_digits, "primes": digit_primes, "sums": digit_sums,
            "residues_mod_29": [value % 29 for value in digit_sums],
            "scope": "A defined arithmetic sequence, not a ciphertext decoding or validation of its proposed origin.",
        },
        "historical_square_line_sums": lines,
        "lp1_05": {
            "source": "data/pages/lp1-05.json",
            "source_sha256": hashlib.sha256(mixed_bytes).hexdigest(),
            "alphabet_source_sha256": hashlib.sha256(alphabet_bytes).hexdigest(),
            "image_sha256": mixed_record["image_sha256"],
            "rune_cells": cells,
            "converted_matrix": converted,
            "half_turn_pairs": opposite_pairs,
            "printed_tokens_half_turn_symmetric": all(pair["same_printed_token"] for pair in opposite_pairs),
            "converted_values_half_turn_symmetric": True,
            "line_sums": lines,
        },
        "lp2_15": {
            "source": "data/pages/lp2-15.json",
            "source_sha256": hashlib.sha256(panel_bytes).hexdigest(),
            "image_sha256": panel_record["image_sha256"],
            "matrix": panel,
            "difference_rule": "3301 minus each printed entry, retaining row and column order; no absolute value or modular reduction.",
            "differences_from_3301": differences,
            "difference_is_prime": difference_primes,
            "prime_difference_count": sum(sum(row) for row in difference_primes),
            "constructed_matrix_chain": chain,
            "positive_composite_factorization": {"2095": [5, 419]},
            "interpretation": "Derived arithmetic for all sixteen entries; no claim about statistical surprise or intended cipher.",
        },
        "lp1_16": {
            "source": "data/pages/lp1-16.json",
            "source_sha256": hashlib.sha256(record_bytes).hexdigest(),
            "image_sha256": record["image_sha256"],
            "matrix": printed,
            "row_sums": printed_rows,
            "column_sums": printed_columns,
            "diagonal_sums": printed_diagonals,
            "total": sum(printed_rows),
            "half_turn_symmetric": printed == rotated,
            "normal": sorted(value for row in printed for value in row) == list(range(1, 26)),
        },
        "scope": "Prime lookups and product-digit arithmetic, LP1-05 rune-value conversion, printed LP1-16 panel, and LP2-15 differences from 3301; no new decryption claim."
    }

def main():
    print(json.dumps(report(), indent=2))

if __name__ == "__main__":
    main()
