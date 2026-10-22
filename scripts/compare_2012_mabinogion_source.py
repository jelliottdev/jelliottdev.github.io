"""Compare the decoded 2012 Reddit excerpt with a preserved Gutenberg text.

This checks word identity, not byte identity or the historical source edition.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "exports/cicada-2012-subreddit.json"
SOURCE = ROOT / "exports/sources/gutenberg-5160-2021.txt"
OUTPUT = ROOT / "exports/cicada-2012-source-comparison.json"
INCIPIT = "King Arthur was at Caerlleon upon Usk"


def words(value):
    return re.findall(r"[A-Za-z]+", value.lower())


def display_path(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=LEDGER)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    ledger_bytes = args.ledger.read_bytes()
    source_bytes = args.source.read_bytes()
    ledger = json.loads(ledger_bytes)
    selected = ledger["variants"]["named-author"]["selected_lines"]
    decoded = " ".join(item["decoded"] for item in selected)
    source_text = source_bytes.decode("utf-8-sig")
    if source_text.count(INCIPIT) != 1:
        raise ValueError("Expected one occurrence of the tale's incipit")
    source_tale = source_text[source_text.index(INCIPIT):]
    decoded_words = words(decoded)
    source_words = words(source_tale)
    first_mismatch = next(
        (index + 1 for index, (left, right) in enumerate(zip(decoded_words, source_words))
         if left != right),
        None,
    )
    if first_mismatch is None and len(source_words) < len(decoded_words):
        first_mismatch = len(source_words) + 1
    report = {
        "question": "Does the decoded Reddit excerpt follow Gutenberg ebook 5160 word for word?",
        "scope": "Named-author selection, 185 text posts; words A-Z only, case-insensitive.",
        "ledger": display_path(args.ledger),
        "ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
        "source": display_path(args.source),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_url": "https://www.gutenberg.org/ebooks/5160",
        "source_note": "Current preserved Gutenberg file says it was most recently updated in 2021; it is not a 2012 byte witness.",
        "post_count": len(selected),
        "decoded_word_count": len(decoded_words),
        "matching_word_prefix": (first_mismatch - 1 if first_mismatch else len(decoded_words)),
        "first_mismatch_word": first_mismatch,
        "first_post_ending": selected[0]["decoded"].split()[-5:],
        "last_post_ending": selected[-1]["decoded"].split()[-5:],
        "source_next_words": source_words[len(decoded_words):len(decoded_words) + 8],
        "limits": [
            "Word agreement does not prove which ebook revision or printed edition the authors used.",
            "Whitespace and punctuation are ignored; Reddit title line breaks remain necessary for the book-code lookups.",
            "The comparison does not explain why posting continued after lookup line 76.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"Matched {report['matching_word_prefix']} of {len(decoded_words)} decoded words; report: {args.output}")
    if first_mismatch:
        raise SystemExit(f"First mismatch at word {first_mismatch}")


if __name__ == "__main__":
    main()
