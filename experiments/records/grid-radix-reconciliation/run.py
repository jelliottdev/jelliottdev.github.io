"""Reconcile the reported 59-symbol grid with three explicit digit alphabets."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import string

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CSV = ROOT / "exports/alphanumeric-grids.csv"
SOURCE = HERE / "source-tokens.txt"
OUTPUT = HERE / "results.json"
ALPHABET_62 = string.digits + string.ascii_uppercase + string.ascii_lowercase
ALPHABET_60 = ALPHABET_62[:60]
ALPHABET_59 = ALPHABET_60.replace("f", "")
assert len(ALPHABET_59) == 59


def digest(data):
    return hashlib.sha256(data).hexdigest()


def summarize(tokens, base, alphabet):
    used = set("".join(tokens))
    missing = sorted(used - set(alphabet))
    invalid = sorted(ch for ch in used & set(alphabet) if alphabet.index(ch) >= base)
    if missing or invalid:
        return {"valid": False, "missing_digits": missing,
                "out_of_range_digits": invalid}
    values = [base * alphabet.index(token[0]) + alphabet.index(token[1]) for token in tokens]
    return {
        "valid": True,
        "missing_digits": [],
        "out_of_range_digits": [],
        "maximum_value": max(values),
        "values_above_byte": sum(value > 255 for value in values),
        "distinct_values": len(set(values)),
        "byte_sha256": digest(bytes(values)) if max(values) <= 255 else None,
        "first_8_values": values[:8],
    }


def inventory(tokens):
    characters = Counter("".join(tokens))
    return {
        "token_count": len(tokens),
        "distinct_tokens": len(set(tokens)),
        "character_count": sum(characters.values()),
        "distinct_characters": len(characters),
        "missing_from_alphanumeric_62": sorted(set(ALPHABET_62) - set(characters)),
        "maximum_conventional_digit": max(ALPHABET_62.index(ch) for ch in characters),
        "lowercase_f_count": characters["f"],
        "leading_digit_counts": dict(sorted(Counter(token[0] for token in tokens).items())),
        "token_4F_count": tokens.count("4F"),
        "token_0x_count": tokens.count("0x"),
    }


def report():
    with CSV.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 256
    assert [int(row["sequence"]) for row in rows] == list(range(1, 257))
    wiki = [row["token"] for row in rows]
    quoted = SOURCE.read_text(encoding="utf-8").split()
    assert len(quoted) == 256
    assert all(len(token) == 2 and token.isascii() and token.isalnum() for token in quoted)
    mismatches = [
        {"sequence": index, "page": row["page"], "row": int(row["row"]),
         "column": int(row["column"]), "wiki": row["token"], "quoted": quoted[index - 1]}
        for index, row in enumerate(rows, 1) if wiki[index - 1] != quoted[index - 1]
    ]
    alphabets = {
        "59_after_deleting_f": (59, ALPHABET_59),
        "59_without_renumbering": (59, ALPHABET_60),
        "60_conventional": (60, ALPHABET_60),
        "62_conventional": (62, ALPHABET_62),
    }
    datasets = {}
    for name, tokens in (("wiki", wiki), ("quoted", quoted)):
        bytes_59 = [59 * ALPHABET_59.index(token[0]) + ALPHABET_59.index(token[1])
                    for token in tokens]
        bytes_60 = [60 * ALPHABET_60.index(token[0]) + ALPHABET_60.index(token[1])
                    for token in tokens]
        datasets[name] = {
            "inventory": inventory(tokens),
            "radices": {label: summarize(tokens, base, alphabet)
                        for label, (base, alphabet) in alphabets.items()},
            "base59_vs_60_changed_values": sum(a != b for a, b in zip(bytes_59, bytes_60)),
        }
    return {
        "schema": "liberpedia-grid-radix-reconciliation-v1",
        "inputs": {"wiki_csv_sha256": digest(CSV.read_bytes()),
                   "quoted_tokens_sha256": digest(SOURCE.read_bytes())},
        "alphabets": {label: alphabet for label, (_, alphabet) in alphabets.items()},
        "datasets": datasets,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "interpretation": [
            "Observed symbol count is not a radix: a 59-symbol sample may be drawn from a larger alphabet.",
            "Base 59 becomes valid only after removing f and renumbering later lowercase digits. Under conventional alphanumeric values, x is digit 59 and is invalid in base 59.",
            "Base 60 is uniquely compatible with both the conventional alphanumeric digit order and one byte per token for these inputs; this does not establish the intended decoding.",
            "The quoted 256-token list and the wiki export are separate transcriptions. Exact output claims must identify which one was used.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    content = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.check:
        assert OUTPUT.read_bytes() == content, "results.json differs from replay"
    else:
        OUTPUT.write_bytes(content)
    print("wiki symbols", result["datasets"]["wiki"]["inventory"]["distinct_characters"],
          "quoted symbols", result["datasets"]["quoted"]["inventory"]["distinct_characters"],
          "token mismatches", result["mismatch_count"])


if __name__ == "__main__":
    main()
