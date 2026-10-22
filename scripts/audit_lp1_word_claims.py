"""Recount a reported LP1 word/word-type claim from pinned page readings.

This is a source-bound audit, not a cipher experiment. Run with --check to
compare the complete saved result with a fresh calculation.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "source-intake" / "lp1-word-count-audit.json"
WORDS = re.compile(r"[A-Z]+(?:'[A-Z]+)?|[0-9]+")
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
RUNE_WORDS = re.compile(f"[{RUNES}]+(?:'[{RUNES}]+)*")
SECTIONS = (
    "warning", "welcome", "some-wisdom", "first-koan",
    "loss-of-divinity", "second-koan", "instruction",
)
SECTION_PAGES = {
    "warning": ("01",), "welcome": ("03", "04"),
    "some-wisdom": ("05",), "first-koan": ("06", "07", "08", "09"),
    "loss-of-divinity": ("10", "11", "12", "13"),
    "second-koan": ("14", "15"), "instruction": ("16",),
}


def recount() -> dict:
    pages = []
    section_words = {}
    for path in sorted((ROOT / "data" / "pages").glob("lp1-*.json")):
        page = json.loads(path.read_text(encoding="utf-8"))
        reading = page.get("reading") or {}
        section = reading.get("section")
        if section not in SECTIONS or section in section_words:
            continue
        tokens = WORDS.findall(reading["reading"].upper())
        section_words[section] = tokens
        pages.append({
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "section": section,
        })
    if tuple(section_words) != SECTIONS:
        raise ValueError(f"Unexpected LP1 section inventory: {tuple(section_words)}")

    # LP1-05's known reading appends the 5×5 square after KNOW THIS. The
    # separate numeric tokens are not rune words, and 13 cells are words.
    wisdom = section_words["some-wisdom"]
    square_start = wisdom.index("KNOW") + 2
    if wisdom[square_start - 2:square_start] != ["KNOW", "THIS"]:
        raise ValueError("LP1-05 square boundary moved")
    square = wisdom[square_start:]
    if len(square) != 25 or sum(t.isdigit() for t in square) != 12:
        raise ValueError("LP1-05 square is not the pinned 25-cell text")
    square_words = [t for t in square if not t.isdigit()]

    all_words = [
        token for section in SECTIONS for token in section_words[section]
        if not token.isdigit()
    ]
    prose_words = all_words.copy()
    for token in square_words:
        prose_words.remove(token)
    # The removal above affects the multiset, not word order; frequencies and
    # type counts are all that are computed below.
    all_freq = Counter(all_words)
    prose_freq = Counter(prose_words)
    section_counts = []
    ciphertext_inputs = []
    for section in SECTIONS:
        tokens = section_words[section]
        raw = ""
        for number in SECTION_PAGES[section]:
            path = ROOT / "text" / f"lp1-{number}.txt"
            ciphertext_inputs.append({
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
            raw += path.read_text(encoding="utf-8").replace("/", "").replace("\n", "")
        rune_word_count = len(RUNE_WORDS.findall(raw))
        if rune_word_count != sum(not t.isdigit() for t in tokens):
            raise ValueError(f"Ciphertext/readings disagree on word count: {section}")
        section_counts.append({
            "section": section,
            "all_tokens": len(tokens),
            "rune_word_tokens": rune_word_count,
            "numeric_tokens": sum(t.isdigit() for t in tokens),
        })
    return {
        "schema": "liberpedia-lp1-word-claim-audit-v1",
        "scope": "One reading per seven solved LP1 sections, pinned contextual English in data/pages/lp1-*.json. Uppercase ASCII word tokens with an internal apostrophe retained; numeric square cells excluded from rune-word totals. LP1-05 square has 25 cells, 13 of them rune words. This is not a fresh image transcription audit.",
        "inputs": pages,
        "ciphertext_inputs": ciphertext_inputs,
        "section_counts": section_counts,
        "lp1_05_square_words": square_words,
        "all_rune_words": {
            "tokens": len(all_words),
            "distinct_types": len(all_freq),
            "hapax_types": sum(v == 1 for v in all_freq.values()),
            "within_tokens": all_freq["WITHIN"],
            "instruction_tokens": all_freq["INSTRUCTION"],
        },
        "excluding_lp1_05_square": {
            "tokens": len(prose_words),
            "distinct_types": len(prose_freq),
            "hapax_types": sum(v == 1 for v in prose_freq.values()),
            "within_tokens": prose_freq["WITHIN"],
            "instruction_tokens": prose_freq["INSTRUCTION"],
        },
        "reported": {"tokens_without_square": 681, "tokens_with_square": 694,
                     "unique_without_square": 109, "unique_with_square": 121,
                     "within_tokens": 6, "instruction_tokens": 4},
        "interpretation": "681 and 694 reproduce when the 13 LP1-05 square words are toggled. Under ordinary distinct case-insensitive word types, the corresponding totals are 245 and 256, not 109 and 121. WITHIN appears four times in these seven contextual LP1 readings; INSTRUCTION appears four times. The supplied source does not define 'unique' or identify two additional WITHIN occurrences, so those claims are unresolved rather than disproved for every possible corpus convention.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = recount()
    data = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != data:
            raise SystemExit("Saved LP1 word audit differs from fresh recount")
        print("LP1 word audit matches saved result")
    else:
        OUT.write_text(data, encoding="utf-8")
        print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
