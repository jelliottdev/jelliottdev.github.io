"""Independent standard-library recalculation of all source J/K/L manuscript rows."""
from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
N = 29


def near(a: float, b: float, name: str, tol: float = 1e-9) -> None:
    if not math.isclose(a, b, rel_tol=tol, abs_tol=tol):
        raise AssertionError(f"{name}: {a} != {b}")


def tail_even(chi: float) -> float:
    # Survival function for 28 df = Poisson lower tail at 13 with mean χ²/2.
    mean = chi / 2
    term = math.exp(-mean)
    total = term
    for i in range(1, 14):
        term *= mean / i
        total += term
    return total


def tail_wh(chi: float, df: int) -> float:
    z = ((chi / df) ** (1 / 3) - 1 + 2 / (9 * df)) / math.sqrt(2 / (9 * df))
    return math.erfc(z / math.sqrt(2)) / 2


def distribution(q: list[float], key: list[float], mode: str, offset: int) -> list[float]:
    out = [0.] * N
    for i, p in enumerate(q):
        for j, k in enumerate(key):
            if mode == "sub":
                idx = i + j + offset
            elif mode == "add":
                idx = i - j - offset
            elif mode == "beaufort":
                idx = j + offset - i
            else:
                raise AssertionError(mode)
            out[idx % N] += p * k
    return out


def llr(observed: list[int], predicted: list[float]) -> float:
    return sum(v * math.log(N * p) for v, p in zip(observed, predicted))


def mod_weights(weights: list[int]) -> list[float]:
    out = [0.] * N
    for j, v in enumerate(weights):
        out[j % N] += v / sum(weights)
    return out


def main() -> None:
    inp = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))
    res = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert len(RUNES) == N and len(set(RUNES)) == N
    indices = {r: i for i, r in enumerate(RUNES)}
    pages = []
    for n in range(56):
        page = json.loads((ROOT / "data" / "pages" / f"lp2-{n:02}.json").read_text(encoding="utf-8"))
        pages.extend(indices[ch] for ch in page["raw"] if ch in indices)
    assert pages == inp["runes"], "site/source GP29 stream differs"
    assert len(pages) == res["rune_count"] == 12956
    lengths = inp["segments"]
    assert lengths == [729, 1145, 1729, 9, 1894, 1021, 1524, 1589, 3316]
    assert sum(lengths) == len(pages)
    streams, cursor = [], 0
    for size in lengths:
        streams.append(pages[cursor:cursor + size]); cursor += size
    q = inp["solved_model_q"]
    assert len(q) == N
    near(sum(q), 1, "q normalization")
    observed = [pages.count(i) for i in range(N)]
    mappings = {"letters": list(range(N)),
                "prime values": [p % N for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109]],
                "phi(prime values)": [(p - 1) % N for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109]]}
    assert len(res["c10"]) == 27
    for row in res["c10"]:
        weights = [0.] * N
        for letter, mapped in enumerate(mappings[row["mapping"]]):
            weights[mapped] += row["mixture"] * q[letter] + (1-row["mixture"]) / N
        scores = [llr(observed, distribution(q, weights, row["mode"], off)) for off in range(N)]
        near(max(scores), row["best_llr"], "C10")
        assert scores.index(max(scores)) == row["best_offset"]
    assert len(res["c13"]) == 4
    for row in res["c13"]:
        key = mod_weights(row["weights"])
        scores = [(llr(observed, distribution(q, key, mode, off)), mode, off)
                  for mode in ("sub", "add", "beaufort") for off in range(N)]
        score, mode, off = max(scores)
        near(score, row["best_llr"], "C13")
        assert (mode, off) == (row["best_mode"], row["best_offset"])
    freq = [v / len(pages) for v in observed]
    assert len(res["c11"]) == 1998
    expected_c11 = {}
    for sign in (1, -1):
        expected_c11[sign] = [sum(freq[a] * freq[(x - sign*a) % N] for a in range(N)) for x in range(N)]
    for row in res["c11"]:
        lag, sign = row["lag"], row["sign"]
        counts = [0] * N
        for stream in streams:
            for a, b in zip(stream, stream[lag:]):
                counts[(b + sign * a) % N] += 1
        total = sum(counts)
        chi = sum((o - total*e)**2 / (total*e) for o, e in zip(counts, expected_c11[sign]))
        assert total == row["pairs"]
        near(chi, row["chi2"], "C11")
        near(tail_even(chi), row["p"], "C11 p", 1e-7)
    assert len(res["c12"]) == 1000
    for row in res["c12"]:
        lag = row["lag"]
        table = [[0] * N for _ in range(N)]
        for stream in streams:
            for a, b in zip(stream, stream[lag:]):
                table[a][b] += 1
        chi = 0.
        for a in range(N):
            subtotal = sum(table[a]) - table[a][a]
            for b in range(N):
                if b != a:
                    expected = subtotal * freq[b] / (1-freq[a])
                    chi += (table[a][b] - expected)**2 / expected
        assert row["df"] == N*(N-2)
        near(chi, row["chi2"], "C12")
        near(tail_wh(chi, row["df"]), row["p"], "C12 p", 1e-7)
    assert min(row["p"] for row in res["c11"]) > .01/1998
    assert min(row["p"] for row in res["c12"]) > .01/1000
    print("independent C10/C11/C12/C13 rows and source/site stream: OK")


if __name__ == "__main__":
    main()
