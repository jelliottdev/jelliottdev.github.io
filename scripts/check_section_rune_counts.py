"""Independently recount every span and equation in section-rune-counts.json."""
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
report = json.loads((ROOT / "exports/section-rune-counts.json").read_text(encoding="utf-8"))
source_path = ROOT / report["source_snapshot"]
source_bytes = source_path.read_bytes()
assert hashlib.sha256(source_bytes).hexdigest() == report["input_sha256"][report["source_snapshot"]]
sheet = [row for row in csv.reader(io.StringIO(source_bytes.decode("utf-8"), newline=""))
         if row and row[0].isdigit()]
assert len(sheet) == len(report["sections"]) == 23

# This checker uses the Unicode runic block, rather than the alphabet table
# and character-filtering loop in the producing script.
def runes(text):
    return "".join(c for c in text if "\u16a0" <= c <= "\u16ff")


used = {}
by_name = {}
for row, original in zip(report["sections"], sheet):
    assert [str(row["order"]), row["section"], str(row["runes"]),
            str(row["without_f"])] == original
    n = zeros = 0
    for span in row["spans"]:
        page = span["page"]
        part = span["part_after_ampersand"]
        pieces = [runes(piece) for piece in (ROOT / f"text/{page}.txt").read_text(encoding="utf-8").split("&")]
        pieces = [piece for piece in pieces if piece]
        text = "".join(pieces) if part is None else pieces[part]
        assert len(text) == span["runes"] and text.count("ᚠ") == span["f_runes"]
        assert (page, part) not in used
        used[page, part] = row["section"]
        n += len(text)
        zeros += text.count("ᚠ")
    assert (n, zeros, n - zeros) == (row["runes"], row["f_runes"], row["without_f"])
    by_name[row["section"]] = row

for equality in report["equalities"]:
    for expression in equality["expressions"]:
        value = sum(by_name[term["section"]][term["measure"]] * term["sign"]
                    for term in expression)
        assert value == equality["value"]

assert [(item["value"], len(item["expressions"])) for item in report["equalities"]] == [
    (2883, 2), (1894, 2), (1433, 3), (1814, 2), (695, 2), (91, 2)]
assert sum(row["runes"] for row in report["sections"]) == 15933
assert sum(row["without_f"] for row in report["sections"]) == 15396
print("PASS: independent Unicode-block recount of 23 sections and six equalities")
