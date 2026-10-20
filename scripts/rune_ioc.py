"""Reproduce whole-page IoC from archived rune transcriptions (no network).

Print all records as JSON, or select a page: python scripts/rune_ioc.py lp2-31
Compare all current inputs with the published baseline: --check
Write a new report without overwriting an existing file: --output PATH
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "data/evidence/rune-ioc.json"


def coincidence(symbols):
    """Probability that two distinct, uniformly selected positions match."""
    counts = Counter(symbols)
    n = sum(counts.values())
    numerator = sum(c * (c - 1) for c in counts.values())
    denominator = n * (n - 1)
    return {
        "n": n, "numerator": numerator, "denominator": denominator,
        "ioc": numerator / denominator if n >= 2 else None,
    }


def report():
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    alphabet = [a["rune"] for a in index["alphabet"]]
    if len(alphabet) != 29 or len(set(alphabet)) != 29:
        raise ValueError("Expected 29 distinct runes")
    alphabet_bytes = "".join(alphabet).encode("utf-8")
    records = []
    for page in index["pages"]:
        pid = page["id"]
        path = ROOT / "text" / (pid + ".txt")
        if path.exists():
            payload = path.read_bytes()
            text = payload.decode("utf-8")
            # Unknown runic code points must not disappear silently.
            unknown = {c for c in text if "\u16a0" <= c <= "\u16ff"} - set(alphabet)
            if unknown:
                raise ValueError(f"{pid}: unknown runic symbols {ascii(unknown)}")
            symbols = [c for c in text if c in alphabet]
            source = path.relative_to(ROOT).as_posix()
            digest = hashlib.sha256(payload).hexdigest()
        else:
            if page["rune_count"] != 0:
                raise ValueError(f"Missing transcription: {pid}")
            symbols, source, digest = [], None, None
        result = coincidence(symbols)
        if result["n"] != page["rune_count"]:
            raise ValueError(f"Rune count disagrees with index: {pid}")
        counts = Counter(symbols)
        records.append({
            "page": pid, "input_path": source, "input_sha256": digest,
            **result, "scaled_ioc_29": 29 * result["ioc"] if result["ioc"] is not None else None,
            "counts": [counts[r] for r in alphabet],
        })
    return {
        "schema": "liberpedia-rune-ioc-v1",
        "scope": "Whole archived rune stream per page; includes rune headings; no corrections or decryption. Excludes punctuation, whitespace, Latin text and printed decimal numbers.",
        "alphabet": alphabet,
        "alphabet_sha256": hashlib.sha256(alphabet_bytes).hexdigest(),
        "alphabet_hash_encoding": "UTF-8 concatenation in listed order, no separator",
        "uniform_independent_expectation": 1 / 29,
        "records": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("page", nargs="?", help="Exact page ID, e.g. lp2-31")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.page and args.check:
        parser.error("--check compares the full baseline; omit the page")
    result = report()
    if args.check:
        saved = json.loads(BASELINE.read_text(encoding="utf-8"))
        if result != saved:
            raise SystemExit("Baseline differs. Inspect input hashes and counting rules before updating.")
        print(f"Verified {len(result['records'])} page records against the published baseline.")
        return
    if args.page:
        result["records"] = [r for r in result["records"] if r["page"] == args.page]
        if not result["records"]:
            parser.error("Unknown page ID")
    output = json.dumps(result, ensure_ascii=True, indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
