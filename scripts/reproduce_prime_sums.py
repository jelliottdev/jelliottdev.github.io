"""Reproduce published Gematria Primus sums without changing repository files.

Python 3, standard library only. Run:
    python scripts/reproduce_prime_sums.py
    python scripts/reproduce_prime_sums.py --json

Re-decodes the known controls, checks their literal outputs, then sums rune
prime values. This is a verification of named examples, not a cipher search
or a statistical test of authorial intent.
"""
import argparse
import hashlib
import json
from math import isqrt
import re
import sys

from reproduce_reading import ROOT, RUNES, check, reproduce


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def is_prime(number):
    return number >= 2 and all(number % d for d in range(2, isqrt(number) + 1))


def describe_sum(number):
    reverse = int(str(number)[::-1])
    return {"sum": number, "prime": is_prime(number), "reverse": reverse,
            "reverse_prime": is_prime(reverse),
            "emirp": number != reverse and is_prime(number) and is_prime(reverse)}


def verify():
    alphabet = read("data/index.json")["alphabet"]
    by_rune = {entry["rune"]: entry for entry in alphabet}
    if "".join(entry["rune"] for entry in alphabet) != RUNES:
        raise ValueError("Alphabet order differs from the reading implementation")
    evidence = read("data/evidence/spelling-sums.json")
    known_hash = hashlib.sha256((ROOT / "data/evidence/known-readings.json").read_bytes()).hexdigest()
    if known_hash != evidence["source_sha256"]["known_readings"]:
        raise ValueError("Known-reading evidence hash differs from the recorded input")

    def record(text):
        tokens = [by_rune[char] for char in text if char in by_rune]
        return {"runes": "".join(t["rune"] for t in tokens),
                "labels": [t["latin"] for t in tokens],
                "values": [t["prime"] for t in tokens],
                **describe_sum(sum(t["prime"] for t in tokens))}

    decoded = {}
    for control in read("data/evidence/reading-methods.json")["controls"]:
        output, trace = reproduce(control)
        check(output)
        for page_id in control["pages"]:
            # The trace already includes the documented source correction and
            # method-specific interruption rules. Preserve archive separators.
            indices = iter(row[6] for row in trace if row[0] == page_id)
            raw = (ROOT / f"text/{page_id}.txt").read_text(encoding="utf-8")
            runes = "".join(RUNES[next(indices)] if char in by_rune else char for char in raw)
            decoded[page_id] = runes.replace("/\n", "").replace("/", "").replace("\n", "")

    words = []
    for expected in evidence["words"]:
        page_id = expected["page"]
        tokens = re.findall("[" + RUNES + "]+", decoded[page_id])
        actual = record(tokens[expected["word_ordinal"]])
        if any(actual[key] != expected[key] for key in actual):
            raise ValueError(f"Word evidence mismatch: {page_id}, ordinal {expected['word_ordinal']}")
        words.append({"page": page_id, "word_ordinal": expected["word_ordinal"], **actual})

    clauses = [record(part) for part in decoded["lp2-57"].split(".") if record(part)["runes"]]
    if len(clauses) != len(evidence["lp2_57_clauses"]):
        raise ValueError("LP2-57 clause count differs")
    for position, (actual, expected) in enumerate(zip(clauses, evidence["lp2_57_clauses"])):
        if any(actual[key] != expected[key] for key in actual):
            raise ValueError(f"LP2-57 segment {position} differs from published evidence")

    def word(labels, page):
        return next(row for row in words if row["page"] == page and "".join(row["labels"]) == labels)

    # These are declared counterfactual changes, not additional source text.
    values = {row["latin"]: row["prime"] for row in alphabet}
    changes = [
        {"example": "LP2-57 first body sentence: add one I before NG in TUNNELNG",
         "original": clauses[1]["sum"], "delta": values["I"]},
        {"example": "LP1-16 CWESTIAN: replace IA with separate I and O",
         "original": word("CWESTIAN", "lp1-16")["sum"],
         "delta": values["I"] + values["O"] - values["IA"]},
        {"example": "LP1-04 WIDSOM: exchange D and S",
         "original": word("WIDSOM", "lp1-04")["sum"], "delta": 0},
        {"example": "LP1-10 BELIEUE: exchange the middle I and E",
         "original": word("BELIEUE", "lp1-10")["sum"], "delta": 0},
    ]
    for change in changes:
        change["alternative"] = describe_sum(change["original"] + change["delta"])
    return {"scope": "Known decoded runes; rune-only sums; archived LP2-57 period boundaries.",
            "verified_literal_pages": len(decoded), "verified_word_occurrences": len(words),
            "words": words, "lp2_57_segments": clauses,
            "lp2_57_heading_and_body": describe_sum(sum(c["sum"] for c in clauses)),
            "counterfactuals": changes,
            "limit": "Reproduces arithmetic, not authorial intent or a chance probability."}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true", help="Print the complete machine-readable result")
    args = parser.parse_args()
    result = verify()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(f"PASS: {result['verified_literal_pages']} literal pages and {result['verified_word_occurrences']} word occurrences checked.")
    for index, segment in enumerate(result["lp2_57_segments"]):
        name = "Heading" if index == 0 else f"Body sentence {index}"
        print(f"{name}: {segment['sum']}; reverse {segment['reverse']}; emirp={segment['emirp']}")
    total = result["lp2_57_heading_and_body"]
    print(f"Heading + body: {total['sum']}; prime={total['prime']}")
    for change in result["counterfactuals"]:
        alternative = change["alternative"]
        print(f"{change['example']}: {change['original']} {change['delta']:+d} = {alternative['sum']}; prime={alternative['prime']}; emirp={alternative['emirp']}")
    print(result["limit"])


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
