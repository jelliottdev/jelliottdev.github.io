"""Independent constraint construction, modular rank, and direct witness checks."""
from fractions import Fraction
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def equations(n, symmetry, fixed=None):
    """Construct coefficients from predicates, separately from run.py."""
    positions = [(r, c) for r in range(n) for c in range(n)]
    rows = [[int(r == k) for r, c in positions] for k in range(n)]
    rows += [[int(c == k) for r, c in positions] for k in range(n)]
    rows += [[int(r == c) for r, c in positions],
             [int(r+c == n-1) for r, c in positions]]
    for r, c in positions:
        if "half-turn" in symmetry:
            rows.append([int((a, b) == (r, c))-int((a, b) == (n-1-r, n-1-c))
                         for a, b in positions])
        if "transpose" in symmetry:
            rows.append([int((a, b) == (r, c))-int((a, b) == (c, r))
                         for a, b in positions])
    if fixed is not None:
        rows.append([int(i == fixed) for i in range(n*n)])
    return rows


def modular_rank(rows, prime):
    a = [[x % prime for x in row] for row in rows]
    rank = 0
    for col in range(len(a[0])):
        pivot = next((k for k in range(rank, len(a)) if a[k][col]), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        inv = pow(a[rank][col], -1, prime)
        for k in range(rank+1, len(a)):
            scale = a[k][col]*inv % prime
            a[k] = [(v-scale*w) % prime for v, w in zip(a[k], a[rank])]
        rank += 1
    return rank


def verify_grid(grid, target):
    n = len(grid)
    assert all(len(row) == n for row in grid)
    assert all(type(x) is int and x > 0 for row in grid for x in row)
    assert all(sum(row) == target for row in grid)
    assert all(sum(grid[r][c] for r in range(n)) == target for c in range(n))
    assert sum(grid[i][i] for i in range(n)) == target
    assert sum(grid[i][n-1-i] for i in range(n)) == target
    assert all(grid[r][c] == grid[n-1-r][n-1-c] for r in range(n) for c in range(n))


def main():
    result = json.loads((HERE/"results.json").read_text(encoding="utf-8"))
    for case in result["cases"]:
        n, symmetry = case["order"], case["symmetry"]
        rows = equations(n, symmetry)
        basis = [[Fraction(x) for x in v] for v in case["rational_basis"]]
        free = case["free_cells_zero_based"]
        assert len(basis) == len(free) == case["dimension"]
        # Identity restriction proves independence of the displayed null vectors.
        for i, v in enumerate(basis):
            assert [v[j] for j in free] == [int(i == j) for j in range(len(free))]
            assert all(sum(a*b for a, b in zip(row, v)) == 0 for row in rows)
        # Modular rank is a lower bound on rational rank. Matching the upper
        # bound from the independent null vectors certifies exact rational rank.
        for prime in (1000000007, 1000000009):
            assert modular_rank(rows, prime) == case["rank"] == n*n-len(basis)
        if symmetry == "half-turn":
            for cell, dimension in enumerate(case["dimension_with_each_cell_fixed"]):
                evaluation_is_nonzero = any(v[cell] for v in basis)
                assert dimension == len(basis)-int(evaluation_is_nonzero)
                assert n*n-modular_rank(equations(n, symmetry, cell), 1000000007) == dimension
    known = {(c["order"], c["symmetry"]): c["dimension"] for c in result["cases"]}
    assert known[3, "none"] == 2
    assert known[3, "half-turn"] == 0
    # Historical values duplicated here deliberately, independently of the parser.
    original = {
        "lp1-05": [[272,138,341,131,151],[366,199,130,320,18],
                   [226,245,91,245,226],[18,320,130,199,366],[151,131,341,138,272]],
        "lp1-16": [[434,1311,312,278,966],[204,812,934,280,1071],
                   [626,620,809,620,626],[1071,280,934,812,204],[966,278,312,1311,434]]}
    seen = set()
    for example in result["counterexamples"]:
        page = example["page"]
        r, c = [x-1 for x in example["fixed_cell_one_based"]]
        assert (page, r, c) not in seen
        seen.add((page, r, c))
        assert example["original"] == original[page]
        changed = example["positive_counterexample"]
        verify_grid(original[page], example["line_sum"])
        verify_grid(changed, example["line_sum"])
        assert changed != original[page]
        assert changed[r][c] == original[page][r][c] == example["fixed_value"]
    assert len(seen) == 50
    print("PASS: all 12 exact ranks certified; fixed-cell dimensions checked; 50 positive counterexamples verified.")


if __name__ == "__main__":
    main()
