"""Measure empirical single-rune entropy of an archived page; no decryption or network."""
import argparse
import json
import math
from pathlib import Path
import sys
from rune_ioc import report as frequency_report


def entropy(counts):
    """Bits per symbol of the empirical distribution; None for no observations."""
    if any(type(c) is not int or c < 0 for c in counts):
        raise ValueError("Counts must be nonnegative integers")
    total = sum(counts)
    if total == 0:
        return None
    return math.fsum(-(c / total) * math.log2(c / total) for c in counts if c)


def report(page):
    source = frequency_report()
    row = next((r for r in source["records"] if r["page"] == page), None)
    if row is None:
        raise ValueError("Unknown page ID")
    return {
        "schema": "liberpedia-rune-entropy-v1", "page": page,
        "scope": source["scope"], "input_path": row["input_path"],
        "input_sha256": row["input_sha256"],
        "alphabet_sha256": source["alphabet_sha256"],
        "alphabet": source["alphabet"], "counts": row["counts"], "n": row["n"],
        "observed_symbols": sum(c > 0 for c in row["counts"]),
        "empirical_entropy_bits": entropy(row["counts"]),
        "uniform_29_entropy_bits": math.log2(29),
        "finite_sample_maximum_entropy_bits": maximum_entropy(row["n"], 29),
        "interpretation": "Single-symbol frequency summary, not entropy rate, a randomness test, or evidence of a cipher family. Empty input has null entropy.",
    }


def maximum_entropy(n, alphabet_size):
    """Maximum empirical entropy: integer counts differ by at most one."""
    if type(n) is not int or n < 0:
        raise ValueError("Sample size must be a nonnegative integer")
    if type(alphabet_size) is not int or alphabet_size < 1:
        raise ValueError("Alphabet size must be a positive integer")
    quotient, remainder = divmod(n, alphabet_size)
    return entropy([quotient + 1] * remainder
                   + [quotient] * (alphabet_size - remainder))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("page", type=str.lower)
    parser.add_argument("--output", type=Path, help="Save UTF-8 JSON; refuse existing files")
    args = parser.parse_args()
    try:
        text = json.dumps(report(args.page), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8", newline="") as handle:
                handle.write(text)
            print("Saved report:", args.output)
        else:
            print(text, end="")
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="")
    main()
