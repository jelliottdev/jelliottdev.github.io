"""Replay the published section-count sheet against archived page transcriptions.

The only within-page splits are the explicit '&' section markers in source text.
This counts runes; it neither aligns nor decrypts their values.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "data/source-snapshots/lp-rune-counts-2026-10-22.csv"
OUTPUT = "exports/section-rune-counts.json"


def pages(release, first, last):
    return [(f"{release}-{i:02}", None) for i in range(first, last + 1)]


# A part number means the first (0) or second (1) rune-bearing piece around
# an '&' marker. None means the entire page, including every piece.
SECTIONS = [
    ("Warning", pages("lp1", 1, 1)),
    ("Welcome", pages("lp1", 3, 4)),
    ("Some Wisdom", [("lp1-05", 0)]),
    ("KT1", [("lp1-05", 1)]),
    ("Koan 1", pages("lp1", 6, 9)),
    ("Loss Divinity", pages("lp1", 10, 13)),
    ("Koan 2", pages("lp1", 14, 15)),
    ("Instruction", [("lp1-16", 0)]),
    ("KT2", [("lp1-16", 1)]),
    ("Sign Post", pages("lp2", 0, 2)),
    ("Spirals", pages("lp2", 3, 7)),
    ("Branches", pages("lp2", 8, 14)),
    ("Pre Mobius Table KT3", [("lp2-15", 0)]),
    ("Mobius", [("lp2-15", 1)] + pages("lp2", 16, 22)),
    ("Mayfly", pages("lp2", 23, 26)),
    ("Wing Tree", pages("lp2", 27, 32)),
    ("WT 3 dots", [("lp2-33", 0)]),
    ("Cuneiform", [("lp2-33", 1)] + pages("lp2", 34, 38) + [("lp2-39", 0)]),
    ("Cunieform 3 dots", [("lp2-39", 1)]),
    ("Spiral Brances", pages("lp2", 40, 53)),
    ("54-55", pages("lp2", 54, 55)),
    ("An End", pages("lp2", 56, 56)),
    ("Parable", pages("lp2", 57, 57)),
]

EQUALITIES = [
    ("2883", [[("Spirals", "runes", 1), ("Branches", "runes", 1),
               ("Pre Mobius Table KT3", "runes", 1)],
              [("Spiral Brances", "without_f", 1)]]),
    ("1894", [[("Koan 1", "without_f", 1), ("Loss Divinity", "without_f", 1),
               ("Koan 2", "without_f", 1), ("Instruction", "without_f", 1)],
              [("Mobius", "runes", 1)]]),
    ("1433", [[("Koan 2", "without_f", 1), ("Spirals", "without_f", 1)],
              [("Cuneiform", "without_f", 1)], [("Wing Tree", "runes", 1)]]),
    ("1814", [[("Koan 1", "without_f", 1), ("Loss Divinity", "without_f", 1),
               ("Koan 2", "without_f", 1)],
              [("Sign Post", "without_f", 1), ("Spirals", "without_f", 1)]]),
    ("695", [[("Koan 1", "runes", 1), ("KT1", "runes", -1)],
             [("Sign Post", "without_f", 1)]]),
    ("91", [[("Warning", "without_f", 1), ("Parable", "without_f", -1)],
            [("WT 3 dots", "runes", 1)]]),
]


def calculate():
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    alphabet = {row["rune"] for row in index["alphabet"]}
    f = next(row["rune"] for row in index["alphabet"] if row["index"] == 0)
    assert f == "ᚠ"
    source_bytes = (ROOT / SOURCE).read_bytes()
    source_rows = [row for row in csv.reader(io.StringIO(source_bytes.decode("utf-8"), newline=""))
                   if row and row[0].isdigit()]
    assert len(source_rows) == len(SECTIONS) == 23
    page_rows = {row["id"]: row for row in index["pages"]}
    used = {}
    input_hashes = {SOURCE: hashlib.sha256(source_bytes).hexdigest(),
                    "data/index.json": hashlib.sha256((ROOT / "data/index.json").read_bytes()).hexdigest()}
    output = []
    for position, ((name, spans), source) in enumerate(zip(SECTIONS, source_rows), 1):
        assert source[:2] == [str(position), name]
        chars = []
        details = []
        for page, part in spans:
            path = f"text/{page}.txt"
            raw = (ROOT / path).read_text(encoding="utf-8")
            input_hashes[path] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            unknown = {c for c in raw if "\u16a0" <= c <= "\u16ff"} - alphabet
            if unknown:
                raise ValueError(f"Unknown runes on {page}: {unknown}")
            pieces = ["".join(c for c in text if c in alphabet) for text in raw.split("&")]
            pieces = [text for text in pieces if text]
            assert sum(map(len, pieces)) == page_rows[page]["rune_count"]
            if part is None:
                assert (page, None) not in used and not any(key[0] == page for key in used)
                segment = "".join(pieces)
            else:
                assert len(pieces) == 2 and part in (0, 1)
                assert (page, part) not in used and (page, None) not in used
                segment = pieces[part]
            used[page, part] = name
            chars.append(segment)
            details.append({"page": page, "part_after_ampersand": part,
                            "runes": len(segment), "f_runes": segment.count(f)})
        stream = "".join(chars)
        row = {"order": position, "section": name, "runes": len(stream),
               "f_runes": stream.count(f), "without_f": len(stream) - stream.count(f),
               "spans": details,
               "published_runes": int(source[2]), "published_without_f": int(source[3])}
        assert (row["runes"], row["without_f"]) == (row["published_runes"], row["published_without_f"]), name
        output.append(row)
    for page, record in page_rows.items():
        if record["rune_count"] == 0:
            continue
        parts = [key[1] for key in used if key[0] == page]
        assert parts in ([None], [0, 1]), (page, parts)
    by_name = {row["section"]: row for row in output}
    matches = []
    for label, expressions in EQUALITIES:
        score = lambda terms: sum(by_name[name][metric] * sign for name, metric, sign in terms)
        assert all(score(terms) == int(label) for terms in expressions), label
        matches.append({"value": int(label), "expressions": [
            [{"section": name, "measure": metric, "sign": sign,
              "value": by_name[name][metric]} for name, metric, sign in terms]
            for terms in expressions]})
    totals = {"runes": sum(row["runes"] for row in output),
              "without_f": sum(row["without_f"] for row in output)}
    assert totals == {"runes": 15933, "without_f": 15396}
    return {"schema": "liberpedia-section-rune-counts-v1",
            "source_url": "https://docs.google.com/spreadsheets/d/1iLqpw2RTuapEE_p9WFhTpcwz7PdKJDCysseLbX2ucps/edit",
            "source_snapshot": SOURCE, "retrieved": "2026-10-22",
            "rule": "Count stored 29-alphabet runes; split only at an explicit '&' section marker. Without F removes every ᚠ rune. Full-page spans retain headings. Decimal labels, punctuation and '$' do not count.",
            "input_sha256": dict(sorted(input_hashes.items())), "sections": output,
            "equalities": matches, "totals": totals,
            "limits": "Exact arithmetic on the archived transcription and a saved public spreadsheet snapshot. It does not show a key, alignment rule, chance probability or intentional construction. Section marks and glyphs still depend on source transcription accuracy."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = calculate()
    if args.check:
        assert result == json.loads((ROOT / OUTPUT).read_text(encoding="utf-8"))
        print("PASS: 23 section counts and six reported equalities")
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    if not args.check and not args.output:
        print(json.dumps({"sections": len(result["sections"]), "equalities": len(result["equalities"]),
                          "totals": result["totals"]}))
