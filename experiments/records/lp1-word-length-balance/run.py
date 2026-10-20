"""Reproduce the fixed 464-word column-balance test. Python standard library.

--check compares a full rerun with stored results and word provenance.
Without --check, writes outputs in this experiment's folder.
"""
import argparse
import hashlib
import json
import random
import re
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
WORD = re.compile(f"[{RUNES}]+(?:'[{RUNES}]+)*")


def reconstruct(plan):
    words, sections = [], []
    for section in plan["sections"]:
        chars, pages = [], []
        for page in section["pages"]:
            path = f"text/{page}.txt"
            raw = (ROOT / path).read_bytes()
            if hashlib.sha256(raw).hexdigest() != plan["input_hashes"][path]:
                raise ValueError(f"Input hash changed: {path}")
            for ch in raw.decode("utf-8"):
                if "\u16a0" <= ch <= "\u16ff" and ch not in RUNES:
                    raise ValueError(f"Unknown rune in {path}")
                if ch not in "/\r\n":
                    chars.append(ch)
                    pages.append(page)
        start = len(words)
        for number, match in enumerate(WORD.finditer("".join(chars)), 1):
            words.append({
                "word": len(words) + 1, "section": section["id"],
                "section_word": number, "pages": list(dict.fromkeys(pages[match.start():match.end()])),
                "ciphertext": match.group(),
                "rune_length": sum(ch in RUNES for ch in match.group()),
                "row": len(words) // plan["columns"] + 1,
                "column": len(words) % plan["columns"] + 1,
            })
        sections.append({"section": section["id"], "words": len(words) - start,
                         "runes": sum(w["rune_length"] for w in words[start:])})
    return words, sections


def score(lengths, columns):
    """Integer multiple of variance; no floating-point tail comparisons."""
    total = sum(lengths)
    return sum((columns * sum(lengths[j::columns]) - total) ** 2 for j in range(columns))


def calculate():
    plan = json.loads((HERE / "plan.json").read_text())
    words, sections = reconstruct(plan)
    lengths = [w["rune_length"] for w in words]
    submitted = json.loads((HERE / "submitted-lengths.json").read_text())["lengths"]
    if lengths != submitted:
        raise ValueError("Reconstructed lengths do not match the supplied vector")
    n, k = len(lengths), plan["columns"]
    if n % k:
        raise ValueError("Equal column sizes are required")
    m, total, squares = n // k, sum(lengths), sum(x*x for x in lengths)
    observed = score(lengths, k)
    variance = Fraction(observed, k**3 * m**2)
    # Population variance of fixed lengths times (k-1)/(n-1).
    expected = Fraction((k-1) * (n*squares-total**2), n*n*(n-1))
    rng = random.Random(plan["seed"])
    null = []
    for _ in range(plan["trials"]):
        shuffled = lengths.copy()
        rng.shuffle(shuffled)
        null.append(score(shuffled, k))
    tail = sum(x <= observed for x in null)
    p = Fraction(tail + 1, len(null) + 1)
    results = {
        "sections": sections, "words": n, "runes": total,
        "columns": k, "rows": m,
        "column_sums": [sum(lengths[j::k]) for j in range(k)],
        "observed_integer_score": observed,
        "variance_of_column_means": str(variance),
        "expected_variance": str(expected),
        "R_fraction": str(variance / expected), "R": float(variance / expected),
        "trials": len(null), "seed": plan["seed"],
        "lower_tail_with_ties": tail, "p_fraction": str(p), "p": float(p),
        "null_integer_scores": null,
    }
    return words, results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    words, results = calculate()
    for filename, value in [("words.json", words), ("results.json", results)]:
        path = HERE / filename
        if args.check:
            if json.loads(path.read_text(encoding="utf-8")) != value:
                raise SystemExit(f"FAIL: {filename} differs")
        else:
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in results.items() if k != "null_integer_scores"}, indent=2))
    print("PASS: full rerun agrees" if args.check else "Saved results and word provenance")


if __name__ == "__main__":
    main()
