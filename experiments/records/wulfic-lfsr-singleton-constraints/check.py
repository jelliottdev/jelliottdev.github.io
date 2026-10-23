"""Independent page parser, small-grid oracle and every published witness check."""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import re
from collections import Counter
from pathlib import Path

from controls import controls
from finalize import decode

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNE_ORDER = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛂᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
INDEX = {c: i for i, c in enumerate(RUNE_ORDER)}
INDEX["ᛄ"] = 11


def independent_page(page: dict) -> None:
    data = (ROOT / page["site_page_path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == page["site_page_sha256"]
    raw = json.loads(data)["raw"].strip()
    chunks = [s for s in re.split(r"[-•\n /.]", raw) if s]
    words = [[INDEX[c] for c in chunk if c in INDEX] for chunk in chunks]
    words = [w for w in words if w]
    runes = list(itertools.chain.from_iterable(words))
    singles = []
    pos = 0
    for word in words:
        if len(word) == 1:
            singles.append(pos)
        pos += len(word)
    assert runes == page["runes"]
    assert singles == page["singleton_positions"]


def basis(coeff: tuple[int, ...], last: int) -> list[list[int]]:
    length = len(coeff)
    out = [[int(i == j) for j in range(length)] for i in range(length)]
    for i in range(length, last + 1):
        out.append([sum(coeff[k] * out[i - length + k][j] for k in range(length)) % 29 for j in range(length)])
    return out


def inverse(matrix: list[list[int]]) -> list[list[int]] | None:
    n = len(matrix)
    aug = [[*row, *(int(i == j) for j in range(n))] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = next((r for r in range(col, n) if aug[r][col]), None)
        if pivot is None:
            return None
        aug[pivot], aug[col] = aug[col], aug[pivot]
        factor = pow(aug[col][col], -1, 29)
        aug[col] = [(x * factor) % 29 for x in aug[col]]
        for r in range(n):
            if r != col:
                factor = aug[r][col]
                aug[r] = [(x - factor * y) % 29 for x, y in zip(aug[r], aug[col])]
    return [row[n:] for row in aug]


def oracle(page: dict, length: int, codes: int) -> dict[str, tuple[int, int, int]]:
    positions, cipher = page["singleton_positions"], page["runes"]
    assert len(positions) >= length
    out = {m: [0, 0, 0] for m in ("sub", "add", "beaufort")}
    for code in range(codes):
        x = code
        coeff = []
        for _ in range(length):
            coeff.append(x % 29)
            x //= 29
        alpha = basis(tuple(coeff), positions[-1])
        inv = inverse([alpha[pos] for pos in positions[:length]])
        if inv is None:
            continue
        for mode in out:
            out[mode][0] += 1
            for mask in range(1 << length):
                guessed = [24 if mask & (1 << i) else 10 for i in range(length)]
                if mode == "sub":
                    rhs = [(cipher[pos] - p) % 29 for pos, p in zip(positions, guessed)]
                elif mode == "add":
                    rhs = [(p - cipher[pos]) % 29 for pos, p in zip(positions, guessed)]
                else:
                    rhs = [(cipher[pos] + p) % 29 for pos, p in zip(positions, guessed)]
                state = [sum(row[j] * rhs[j] for j in range(length)) % 29 for row in inv]
                hits = length
                for pos in positions[length:]:
                    key = sum(v * s for v, s in zip(alpha[pos], state)) % 29
                    c = cipher[pos]
                    p = (c - key) % 29 if mode == "sub" else (c + key) % 29 if mode == "add" else (key - c) % 29
                    hits += p in (10, 24)
                out[mode][1] = max(out[mode][1], hits)
                out[mode][2] += hits == len(positions)
    return {k: tuple(v) for k, v in out.items()}


def tabrows(name: str) -> dict[tuple[str, int, str], dict]:
    rows = list(csv.DictReader((HERE / name).open(encoding="utf-8"), delimiter="\t"))
    return {(r["page"], int(r["length"]), r["mode"]): r for r in rows}


def independent_small_field_controls() -> None:
    """Exhaust every tap/state in toy fields, with nonconsecutive cribs."""
    def invert_q(matrix: list[list[int]], q: int) -> list[list[int]] | None:
        n = len(matrix)
        a = [[*row, *(int(i == j) for j in range(n))] for i, row in enumerate(matrix)]
        for col in range(n):
            pivot = next((i for i in range(col, n) if a[i][col] % q), None)
            if pivot is None:
                return None
            a[pivot], a[col] = a[col], a[pivot]
            factor = pow(a[col][col], -1, q)
            a[col] = [(v * factor) % q for v in a[col]]
            for i in range(n):
                if i != col:
                    factor = a[i][col]
                    a[i] = [(v - factor * u) % q for v, u in zip(a[i], a[col])]
        return [row[n:] for row in a]

    cases = 0
    for q, lengths in ((3, (1, 2, 3)), (5, (1, 2))):
        for length in lengths:
            positions = [1, 3, 5, 7, 9][:max(length + 1, 4)]
            ciphertext = [(2 * i + 1) % q for i in positions]
            nonsingular = 0
            for taps in itertools.product(range(q), repeat=length):
                # Basis is independently generated modulo q, not by the GF(29) scanner.
                alpha = [[int(i == j) for j in range(length)] for i in range(length)]
                for n in range(length, positions[-1] + 1):
                    alpha.append([sum(taps[k] * alpha[n - length + k][j] for k in range(length)) % q for j in range(length)])
                inverse_q = invert_q([alpha[p] for p in positions[:length]], q)
                if inverse_q is None:
                    continue
                nonsingular += 1
                via_constraints: set[tuple[int, ...]] = set()
                for plain in itertools.product((0, 1), repeat=length):
                    rhs = [(c - p) % q for c, p in zip(ciphertext, plain)]
                    state = tuple(sum(row[i] * rhs[i] for i in range(length)) % q for row in inverse_q)
                    ks = [sum(alpha[p][j] * state[j] for j in range(length)) % q for p in positions]
                    if all((c - k) % q in (0, 1) for c, k in zip(ciphertext, ks)):
                        via_constraints.add(state)
                brute: set[tuple[int, ...]] = set()
                for state in itertools.product(range(q), repeat=length):
                    key = list(state)
                    while len(key) <= positions[-1]:
                        key.append(sum(taps[k] * key[-length + k] for k in range(length)) % q)
                    if all((c - key[p]) % q in (0, 1) for c, p in zip(ciphertext, positions)):
                        brute.add(state)
                assert via_constraints == brute, (q, length, taps)
                cases += 1
            assert nonsingular > 0
    assert cases > 0

    # A planted GF(29) stream with first-L positions away from the state seed.
    # This guards the nontrivial basis inversion that consecutive-position plants do not.
    positions = [1, 3, 5, 7, 9, 12, 15]
    for length in range(1, 6):
        chosen = None
        for taps in itertools.product(range(4), repeat=length):
            alpha = basis(taps, positions[-1])
            matrix = [alpha[p] for p in positions[:length]]
            inv = inverse(matrix)
            if inv is not None:
                chosen = (taps, alpha, inv)
                break
        assert chosen is not None
        taps, alpha, inv = chosen
        state = tuple((3 + 2 * i) % 29 for i in range(length))
        key = [sum(alpha[p][j] * state[j] for j in range(length)) % 29 for p in positions]
        target = [10 if i % 2 == 0 else 24 for i in range(len(positions))]
        for mode in ("sub", "add", "beaufort"):
            cipher = [(p + k) % 29 if mode == "sub" else (p - k) % 29 if mode == "add" else (k - p) % 29
                      for p, k in zip(target, key)]
            rhs = [(c - p) % 29 if mode == "sub" else (p - c) % 29 if mode == "add" else (c + p) % 29
                   for c, p in zip(cipher[:length], target[:length])]
            solved = tuple(sum(row[i] * rhs[i] for i in range(length)) % 29 for row in inv)
            assert solved == state
            assert all((c - k) % 29 == p if mode == "sub" else (c + k) % 29 == p if mode == "add" else (k - c) % 29 == p
                       for c, k, p in zip(cipher, key, target))


def main() -> None:
    independent_small_field_controls()
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    pages = {p["id"]: p for p in json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))["pages"]}
    assert len(pages) == 3 and len(result["rows"]) == 45
    for page in pages.values():
        independent_page(page)
    for field, name in (("plan_sha256", "plan.json"), ("source_cpp_sha256", "scan.cpp"),
                        ("inputs_sha256", "inputs.json"), ("full_scan_tsv_sha256", "full-summary.tsv"),
                        ("control_input_sha256", "control-input.txt"),
                        ("control_candidate_sha256", "control-candidates.tsv")):
        assert result[field] == hashlib.sha256((HERE / name).read_bytes()).hexdigest()
    full = tabrows("full-summary.tsv")
    assert len(full) == 45
    for r in result["rows"]:
        key = (r["page"], r["length"], r["mode"])
        tab = full[key]
        assert (r["polynomials"], r["first_basis_invertible"], r["best_singletons_matched"], r["full_singleton_matches"]) == tuple(int(tab[k]) for k in ("polynomials", "invertible", "best", "full"))
        assert r["polynomials"] == 29 ** r["length"]
        for ex in r["examples"]:
            alpha = basis(tuple(ex["coefficients"]), pages[r["page"]]["singleton_positions"][r["length"] - 1])
            assert inverse([alpha[pos] for pos in pages[r["page"]]["singleton_positions"][:r["length"]]]) is not None
            plain = decode(pages[r["page"]]["runes"], ex["coefficients"], ex["initial_state"], r["mode"])
            assert ex["singleton_values"] == [plain[pos] for pos in pages[r["page"]]["singleton_positions"]]
            assert set(ex["singleton_values"]) <= {10, 24}
            assert ex["full_page_decode_sha256"] == hashlib.sha256(bytes(plain)).hexdigest()
            freq = Counter(plain)
            n = len(plain)
            assert ex["normalized_ioc"] == round(29 * sum(v * (v - 1) for v in freq.values()) / (n * (n - 1)), 6)
    # Exhaust all L1/L2 polynomials independently and compare all three modes.
    for length in (1, 2):
        for page in pages.values():
            o = oracle(page, length, 29 ** length)
            for mode, got in o.items():
                row = full[(page["id"], length, mode)]
                assert got == tuple(int(row[k]) for k in ("invertible", "best", "full"))
    # For L3–L5, independently re-enumerate the first 100 polynomials.
    spot = tabrows("spot-summary.tsv")
    for length in (3, 4, 5):
        for page in pages.values():
            o = oracle(page, length, 100)
            for mode, got in o.items():
                row = spot[(page["id"], length, mode)]
                assert int(row["polynomials"]) == 100
                assert got == tuple(int(row[k]) for k in ("invertible", "best", "full"))
    expected, text = controls()
    assert (HERE / "control-input.txt").read_text(encoding="utf-8") == text
    rows = list(csv.DictReader((HERE / "control-candidates.tsv").open(encoding="utf-8"), delimiter="\t"))
    found = {(r["page"], int(r["length"]), r["mode"], r["coefficients:state"]) for r in rows}
    for c in expected:
        mode = "sub" if c["mode"] == "add" else c["mode"]
        state = [(-x) % 29 for x in c["state"]] if c["mode"] == "add" else c["state"]
        witness = (c["id"], c["length"], mode, f"{','.join(map(str,c['coeff']))}:{','.join(map(str,state))}")
        assert witness in found
    print("PASS: toy-field tap/state oracles, nonconsecutive plants, 45 results rows, decoded examples, L1/L2 grids, L3–L5 first 100, 15 scanner plants")


if __name__ == "__main__":
    main()
