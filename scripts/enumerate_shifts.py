"""Enumerate a teaching example: whole-stream order x fixed shift, no scoring.

Run from the extracted reference bundle or repository:
    python scripts/enumerate_shifts.py lp2-31 --output my-shifts.json
Standard library only. Existing output files are never overwritten.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def candidates(indices):
    """Original then reversed; subtract k modulo 29, for k = 0..28."""
    if not indices or any(type(i) is not int or not 0 <= i < 29 for i in indices):
        raise ValueError("Expected a nonempty sequence of integer rune indices 0..28")
    return [
        {"order": order, "shift": k,
         "indices": [(i - k) % 29 for i in stream]}
        for order, stream in [("original", indices), ("reversed", list(reversed(indices)))]
        for k in range(29)
    ]


def report(page_id):
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    if page_id not in {p["id"] for p in index["pages"]}:
        raise ValueError("Unknown page ID")
    alphabet = [a["rune"] for a in index["alphabet"]]
    if len(alphabet) != 29 or len(set(alphabet)) != 29:
        raise ValueError("Expected 29 distinct alphabet runes")
    source = "text/" + page_id + ".txt"
    payload = (ROOT / source).read_bytes()
    text = payload.decode("utf-8")
    unknown = {c for c in text if "\u16a0" <= c <= "\u16ff"} - set(alphabet)
    if unknown:
        raise ValueError("Unknown runic symbols: " + ascii(unknown))
    lookup = {r: i for i, r in enumerate(alphabet)}
    indices = [lookup[c] for c in text if c in lookup]
    cases = candidates(indices)
    return {
        "schema_version": 1,
        "purpose": "Candidate enumeration only; no scoring, match test, or finding",
        "page": page_id, "source": source,
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "alphabet_runes_in_index_order": alphabet,
        "selection": "All recognized runes, including headings; all other characters excluded",
        "operation": "Reverse the entire selected stream if requested, then (index - shift) % 29",
        "rune_count": len(indices), "case_count": len(cases),
        "distinct_output_count": len({tuple(c["indices"]) for c in cases}),
        "cases": cases,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("page", help="Exact archive page ID, such as lp2-31")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = report(args.page)
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=True, indent=2)
            handle.write("\n")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Cannot enumerate shifts: {error}\n")
    print(f"Saved {result['case_count']} cases; no scoring or match test performed.")


if __name__ == "__main__":
    main()
