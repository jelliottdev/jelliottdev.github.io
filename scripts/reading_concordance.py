"""Find words or phrases in the nine contextual known-reading sections.

Default: contextual English by section. --literal: decoded rune labels by page.
Positions are word or character positions, never rune offsets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

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


def literal_concordance(root, query, prefix=False, context=10):
    """Join slash/newline wraps while preserving original character positions."""
    concordance([], query, prefix, context)
    hits, sources = [], []
    for path in sorted((root / "data/pages").glob("*.json")):
        raw = path.read_bytes()
        page = json.loads(raw)
        literal = (page.get("reading") or {}).get("literal")
        if not literal:
            continue
        offsets = [i for i, char in enumerate(literal) if char not in "/\r\n"]
        joined = "".join(literal[i] for i in offsets)
        source = {"page": page["id"], "path": path.relative_to(root).as_posix(),
                  "sha256": hashlib.sha256(raw).hexdigest()}
        sources.append(source)
        controls = [{"id": page["id"], "pages": [page["id"]], "reading": joined}]
        spans = list(WORD.finditer(joined))
        for hit in concordance(controls, query, prefix, context):
            start = offsets[hit["source_start"]]
            end = offsets[hit["source_end"] - 1] + 1
            first = max(0, hit["word_start"] - 1 - context)
            last = min(len(spans), hit["word_end"] + context) - 1
            hit.update(
                page=page["id"], source=source["path"], source_sha256=source["sha256"],
                source_start=start, source_end=end, matched_source=literal[start:end],
                line_start=literal.count("\n", 0, start) + 1,
                line_end=literal.count("\n", 0, end - 1) + 1,
                source_excerpt=literal[offsets[spans[first].start()]:offsets[spans[last].end() - 1] + 1],
                reading_url="https://jelliottdev.github.io/#/page/" + page["id"])
            del hit["section"]
            del hit["section_pages"]
            hits.append(hit)
    return hits, sources


def render_result(result, structured=False):
    if structured:
        return json.dumps(result, ensure_ascii=True, indent=2) + "\n"
    lines = [
        (f"{result['occurrences']} occurrences across {result['pages_searched']} literal page readings."
         if "pages_searched" in result else
         f"{result['occurrences']} occurrences across {result['sections_searched']} known-reading sections."),
        result["representation"],
        result["position_convention"],
    ]
    for h in result["hits"]:
        lines.extend([
            (f"\n{h['page']}, literal lines {h['line_start']}–{h['line_end']}, word {h['word_start']}"
             if "page" in h else
             f"\n{h['section']} ({', '.join(h['section_pages'])}), word {h['word_start']}"),
            f"{h['before']} [{h['matched']}] {h['after']}".strip(),
            h["reading_url"],
        ])
    if "source_sha256" in result:
        lines.append("\nSource SHA-256: " + result["source_sha256"])
    else:
        lines.append("\nPer-page source hashes are included in the JSON report.")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Word or quoted phrase; case-insensitive")
    parser.add_argument("--literal", action="store_true",
                        help="Search per-page decoded labels, joining slash/newline wraps")
    parser.add_argument("--prefix", action="store_true", help="Match words beginning with the query")
    parser.add_argument("--context", type=int, default=10, help="Surrounding words per side (0–50)")
    parser.add_argument("--json", action="store_true", help="Print a structured result")
    parser.add_argument("--output", type=Path, help="Save UTF-8 text or JSON without overwriting")
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
    if args.literal:
        try:
            hits, sources = literal_concordance(ROOT, args.query, args.prefix, args.context)
        except ValueError as error:
            parser.error(str(error))
        for key in ("source", "source_sha256", "sections_searched"):
            del result[key]
        result.update(
            schema="liberpedia-literal-concordance-v1",
            representation="Per-page literal decoded labels; slash and CR/LF wraps removed before tokenization; no spelling expansion",
            position_convention="One-based words in joined literal labels and one-based literal text lines; neither is a rune offset",
            source_offset_convention="Zero-based Unicode character offsets into the page reading.literal; end exclusive",
            pages_searched=len(sources), sources=sources, occurrences=len(hits), hits=hits)
    rendered = render_result(result, args.json)
    if args.output:
        try:
            with args.output.open("x", encoding="utf-8", newline="") as destination:
                destination.write(rendered)
        except OSError as error:
            parser.error(str(error))
        print("Saved report:", args.output)
    else:
        sys.stdout.reconfigure(encoding="utf-8", newline="")
        print(rendered, end="")


if __name__ == "__main__":
    main()
