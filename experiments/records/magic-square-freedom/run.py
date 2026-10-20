"""Exact linear constraints and positive-integer counterexamples; no dependencies."""
import argparse
from fractions import Fraction
from functools import reduce
import hashlib
import json
from math import gcd, lcm
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def constraints(n, symmetry, fixed=None):
    """Rows act on differences, so their right-hand side is always zero."""
    rows = []
    for cells in (
        [[r*n+c for c in range(n)] for r in range(n)]
        + [[r*n+c for r in range(n)] for c in range(n)]
        + [[i*n+i for i in range(n)], [i*n+n-1-i for i in range(n)]]
    ):
        row = [0] * (n*n)
        for cell in cells:
            row[cell] += 1
        rows.append(row)
    for i in range(n*n):
        partners = []
        if "half-turn" in symmetry:
            partners.append(n*n-1-i)
        if "transpose" in symmetry:
            partners.append((i % n)*n+i//n)
        for j in partners:
            if i < j:
                row = [0] * (n*n)
                row[i], row[j] = 1, -1
                rows.append(row)
    if fixed is not None:
        row = [0] * (n*n)
        row[fixed] = 1
        rows.append(row)
    return rows


def nullspace(rows):
    """RREF over Q, with deterministic left-to-right pivots."""
    a = [[Fraction(x) for x in row] for row in rows]
    width = len(a[0])
    pivots = []
    for c in range(width):
        k = len(pivots)
        pivot = next((r for r in range(k, len(a)) if a[r][c]), None)
        if pivot is None:
            continue
        a[k], a[pivot] = a[pivot], a[k]
        divisor = a[k][c]
        a[k] = [x/divisor for x in a[k]]
        for r in range(len(a)):
            if r != k and a[r][c]:
                multiplier = a[r][c]
                a[r] = [x-multiplier*y for x, y in zip(a[r], a[k])]
        pivots.append(c)
    free = [c for c in range(width) if c not in pivots]
    basis = []
    for c in free:
        v = [Fraction(0)] * width
        v[c] = Fraction(1)
        for r, pivot in enumerate(pivots):
            v[pivot] = -a[r][c]
        basis.append(v)
    return pivots, free, basis


def primitive(v):
    scale = lcm(*(x.denominator for x in v))
    integers = [int(x*scale) for x in v]
    factor = reduce(gcd, integers)
    return [x//factor for x in integers]


def matrices():
    alphabet = {a["rune"]: a["prime"] for a in
                json.loads((ROOT/"data/index.json").read_text(encoding="utf-8"))["alphabet"]}
    result = {}
    for page in ("lp1-05", "lp1-16"):
        raw = json.loads((ROOT/f"data/pages/{page}.json").read_text(encoding="utf-8"))["raw"]
        rows = [line.rstrip("/").split("-") for line in raw.splitlines()
                if re.search(r"[0-9]", line)]
        assert len(rows) == 5 and all(len(r) == 5 for r in rows)
        result[page] = [[int(s) if s.isdecimal() else sum(alphabet[ch] for ch in s)
                         for s in row] for row in rows]
    return result


def report():
    plan = json.loads((HERE/"plan.json").read_text(encoding="utf-8"))
    cases = []
    for n in plan["cases"]["orders"]:
        for symmetry in plan["cases"]["symmetries"]:
            rows = constraints(n, symmetry)
            pivots, free, basis = nullspace(rows)
            case = {"order": n, "symmetry": symmetry, "equations": len(rows),
                    "variables": n*n, "rank": len(pivots), "dimension": len(free),
                    "free_cells_zero_based": free,
                    "rational_basis": [[str(x) for x in v] for v in basis]}
            if symmetry == "half-turn":
                case["dimension_with_each_cell_fixed"] = [
                    len(nullspace(constraints(n, symmetry, i))[1]) for i in range(n*n)]
            cases.append(case)
    examples = []
    for page, grid in matrices().items():
        flat = sum(grid, [])
        for cell in range(25):
            _, _, basis = nullspace(constraints(5, "half-turn", cell))
            direction = primitive(basis[0])
            candidates = [[x+sign*d for x, d in zip(flat, direction)] for sign in (1, -1)]
            changed = next((v for v in candidates if min(v) > 0), None)
            examples.append({
                "page": page, "fixed_cell_one_based": [cell//5+1, cell % 5+1],
                "fixed_value": flat[cell], "line_sum": sum(grid[0]), "original": grid,
                "primitive_direction": [direction[r*5:(r+1)*5] for r in range(5)],
                "positive_counterexample": (
                    [changed[r*5:(r+1)*5] for r in range(5)] if changed is not None else None)})
    inputs = ["data/index.json", "data/pages/lp1-05.json", "data/pages/lp1-16.json",
              str((HERE/"plan.json").relative_to(ROOT)).replace("\\", "/")]
    return {"scope": "Rational dimensions for fixed line sums; constructive positive-integer nonuniqueness.",
            "input_sha256": {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs},
            "cases": cases, "counterexamples": examples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    target = HERE/"results.json"
    if args.write:
        target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8", newline="\n")
    if args.check:
        assert result == json.loads(target.read_text(encoding="utf-8"))
        print("PASS exact recomputation")
    for c in result["cases"]:
        print(c["order"], c["symmetry"], "rank", c["rank"], "dimension", c["dimension"])
    print("Positive counterexamples:", sum(e["positive_counterexample"] is not None
                                          for e in result["counterexamples"]), "/ 50")


if __name__ == "__main__":
    main()
