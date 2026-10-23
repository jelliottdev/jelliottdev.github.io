"""Recount a reported LP1 seven-word, 21-rune, GP-825 coincidence.

Uses the shipped decoded-rune traces and archived word separators. It does not
test the proposed LP2 phrase or treat a selected coincidence as a decryption.
"""

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/source-intake/lp1-seven-word-825-audit.json"
SECTIONS = {
    "warning": ("01",),
    "welcome": ("03", "04"),
    "some-wisdom": ("05",),
    "first-koan": ("06", "07", "08", "09"),
    "loss-of-divinity": ("10", "11", "12", "13"),
    "second-koan": ("14", "15"),
    "instruction": ("16",),
}


def report():
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    by_rune = {entry["rune"]: (i, entry["prime"], entry["latin"])
               for i, entry in enumerate(alphabet)}
    inputs = {}
    groups = []
    all_words = []
    matches = []
    for section, pages in SECTIONS.items():
        csv_path = ROOT / "exports/readings" / f"{section}.csv"
        with csv_path.open(encoding="utf-8", newline="") as stream:
            trace = list(csv.DictReader(stream))
        inputs[csv_path.relative_to(ROOT).as_posix()] = hashlib.sha256(csv_path.read_bytes()).hexdigest()
        page_texts = []
        for page in pages:
            path = ROOT / "text" / f"lp1-{page}.txt"
            inputs[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
            text = path.read_text(encoding="utf-8")
            if page == "10":
                # The published known-reading trace swaps this documented
                # pair; no analogous correction is assumed for other pages.
                chars = list(text)
                positions = [i for i, char in enumerate(chars) if char in by_rune]
                a, b = positions[116], positions[117]
                chars[a], chars[b] = chars[b], chars[a]
                text = "".join(chars)
            page_texts.append(text)
        raw = "".join(page_texts)
        decoded = []
        used = 0
        for char in raw:
            if char in by_rune:
                row = trace[used]
                assert row["input_rune"] == char
                decoded.append(alphabet[int(row["output_index"])]["rune"])
                used += 1
            elif char not in "/\n\r'":
                decoded.append(" ")
            # Slash and newlines are archival line wrapping, not word breaks.
        assert used == len(trace)
        words = re.findall("[\u16a0-\u16ff]+", "".join(decoded))
        groups.append({"section": section, "word_count": len(words),
                       "within_section_seven_word_windows": max(0, len(words) - 6)})
        for start in range(len(words) - 6):
            window = words[start:start + 7]
            rune_count = sum(map(len, window))
            prime_sum = sum(by_rune[c][1] for word in window for c in word)
            if rune_count == 21 and prime_sum == 825:
                matches.append({
                    "section": section,
                    "start_word_zero_based": start,
                    "latin": " ".join("".join(by_rune[c][2] for c in word) for word in window),
                    "rune_count": rune_count,
                    "prime_sum": prime_sum,
                    "index_sum": sum(by_rune[c][0] for word in window for c in word),
                })
        all_words.extend(words)
    result = {
        "schema": "liberpedia-lp1-825-window-audit-v1",
        "scope": "Seven solved LP1 sections; decoded runes from published traces; words from"
                 " archived rune separators; no windows cross a section boundary; the"
                 " 13 rune-word cells in the LP1-05 square remain included.",
        "inputs_sha256": inputs,
        "sections": groups,
        "all_rune_words": len(all_words),
        "within_section_seven_word_windows": sum(g["within_section_seven_word_windows"] for g in groups),
        "cross_section_windows_if_all_words_concatenated": max(0, len(all_words) - 6),
        "matches_21_runes_gp_825": matches,
    }
    assert len(all_words) == 694, groups
    assert len(matches) >= 1
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    if args.check:
        assert json.loads(OUTPUT.read_text(encoding="utf-8")) == result
        print("PASS: saved LP1 seven-word census matches pinned traces")
    else:
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8", newline="\n")
        print(f"Wrote {OUTPUT.relative_to(ROOT)}")
