"""Exact arithmetic examples for reference articles; not a cipher search."""
from math import isqrt
import json
import re
import hashlib
from pathlib import Path

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
    # Read the printed decimal rows from the shipped transcription, not rune values.
    root = Path(__file__).resolve().parents[1]
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
    print(json.dumps({
        "prime_index_convention": "one-based: p_1 = 2",
        "p_3299": primes[3298], "p_9467": primes[9466],
        "prime_value_to_one_based_position": positions,
        "7649_and_decimal_reverse_are_prime": True,
        "98597_times_30557": 98597*30557,
        "9857_times_30557": 9857*30557,
        "historical_square_line_sums": lines,
        "lp1_05": {
            "source": "data/pages/lp1-05.json",
            "source_sha256": hashlib.sha256(mixed_bytes).hexdigest(),
            "alphabet_source_sha256": hashlib.sha256(alphabet_bytes).hexdigest(),
            "image_sha256": mixed_record["image_sha256"],
            "rune_cells": cells,
            "converted_matrix": converted,
            "line_sums": lines,
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
        "scope": "Arithmetic of the LP1-05 rune-value conversion and printed LP1-16 panel; no new decryption claim."
    }, indent=2))

if __name__ == "__main__":
    main()
