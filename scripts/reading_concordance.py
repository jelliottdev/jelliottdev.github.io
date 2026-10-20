"""Find words or phrases in the nine contextual known-reading sections.

This searches contextual English, not ciphertext or literal rune labels.
Positions are one-based contextual word positions, never rune offsets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/evidence/known-readings.json"
WORD = re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*")


def words(text):
    return [w.replace("’", "'").upper() for w in WORD.findall(text)]


def concordance(controls, query, prefix=False, context=10):
    needle = words(query)
    if not needle:
        raise ValueError("Enter a word or phrase containing letters or digits.")
    if prefix and len(needle) != 1:
        raise ValueError("Prefix matching accepts one word, not a phrase.")
    if not 0 <= context <= 50:
        raise ValueError("Context must be between 0 and 50 words on each side.")
    ids = [c["id"] for c in controls]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate section IDs would double-count the readings.")
    hits = []
    for c in controls:
        spans = list(WORD.finditer(c["reading"]))
        tokens = words(c["reading"])
        for i in range(len(tokens) - len(needle) + 1):
            match = (tokens[i].startswith(needle[0]) if prefix
                     else tokens[i:i + len(needle)] == needle)
            if match:
                end = i + len(needle)
                source_start, source_end = spans[i].start(), spans[end - 1].end()
                excerpt_start = spans[max(0, i - context)].start()
                excerpt_end = spans[min(len(spans), end + context) - 1].end()
                hits.append({
                    "section": c["id"],
                    "section_pages": c["pages"],
                    "word_start": i + 1,
                    "word_end": end,
                    "matched": " ".join(tokens[i:end]),
                    "before": " ".join(tokens[max(0, i - context):i]),
                    "after": " ".join(tokens[end:end + context]),
                    "source_start": source_start,
                    "source_end": source_end,
                    "matched_source": c["reading"][source_start:source_end],
                    "source_excerpt": c["reading"][excerpt_start:excerpt_end],
                    "reading_url": "https://jelliottdev.github.io/#/wiki/reading-" + c["id"],
                })
    return hits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Word or quoted phrase; case-insensitive")
    parser.add_argument("--prefix", action="store_true", help="Match words beginning with the query")
    parser.add_argument("--context", type=int, default=10, help="Surrounding words per side (0–50)")
    parser.add_argument("--json", action="store_true", help="Print a structured result")
    args = parser.parse_args()
    raw = SOURCE.read_bytes()
    data = json.loads(raw)
    try:
        hits = concordance(data["controls"], args.query, args.prefix, args.context)
    except ValueError as e:
        parser.error(str(e))
    result = {
        "schema": "liberpedia-reading-concordance-v1",
        "source": "data/evidence/known-readings.json",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "representation": "Contextual English; section-level attribution, not exact page placement",
        "tokenization": "ASCII letters/digits; internal apostrophes retained and normalized; other punctuation ignored",
        "position_convention": "One-based contextual word positions; not rune offsets",
        "source_offset_convention": "Zero-based Unicode character offsets into the section reading; end exclusive",
        "query": args.query,
        "mode": "word-prefix" if args.prefix else "exact-token-phrase",
        "context_words_per_side": args.context,
        "sections_searched": len(data["controls"]),
        "occurrences": len(hits),
        "hits": hits,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"{len(hits)} occurrences across {len(data['controls'])} known-reading sections.")
        print(result["representation"])
        print(result["position_convention"])
        for h in hits:
            print(f"\n{h['section']} ({', '.join(h['section_pages'])}), word {h['word_start']}")
            print(f"{h['before']} [{h['matched']}] {h['after']}".strip())
            print(h["reading_url"])
        print("\nSource SHA-256: " + result["source_sha256"])


if __name__ == "__main__":
    main()
