"""Independent arithmetic for Leo's published cipher-model fingerprint table."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re


HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
LOOKUP = {ch: i for i, ch in enumerate(RUNES)}
ROW = re.compile(r"^(.+?)\s+(0\.\d{4})\s+(\d\.\d{3})\s+(\d+\.\d)\s+(0\.\d{4})(?:\s+<== TARGET.*)?$")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned(root: Path) -> tuple[dict, list[int]]:
    expected = {
        root / "fingerprint.py": PLAN["source_script_sha256"],
        root / "lp.py": PLAN["source_lp_sha256"],
        root / "dataset.json": PLAN["source_dataset_sha256"],
        root / "results/fingerprint.txt": PLAN["source_receipt_sha256"],
        root / "sources/relikd_LiberPrayground/data/baseline-rune-stream.txt": PLAN["baseline_rune_stream_sha256"],
        root / "sources/relikd_LiberPrayground/data/baseline-rune-words.txt": PLAN["baseline_rune_words_sha256"],
    }
    for path, digest in expected.items():
        if sha(path) != digest:
            raise ValueError(f"input changed: {path}")
    data = json.loads((root / "dataset.json").read_text(encoding="utf-8"))
    baseline = (root / "sources/relikd_LiberPrayground/data/baseline-rune-stream.txt").read_text(encoding="utf-8")
    return data, [LOOKUP[ch] for ch in baseline if ch in LOOKUP][:60000]


def primes(n: int) -> list[int]:
    result = []
    value = 2
    while len(result) < n:
        for d in range(2, int(value ** .5) + 1):
            if value % d == 0:
                break
        else:
            result.append(value)
        value += 1
    return result


def stats(seq: list[int]) -> dict:
    n = len(seq)
    counts = Counter(seq)
    equal1 = sum(a == b for a, b in zip(seq, seq[1:]))
    equal2 = sum(seq[i] == seq[i - 2] for i in range(2, n))
    expectation = n / 29
    return {
        "runes": n,
        "equal1": equal1,
        "equal1_rate": equal1 / (n - 1),
        "ioc": 29 * sum(v * (v - 1) for v in counts.values()) / (n * (n - 1)),
        "chi2_uniform": sum((counts.get(i, 0) - expectation) ** 2 / expectation for i in range(29)),
        "equal2": equal2,
        "equal2_rate": equal2 / (n - 2),
    }


def models(plain: list[int], war: list[int]) -> list[tuple[str, list[int]]]:
    n = len(plain)
    rng = random.Random(PLAN["source_random_seed"])
    out = []

    def add(name, seq):
        out.append((name, seq))

    def sumkey(key):
        return [(x + key[i % len(key)]) % 29 for i, x in enumerate(plain)]

    for length in (8, 13, 29):
        add(f"vigenere key len {length} (random key)", sumkey([rng.randrange(29) for _ in range(length)]))
    ps = primes(n)
    for name, key in (
        ("totient stream (p_n - 1)", [x - 1 for x in ps]),
        ("prime stream (p_n)", ps),
        ("prime stream squared", [x * x for x in ps]),
    ):
        add(name, [(x + key[i]) % 29 for i, x in enumerate(plain)])
    a, b = 1, 1
    fib = []
    for _ in plain:
        fib.append(a % 29)
        a, b = b, (a + b) % 29
    add("fibonacci stream", [(x + fib[i]) % 29 for i, x in enumerate(plain)])
    add("trithemius (i)", [(x + i) % 29 for i, x in enumerate(plain)])
    add("i^2 stream", [(x + i * i) % 29 for i, x in enumerate(plain)])

    def cipher_feedback(sign: int, offset: int = 0):
        prev = 0
        result = []
        for x in plain:
            c = (x + sign * prev + offset) % 29
            result.append(c)
            prev = c
        return result

    add("ciphertext autokey c=p+c_prev", cipher_feedback(1))
    add("ciphertext autokey c=p-c_prev", cipher_feedback(-1))
    for lag, name in ((1, "plaintext autokey c=p+p_prev"), (5, "plaintext autokey lag5")):
        add(name, [(x + (plain[i - lag] if i >= lag else 0)) % 29 for i, x in enumerate(plain)])
    add("plain diff c=p-p_prev", [(x - (plain[i - 1] if i else 0)) % 29 for i, x in enumerate(plain)])
    add("running key English (W&P) vig", [(x + war[i]) % 29 for i, x in enumerate(plain)])
    add("running key English (W&P) beaufort", [(war[i] - x) % 29 for i, x in enumerate(plain)])
    rotated = plain[500:] + plain[:500]
    add("running key LP plaintext itself offset 500", [(x + rotated[i]) % 29 for i, x in enumerate(plain)])
    add("affine a=2 b=7 (monoalphabetic)", [(2 * x + 7) % 29 for x in plain])
    add("OTP random", [rng.randrange(29) for _ in plain])
    add("chain c=c_prev+p+1", cipher_feedback(1, 1))
    key8 = [rng.randrange(29) for _ in range(8)]
    keypos = 0
    interrupted = []
    for x in plain:
        if x == 0:
            interrupted.append(0)
        else:
            interrupted.append((x + key8[keypos % 8]) % 29)
            keypos += 1
    add("vigenere len 8 with F-interrupts", interrupted)
    keypos = 0
    interrupted = []
    for x in plain:
        if x == 0:
            interrupted.append(0)
        else:
            interrupted.append((x + ps[keypos] - 1) % 29)
            keypos += 1
    add("totient with F-interrupts", interrupted)
    # The source's final row passes F unchanged but uses absolute i for the key;
    # it does not pause the War & Peace key clock.
    add("running key English with F-interrupts", [0 if x == 0 else (x + war[i]) % 29 for i, x in enumerate(plain)])
    return out


def table(text: str) -> dict[str, tuple[str, str, str, str]]:
    rows = {}
    for line in text.splitlines():
        match = ROW.match(line)
        if match:
            rows[match.group(1).strip()] = match.groups()[1:]
    return rows


def formatted(s: dict) -> tuple[str, str, str, str]:
    return (f"{s['equal1_rate']:.4f}", f"{s['ioc']:.3f}", f"{s['chi2_uniform']:.1f}", f"{s['equal2_rate']:.4f}")


def build(root: Path) -> dict:
    data, war = pinned(root)
    plain = [v for section in data["sections"] if section["solved"] for v in section["plain_indices"]]
    cipher = [v for section in data["sections"] if not section["solved"] for v in section["indices"]]
    assert len(plain) == 2979 and len(cipher) == 12956 and len(war) == 60000
    receipt = table((root / "results/fingerprint.txt").read_text(encoding="utf-8"))
    assert len(receipt) == PLAN["model_count"] + 1
    observed = stats(cipher)
    target_receipt = list(formatted(observed))
    target_receipt[2] = f"{observed['chi2_uniform'] * len(plain) / len(cipher):.1f}"
    assert tuple(target_receipt) == receipt["UNSOLVED CIPHERTEXT"]
    rows = []
    for name, seq in models(plain, war):
        measured = stats(seq)
        if formatted(measured) != receipt[name]:
            raise AssertionError(f"source receipt differs for {name}: {formatted(measured)} != {receipt[name]}")
        rows.append({"name": name, **measured, "archived_display": list(receipt[name])})
    assert len(rows) == PLAN["model_count"]
    counts = Counter(plain[1:])
    followup = []
    for b in range(29):
        symbol = (-b) % 29
        equal = counts[symbol]
        followup.append({"offset": b, "repeat_symbol": symbol, "count": equal,
                         "rate": equal / (len(plain) - 1), "distance_from_lp2": abs(equal / (len(plain) - 1) - observed["equal1_rate"])})
    ranked = sorted(followup, key=lambda r: (r["distance_from_lp2"], r["offset"]))
    chain = next(r for r in rows if r["name"] == "chain c=c_prev+p+1")
    assert chain["equal1"] == followup[1]["count"] == 20
    return {
        "schema": "leo-cipher-model-fingerprints-v1", "plan_sha256": sha(HERE / "plan.json"),
        "source_revision": PLAN["revision"], "solved_plaintext_runes": len(plain),
        "unsolved_ciphertext_runes": len(cipher), "observed": observed,
        "models": rows, "offset_followup": followup,
        "source_offset_rank_by_absolute_rate_distance": next(i for i, row in enumerate(ranked, 1) if row["offset"] == 1),
        "source_receipt_all_rows_match": True,
        "source_target_chi2_scaled_for_display": observed["chi2_uniform"] * len(plain) / len(cipher),
        "note": "The source's target chi-square is scaled by sample-length ratio; this display value is not a chi-square test statistic with its original null calibration."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build(args.source_root)
    output = HERE / "results.json"
    body = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        assert output.read_text(encoding="utf-8") == body
    else:
        output.write_text(body, encoding="utf-8", newline="\n")
    print(f"23 source rows and 29 offset identities checked; source b=1 rank {result['source_offset_rank_by_absolute_rate_distance']}/29")


if __name__ == "__main__":
    main()
