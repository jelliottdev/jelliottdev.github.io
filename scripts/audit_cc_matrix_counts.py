"""Recount section-size claims in the supplied CC matrix proposal.

This checks representation lengths, not spiral routes or a decryption.
Run with --check to compare the saved report without rewriting it.
"""

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/source-intake/cc-matrix-counts.json"
GROUPS = ((0, 2), (3, 7), (8, 14), (15, 15), (16, 22),
          (23, 26), (27, 31), (32, 32), (33, 38), (33, 39), (39, 39))


def report():
    index_path = ROOT / "data/index.json"
    alphabet = json.loads(index_path.read_text(encoding="utf-8"))["alphabet"]
    lookup = {entry["rune"]: (position, entry["prime"])
              for position, entry in enumerate(alphabet)}
    sources = {"data/index.json": hashlib.sha256(index_path.read_bytes()).hexdigest()}
    pages = {}
    for number in range(40):
        relative = f"text/lp2-{number:02}.txt"
        path = ROOT / relative
        raw = path.read_text(encoding="utf-8")
        unknown = {char for char in raw if "\u16a0" <= char <= "\u16ff"} - lookup.keys()
        if unknown:
            raise ValueError(f"Unknown runes in {relative}: {unknown}")
        pages[number] = "".join(char for char in raw if char in lookup)
        sources[relative] = hashlib.sha256(path.read_bytes()).hexdigest()

    groups = []
    for first, last in GROUPS:
        stream = "".join(pages[number] for number in range(first, last + 1))
        groups.append({
            "pages": f"lp2-{first:02}–{last:02}",
            "runes": len(stream),
            "prime_digits": sum(len(str(lookup[char][1])) for char in stream),
            "index_0_digits": sum(len(str(lookup[char][0])) for char in stream),
            "index_1_digits": sum(len(str(lookup[char][0] + 1)) for char in stream),
        })
    page_15 = (ROOT / "text/lp2-15.txt").read_text(encoding="utf-8")
    header, _, remainder = page_15.partition("\n")
    body = "".join(char for char in remainder if char in lookup)
    assert len(pages[15]) - sum(char in lookup for char in header) == len(body)
    result = {
        "schema": "liberpedia-cc-matrix-counts-v1",
        "scope": "Archived GP runes; count decimal digits of each value before concatenation."
                 " These counts do not select a matrix route.",
        "sources_sha256": sources,
        "groups": groups,
        "lp2_15_body_excluding_header": {
            "runes": len(body),
            "prime_digits": sum(len(str(lookup[char][1])) for char in body),
        },
        "reported_fits": {
            "lp2_00_02_runes": 27 * 27,
            "lp2_03_07_prime_digits": 35 * 67,
            "lp2_08_14_runes": 7 * 13 * 19,
            "lp2_08_14_index_1_digits_before_printed_7": 54 * 54 - 1,
            "lp2_15_body_prime_digits": 17 * 17,
            "lp2_16_22_prime_digits": 59 * 59,
            "lp2_23_26_runes_before_red_exclusion": 15 * 67 + 16,
            "lp2_27_31_runes": 32 * 41,
            "lp2_27_31_index_0_digits": 44 * 50,
            "lp2_32_runes": 11 * 11,
            "lp2_32_index_0_digits": 14 * 14,
            "lp2_33_39_runes": 40 * 42,
            "lp2_33_38_runes": 36 * 40,
            "lp2_39_runes": 15 * 16,
        },
    }
    by_range = {entry["pages"]: entry for entry in groups}
    assert by_range["lp2-00–02"]["runes"] == 729
    assert by_range["lp2-03–07"]["prime_digits"] == 2345
    assert by_range["lp2-08–14"]["runes"] == 1729
    assert by_range["lp2-08–14"]["index_1_digits"] == 2915
    assert result["lp2_15_body_excluding_header"] == {"runes": 150, "prime_digits": 289}
    assert by_range["lp2-16–22"]["prime_digits"] == 3481
    assert by_range["lp2-23–26"]["runes"] == 1021
    assert by_range["lp2-27–31"]["runes"] == 1312
    assert by_range["lp2-27–31"]["index_0_digits"] == 2200
    assert by_range["lp2-32–32"]["runes"] == 121
    assert by_range["lp2-32–32"]["index_0_digits"] == 196
    assert by_range["lp2-33–39"]["runes"] == 1680
    assert by_range["lp2-33–38"]["runes"] == 1440
    assert by_range["lp2-39–39"]["runes"] == 240
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    if args.check:
        assert json.loads(OUTPUT.read_text(encoding="utf-8")) == result
        print("PASS: saved CC matrix-count audit matches pinned inputs")
    else:
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8", newline="\n")
        print(f"Wrote {OUTPUT.relative_to(ROOT)}")
