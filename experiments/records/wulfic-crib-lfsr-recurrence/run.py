"""Crib-derived GF(29) recurrence screen with out-of-crib prediction.

The frozen plan supplies source crib encodings, score weights and target pages.
Only `--bench` and `--controls` are available before plan freeze; `--run` checks
the plan hash receipt before reading the manuscript targets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
N = 29
HOLDOUT = 128


def bm(seq: list[int]) -> tuple[list[int], int]:
    """Berlekamp–Massey over the prime field GF(29)."""
    c, b = [1] + [0] * len(seq), [1] + [0] * len(seq)
    order, shift, prev = 0, 1, 1
    for i, value in enumerate(seq):
        delta = (value + sum(c[j] * seq[i - j] for j in range(1, order + 1))) % N
        if delta == 0:
            shift += 1
            continue
        old = c.copy()
        factor = (delta * pow(prev, -1, N)) % N
        for j in range(shift, len(c)):
            c[j] = (c[j] - factor * b[j - shift]) % N
        if 2 * order <= i:
            order, b, prev, shift = i + 1 - order, old, delta, 1
        else:
            shift += 1
    return c[:order + 1], order


def recurrence_follow(prefix: list[int], poly: list[int], additional: int) -> list[int]:
    out = list(prefix)
    order = len(poly) - 1
    for _ in range(additional):
        out.append((-sum(poly[j] * out[-j] for j in range(1, order + 1))) % N)
    return out


def source_shifted_key(crib_key: list[int], poly: list[int], total: int) -> list[int]:
    """The source's page-zero start, which ignores a crib's nonzero position."""
    order = len(poly) - 1
    return recurrence_follow(crib_key[:order], poly, total - order)


def infer(cipher: list[int], crib: list[int], pos: int, mode: str,
          holdout: int = HOLDOUT) -> tuple[list[int], int] | None:
    m = len(crib)
    if pos + m + holdout > len(cipher):
        return None
    if mode == "sub":
        key = [(cipher[pos + i] - plain) % N for i, plain in enumerate(crib)]
    elif mode == "add":
        key = [(plain - cipher[pos + i]) % N for i, plain in enumerate(crib)]
    else:
        key = [(cipher[pos + i] + plain) % N for i, plain in enumerate(crib)]
    train = key[:-2]
    poly, order = bm(train)
    if order < 2 or order > min(5, len(train) // 2):
        return None
    predicted = recurrence_follow(train, poly, 2 + holdout)
    if predicted[len(train):m] != key[-2:]:
        return None
    return predicted[m:], order


def decrypt(cipher: list[int], key: list[int], mode: str) -> list[int]:
    if mode == "sub":
        return [(c - k) % N for c, k in zip(cipher, key)]
    if mode == "add":
        return [(c + k) % N for c, k in zip(cipher, key)]
    return [(k - c) % N for c, k in zip(cipher, key)]


def score(indices: list[int], pairs: dict[tuple[int, int], int], trips: set[tuple[int, int, int]]) -> int:
    return sum(pairs.get((a, b), 0) for a, b in zip(indices, indices[1:])) + 5 * sum(
        (a, b, c) in trips for a, b, c in zip(indices, indices[1:], indices[2:]))


def cases(cipher: list[int], cribs: dict[str, list[int]], pairs: dict,
          trips: set, limit: int | None = None) -> dict:
    examined = 0
    recurrence_hits = 0
    best = None
    for name, crib in cribs.items():
        for mode in ("sub", "add", "beaufort"):
            for pos in range(max(0, len(cipher) - len(crib) - HOLDOUT + 1)):
                examined += 1
                inferred = infer(cipher, crib, pos, mode)
                if inferred is None:
                    if limit and examined >= limit:
                        return {"windows": examined, "verified_recurrences": recurrence_hits, "best": best}
                    continue
                predicted, order = inferred
                plain = decrypt(cipher[pos + len(crib):pos + len(crib) + HOLDOUT], predicted, mode)
                value = score(plain, pairs, trips)
                recurrence_hits += 1
                cand = {"score": value, "mode": mode, "crib": name, "pos": pos,
                        "order": order, "continuation": plain}
                if best is None or value > best["score"]:
                    best = cand
                if limit and examined >= limit:
                    return {"windows": examined, "verified_recurrences": recurrence_hits, "best": best}
    return {"windows": examined, "verified_recurrences": recurrence_hits, "best": best}


def load_plan() -> dict:
    return json.loads((HERE / "plan.json").read_text(encoding="utf-8"))


def plan_scoring(plan: dict) -> tuple[dict, set]:
    pairs = {tuple(map(int, item["pair"])): item["weight"] for item in plan["score"]["bigrams"]}
    trips = {tuple(map(int, item)) for item in plan["score"]["trigrams"]}
    return pairs, trips


def plant(crib: list[int], mode: str, order: int, pos: int) -> tuple[list[int], list[int]]:
    # The supplied crib is part of the plaintext; the rest is deterministic GP29
    # filler. Recovery is checked exactly, independent of the English score.
    length = pos + len(crib) + HOLDOUT + 5
    rng = random.Random(3301 + 100 * order + pos)
    plain = [rng.randrange(N) for _ in range(length)]
    plain[pos:pos + len(crib)] = crib
    state = [3, 7, 11, 13, 17][:order]
    coeffs = ([2, 3] if order == 2 else [2, 3, 5])
    key = state.copy()
    for _ in range(length - order):
        key.append(sum(a * b for a, b in zip(coeffs, key[-order:])) % N)
    if mode == "sub":
        cipher = [(p + k) % N for p, k in zip(plain, key)]
    elif mode == "add":
        cipher = [(p - k) % N for p, k in zip(plain, key)]
    else:
        cipher = [(k - p) % N for p, k in zip(plain, key)]
    return cipher, plain


def controls(plan: dict) -> dict:
    crib = plan["cribs"]["CIRCUMFERENCE"]
    results = []
    for mode in ("sub", "add", "beaufort"):
        for order in (2, 3):
            for pos in (7, 23):
                cipher, plain = plant(crib, mode, order, pos)
                got = infer(cipher, crib, pos, mode)
                ok = got is not None and decrypt(cipher[pos + len(crib):pos + len(crib) + HOLDOUT],
                                                 got[0], mode) == plain[pos + len(crib):pos + len(crib) + HOLDOUT]
                # Source extracts all crib key symbols and restarts them at page zero.
                if mode == "sub":
                    k = [(cipher[pos + i] - p) % N for i, p in enumerate(crib)]
                elif mode == "add":
                    k = [(p - cipher[pos + i]) % N for i, p in enumerate(crib)]
                else:
                    k = [(cipher[pos + i] + p) % N for i, p in enumerate(crib)]
                poly, source_order = bm(k)
                source_key = source_shifted_key(k, poly, len(cipher))
                wrong_at_crib = decrypt(cipher[pos:pos + len(crib)],
                                        source_key[pos:pos + len(crib)], mode) != crib
                results.append({"mode": mode, "order": order, "pos": pos,
                                "corrected_exact_128": ok, "source_phase_fails_crib": wrong_at_crib,
                                "source_inferred_order": source_order})
    assert all(row["corrected_exact_128"] for row in results), results
    assert all(row["source_phase_fails_crib"] for row in results), results
    cipher, plain = plant(crib, "sub", 3, 23)
    ablation = []
    for parser in ("source", "canonical"):
        # In this plant, old rune U+16C2 is absent; the source parser loses
        # canonical U+16C3 (GP index 11), including positions after the crib.
        origins = [i for i, value in enumerate(cipher) if parser == "canonical" or value != 11]
        parsed = [cipher[i] for i in origins]
        parsed_pos = origins.index(23)
        assert origins[parsed_pos:parsed_pos + len(crib)] == list(range(23, 23 + len(crib)))
        for phase in ("source", "corrected"):
            if phase == "corrected":
                found = infer(parsed, crib, parsed_pos, "sub")
                pred = found[0] if found else []
            else:
                key = [(parsed[parsed_pos + j] - c) % N for j, c in enumerate(crib)]
                poly, _ = bm(key)
                stream = source_shifted_key(key, poly, len(parsed))
                pred = stream[parsed_pos + len(crib):parsed_pos + len(crib) + HOLDOUT]
            start = parsed_pos + len(crib)
            decoded = decrypt(parsed[start:start + HOLDOUT], pred, "sub")
            actual = [plain[i] for i in origins[start:start + HOLDOUT]]
            ablation.append({"parser": parser, "phase": phase,
                             "dropped_runes": len(cipher) - len(parsed),
                             "correct_of_128_retained": sum(a == b for a, b in zip(decoded, actual)),
                             "exact_128": len(decoded) == HOLDOUT and decoded == actual})
    assert [x["exact_128"] for x in ablation] == [False, False, False, True], ablation
    return {"plants": results, "passed": len(results), "ablation": ablation}


def source_cases(cipher: list[int], cribs: dict[str, list[int]], pairs: dict,
                 trips: set) -> dict:
    tested = eligible = 0
    best = None
    for name, crib in cribs.items():
        for mode in ("sub", "add", "beaufort"):
            for pos in range(len(cipher) - len(crib)):
                tested += 1
                if mode == "sub":
                    key = [(c - p) % N for c, p in zip(cipher[pos:pos + len(crib)], crib)]
                elif mode == "add":
                    key = [(p - c) % N for c, p in zip(cipher[pos:pos + len(crib)], crib)]
                else:
                    key = [(c + p) % N for c, p in zip(cipher[pos:pos + len(crib)], crib)]
                poly, order = bm(key)
                if not 2 <= order <= len(crib) // 2:
                    continue
                stream = source_shifted_key(key, poly, len(cipher))
                plain = decrypt(cipher, stream, mode)
                freq = [plain.count(i) for i in range(N)]
                ioc = N * sum(f * (f - 1) for f in freq) / (len(plain) * (len(plain) - 1))
                if ioc <= 1.4:
                    continue
                eligible += 1
                bg = sum(pairs.get((a,b), 0) for a,b in zip(plain, plain[1:]))
                tg = sum((a,b,c) in trips for a,b,c in zip(plain,plain[1:],plain[2:]))
                val = ioc + 0.01 * bg + 0.05 * tg
                candidate = {"score": val, "ioc": ioc, "bigram": bg, "trigram": tg,
                             "crib": name, "mode": mode, "pos": pos, "order": order,
                             "sample_80": plain[:80]}
                if best is None or val > best["score"]:
                    best = candidate
    return {"tested": tested, "source_ioc_gate_passes": eligible, "best": best}


def target_run(plan: dict) -> dict:
    assert plan["null"]["trials"] == 199
    input_bytes = (HERE / "inputs.json").read_bytes()
    assert hashlib.sha256(input_bytes).hexdigest() == plan["inputs_sha256"]
    rows = json.loads(input_bytes)["rows"]
    assert [(x["page_id"], len(x["source_indices"]), len(x["site_indices"])) for x in rows] == [
        (p["page_id"], p["source_rune_count"], p["site_rune_count"]) for p in plan["pages"]]
    pairs, trips = plan_scoring(plan)
    source = {row["page_id"]: source_cases(row["source_indices"], plan["source_cribs"], pairs, trips)
              for row in rows}
    targets = [row for row in rows if row["page_id"].startswith("lp2-")]
    observed = {row["page_id"]: cases(row["site_indices"], plan["cribs"], pairs, trips)
                for row in targets}
    flat = [(pid, result["best"]) for pid, result in observed.items() if result["best"] is not None]
    best_page, best = max(flat, key=lambda x: x[1]["score"]) if flat else (None, None)
    rng = random.Random(plan["null"]["seed"])
    maxima = []
    for trial in range(plan["null"]["trials"]):
        trial_max = None
        for row in targets:
            sample = row["site_indices"].copy()
            rng.shuffle(sample)
            got = cases(sample, plan["cribs"], pairs, trips)["best"]
            if got is not None:
                trial_max = max(trial_max, got["score"]) if trial_max is not None else got["score"]
        maxima.append(trial_max)
        if (trial + 1) % 25 == 0:
            print("null", trial + 1, flush=True)
    comparable = [x for x in maxima if x is not None]
    return {"schema": "wulfic-crib-lfsr-results-v1", "source_original": source,
            "corrected": observed, "observed_global_best_page": best_page,
            "observed_global_best": best, "shared_null_maxima": maxima,
            "null_nonempty_trials": len(comparable),
            "null_at_least_observed": sum(x >= best["score"] for x in comparable) if best else None,
            "screen_hit": best is not None and len(comparable) == len(maxima) and all(best["score"] > x for x in comparable),
            "controls": controls(plan)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bench", action="store_true")
    parser.add_argument("--controls", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    plan = load_plan()
    pairs, trips = plan_scoring(plan)
    if args.controls:
        print(json.dumps(controls(plan), indent=2))
        return
    if args.bench:
        rng = random.Random(20261023)
        synthetic = [rng.randrange(N) for _ in range(273)]
        t = time.perf_counter()
        got = cases(synthetic, plan["cribs"], pairs, trips)
        print(json.dumps({"synthetic_len": len(synthetic), "windows": got["windows"],
                          "seconds": time.perf_counter() - t,
                          "estimated_12page_99null_seconds": (time.perf_counter() - t) * 12 * 100}, indent=2))
        return
    if args.run:
        result = target_run(plan)
        (HERE / "results.json").write_text(json.dumps(result, ensure_ascii=False,
            separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
        print("source pages", len(result["source_original"]), "best", result["observed_global_best_page"],
              result["observed_global_best"]["score"] if result["observed_global_best"] else None,
              "null >=", result["null_at_least_observed"])
        return
    raise SystemExit("Freeze the target/null plan after the synthetic benchmark before running manuscript pages")


if __name__ == "__main__":
    main()
