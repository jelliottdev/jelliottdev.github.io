"""Independent stdlib arithmetic, input, score and selected full-grid null check."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def output(cipher: list[int], arm: str, seed: int, sign: int, gematria: list[int]) -> list[int]:
    plain = []
    running = seed
    for pos, current in enumerate(cipher):
        if arm == "previous_plaintext_prime":
            key = seed if pos == 0 else gematria[plain[pos - 1]]
        else:
            key = running
        value = (current - sign * key) % 29
        plain.append(value)
        if arm == "cumulative_plaintext_prime":
            running = (running + gematria[value]) % 29
    return plain


def score(indices: list[int], labels: list[str], log_probability: dict[str, float], floor: float) -> tuple[float, str]:
    latin = "".join(labels[index] for index in indices)
    total = 0.0
    for i in range(len(latin) - 3):
        total += log_probability.get(latin[i:i + 4], floor)
    return total / (len(latin) - 3), latin


def main() -> None:
    plan_raw = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_raw)
    saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert saved["plan_sha256"] == digest(plan_raw)
    for item in plan["inputs"]:
        assert digest((ROOT / item["path"]).read_bytes()) == item["sha256"]
    assert digest((HERE / "cases.csv").read_bytes()) == saved["cases_sha256"]
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    rune_to_number = {row["rune"]: index for index, row in enumerate(alphabet)}
    primes = [row["prime"] % 29 for row in alphabet]
    labels = [row["latin"] for row in alphabet]
    counts = {}
    for line in (ROOT / plan["score_model"]).read_text(encoding="ascii").splitlines():
        gram, value = line.split()
        counts[gram] = int(value)
    denominator = sum(counts.values())
    log_probability = {gram: math.log10(value / denominator) for gram, value in counts.items()}
    floor = math.log10(.01 / denominator)
    pages = {}
    for page in plan["targets"]:
        from_text = (ROOT / f"text/{page}.txt").read_text(encoding="utf-8")
        source_page = json.loads((ROOT / f"data/pages/{page}.json").read_text(encoding="utf-8"))
        from_page = source_page["raw"]
        one = [rune_to_number[r] for r in from_text if r in rune_to_number]
        two = [rune_to_number[r] for r in from_page if r in rune_to_number]
        assert one == two, f"Independent site page disagrees with pinned source: {page}"
        pages[page] = one
    with (HERE / "cases.csv").open(encoding="utf-8", newline="") as handle:
        cases = list(csv.DictReader(handle))
    assert len(cases) == len(pages) * 2 * 29 * 2 == saved["candidate_count"]
    unique = set()
    best = (-math.inf, None)
    page_best = {page: (-math.inf, None) for page in pages}
    for case in cases:
        key = (case["page"], case["arm"], int(case["seed"]), int(case["sign"]))
        assert key not in unique
        unique.add(key)
        plain = output(pages[key[0]], key[1], key[2], key[3], primes)
        value, latin = score(plain, labels, log_probability, floor)
        assert math.isclose(value, float(case["score"]), rel_tol=0, abs_tol=1e-10), key
        assert digest(bytes(plain)) == case["plaintext_sha256"]
        assert latin[:80] == case["latin_preview"]
        if value > best[0]:
            best = (value, key)
        if value > page_best[key[0]][0]:
            page_best[key[0]] = (value, key)
    observed = saved["observed_global_best"]
    assert best[1] == (observed["page"], observed["arm"], observed["seed"], observed["sign"])
    assert math.isclose(best[0], observed["score"], rel_tol=0, abs_tol=1e-10)
    for winner in saved["observed_page_best"]:
        actual = page_best[winner["page"]]
        assert actual[1] == (winner["page"], winner["arm"], winner["seed"], winner["sign"])
        assert math.isclose(actual[0], winner["score"], rel_tol=0, abs_tol=1e-10)
    with (ROOT / "exports/readings/warning.csv").open(encoding="utf-8", newline="") as handle:
        warning = [int(row["output_index"]) for row in csv.DictReader(handle)]
    assert saved["model_control"]["roundtrips"] == 116
    for arm in plan["arms"]:
        for sign in plan["signs"]:
            for seed in plan["seeds"]:
                stream = []
                state = seed
                for i, plain in enumerate(warning):
                    key = (seed if i == 0 else primes[warning[i - 1]]) if arm == "previous_plaintext_prime" else state
                    stream.append((plain + sign * key) % 29)
                    if arm == "cumulative_plaintext_prime":
                        state = (state + primes[plain]) % 29
                assert output(stream, arm, seed, sign, primes) == warning
    nulls = saved["null_global_maxima"]
    assert len(nulls) == saved["null_trials"] == 199
    assert [row["shuffle_seed"] for row in nulls] == list(range(33017200, 33017399))
    for index, recorded in enumerate(nulls):
        rng = random.Random(recorded["shuffle_seed"])
        shuffled = {page: values.copy() for page, values in pages.items()}
        for page in plan["targets"]:
            rng.shuffle(shuffled[page])
        assert digest(b"".join(bytes(shuffled[page]) + b"\n" for page in plan["targets"])) == recorded["shuffled_streams_sha256"]
        if index not in (0, 99, 198):
            continue
        best_null = (-math.inf, None)
        for page in plan["targets"]:
            for arm in plan["arms"]:
                for seed in plan["seeds"]:
                    for sign in plan["signs"]:
                        plain = output(shuffled[page], arm, seed, sign, primes)
                        value, _ = score(plain, labels, log_probability, floor)
                        if value > best_null[0]:
                            best_null = (value, (page, arm, seed, sign))
        assert best_null[1] == (recorded["page"], recorded["arm"], recorded["seed"], recorded["sign"])
        assert math.isclose(best_null[0], recorded["score"], rel_tol=0, abs_tol=1e-10)
    assert saved["null_exceedances"] == sum(row["score"] >= observed["score"] for row in nulls)
    print("PASS: independent page source, all 6,380 outputs/scores, 116 roundtrips, 199 null input digests and 3 full null grids")


if __name__ == "__main__":
    main()
