"""Locate overlapping repeated n-grams in one archived rune stream.

Python 3; standard library only. No network, decoding, or significance test.
Example: python scripts/rune_ngrams.py lp2-31 --length 3
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def indexed_runes(text, lookup):
    """Keep original Unicode character positions while filtering the rune stream."""
    symbols, positions = [], []
    line, column = 1, 1
    for offset, character in enumerate(text):
        if character in lookup:
            symbols.append(lookup[character])
            positions.append({"offset": offset, "line": line, "column": column})
        if character == "\n":
            line, column = line + 1, 1
        else:
            column += 1
    return symbols, positions


def occurrence(text, positions, start, length):
    first = positions[start]
    end = positions[start + length - 1]["offset"] + 1
    return {
        "start_rune": start,
        "source_start": first["offset"],
        "source_end": end,
        "source_line": first["line"],
        "source_column": first["column"],
        "source_text": text[first["offset"]:end],
    }


def repeated_windows(symbols, length):
    if isinstance(length, bool) or not isinstance(length, int) or not 1 <= length <= 12:
        raise ValueError("Length must be an integer from 1 through 12")
    locations = defaultdict(list)
    for start in range(max(0, len(symbols) - length + 1)):
        locations[tuple(symbols[start:start + length])].append(start)
    return sorted(((pattern, starts) for pattern, starts in locations.items()
                   if len(starts) >= 2), key=lambda item: (-len(item[1]), item[0]))


def report(page_id, length):
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    page = next((page for page in index["pages"] if page["id"] == page_id), None)
    if page is None:
        raise ValueError("Unknown page ID; include the release, for example lp2-31")
    source = ROOT / "text" / (page_id + ".txt")
    if not source.is_file():
        raise ValueError("This page has no archived rune transcription")
    raw = source.read_bytes()
    text = raw.decode("utf-8")
    alphabet = index["alphabet"]
    runes = [entry["rune"] for entry in alphabet]
    if len(runes) != 29 or len(set(runes)) != 29:
        raise ValueError("Expected 29 distinct runes")
    unknown = {c for c in text if "\u16a0" <= c <= "\u16ff"} - set(runes)
    if unknown:
        raise ValueError("Unknown runes in transcription: " + ascii(unknown))
    lookup = {rune: i for i, rune in enumerate(runes)}
    symbols, positions = indexed_runes(text, lookup)
    if len(symbols) != page["rune_count"]:
        raise ValueError("Rune count disagrees with the page index")
    patterns = repeated_windows(symbols, length)
    return {
        "schema": "liberpedia-rune-ngrams-v1",
        "page": page_id,
        "source": source.relative_to(ROOT).as_posix(),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "alphabet_sha256": hashlib.sha256("".join(runes).encode("utf-8")).hexdigest(),
        "scope": "Archived runes in source order, including headings; all non-runes removed. "
                 "Windows may cross word, line, and paragraph boundaries, but not pages.",
        "positions": "Zero-based rune ordinals in the filtered stream; not character offsets.",
        "source_positions": "Source start/end are zero-based Unicode character offsets with "
                            "an exclusive end. Source line/column are one-based; LF starts a new "
                            "line and each Unicode character counts as one column. These are "
                            "archive text positions, not image coordinates or reader text-row IDs.",
        "counting": "All overlapping windows; repeated means at least two occurrences. "
                    "Sorted by count descending, then alphabet-index tuple.",
        "rune_count": len(symbols),
        "length": length,
        "window_count": max(0, len(symbols) - length + 1),
        "repeated_types": len(patterns),
        "patterns": [
            {"indices": list(pattern),
             "labels": [alphabet[i]["latin"] for i in pattern],
             "runes": "".join(runes[i] for i in pattern),
             "count": len(starts), "starts": starts,
             "occurrences": [occurrence(text, positions, start, length) for start in starts]}
            for pattern, starts in patterns
        ],
        "interpretation": "Descriptive counts, not a chance probability, key length, or decryption.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("page", type=str.lower)
    parser.add_argument("--length", type=int, default=3, help="Runes per window, 1–12; default 3")
    parser.add_argument("--output", type=Path, help="Save UTF-8 JSON without overwriting")
    args = parser.parse_args()
    try:
        text = json.dumps(report(args.page, args.length), ensure_ascii=True, indent=2) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8", newline="") as destination:
                destination.write(text)
            print("Saved report:", args.output)
        else:
            print(text, end="")
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
