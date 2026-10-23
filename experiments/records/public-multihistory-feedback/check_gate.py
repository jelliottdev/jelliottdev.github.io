"""Independent arithmetic and search-domain check of the source's planted cipher."""
import ast
import hashlib
import json
from pathlib import Path

import check

HERE = Path(__file__).resolve().parent
N = 29
TRANS = check.TRANS
ALIASES = {"V": 1, "K": 5, "Z": 15, "Q": 5}
ORDER = sorted(enumerate(TRANS), key=lambda entry: -len(entry[1]))


def first_primes(count):
    found = []
    candidate = 2
    while len(found) < count:
        if all(candidate % divisor for divisor in range(2, int(candidate ** 0.5) + 1)):
            found.append(candidate)
        candidate += 1
    return found


PRIMES = first_primes(400)


def plain_source():
    tree = ast.parse((HERE / "source/analysis/round12/C1/control.py").read_text(encoding="utf-8"))
    return next(ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PLAIN" for t in node.targets))


def to_indices(text):
    text = text.upper()
    out, pos = [], 0
    while pos < len(text):
        match = next(((number, word) for number, word in ORDER if text.startswith(word, pos)), None)
        if match:
            out.append(match[0])
            pos += len(match[1])
        else:
            if text[pos] in ALIASES:
                out.append(ALIASES[text[pos]])
            pos += 1
    return out


def key_value(name, history):
    if name == "sum":
        return sum(history) % N
    if name == "gemsum":
        return sum(PRIMES[i] for i in history) % N
    if name == "xor":
        value = 0
        for item in history:
            value ^= item
        return value % N
    if name == "prime_of_sum":
        return PRIMES[sum(history)] % N
    if name == "prime_of_gemsum":
        return PRIMES[sum(PRIMES[i] for i in history)] % N
    if name == "lastdiff":
        return (history[-1] - history[-2]) % N
    if name == "alt_sum":
        return sum(value if i % 2 == 0 else -value for i, value in enumerate(history)) % N
    raise AssertionError(name)


def history_at(mode, cipher, plain, i):
    if mode == "ct":
        return cipher[i-3:i]
    if mode == "pt":
        return plain[i-3:i]
    return [(cipher[j] + plain[j]) % N for j in range(i-3, i)]


def encipher(plain, mode, name):
    cipher = []
    for i, value in enumerate(plain):
        key = [7, 11, 2][i] if i < 3 else key_value(name, history_at(mode, cipher, plain, i))
        cipher.append((value + key) % N)
    return cipher


def decipher(cipher, mode, name, seed):
    plain = []
    for i, value in enumerate(cipher):
        key = seed[i] if i < 3 else key_value(name, history_at(mode, cipher, plain, i))
        plain.append((value - key) % N)
    return plain


def score(indices):
    return check.quadgram_score("".join(TRANS[i] for i in indices))


def main():
    report = json.loads((HERE / "gate-results.json").read_text(encoding="utf-8"))
    assert report["gate_plan_sha256"] == hashlib.sha256((HERE / "gate-plan.json").read_bytes()).hexdigest()
    truth = to_indices(plain_source())
    assert len(truth) == 212
    assert PRIMES[:N] == [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,101,103,107,109]
    for row in report["rows"]:
        mode, name = row["mode"], row["function"]
        cipher = encipher(truth, mode, name)
        assert decipher(cipher, mode, name, [7,11,2]) == truth
        cases = []
        for case in row["all_seed_cases"]:
            seed = [0,0,0] if mode == "ct" else [int(case["seed"][2:])] * 3
            decoded = decipher(cipher, mode, name, seed)
            got_score = round(score(decoded[3:]), 6)
            recovery = round(sum(a == b for a,b in zip(decoded[3:],truth[3:])) / 209, 6)
            assert (case["score"],case["recovery"]) == (got_score,recovery), (mode,name,case["seed"])
            cases.append(case)
        best = max(cases, key=lambda item: item["score"])
        assert (row["best_searched_seed"],row["best_searched_score"],row["best_searched_recovery"]) == (best["seed"],best["score"],best["recovery"])
        assert row["any_tried_seed_recovery_ge_90pct"] == any(x["recovery"] >= .9 for x in cases)
        assert row["search_gate_pass"] == (best["recovery"] >= .9 and best["score"] >= -5.5)
    for mode, expected in {"ct":7,"pt":0,"mix":0}.items():
        assert report["summary"][mode]["search_gate_pass"] == expected
    print("PASS independent 21-plant, all-primer search-domain gate")


if __name__ == "__main__":
    main()
