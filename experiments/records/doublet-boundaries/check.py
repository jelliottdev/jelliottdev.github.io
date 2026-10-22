"""Independent regex and stored-ledger check for the LP2 boundary audit."""
from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
old_ledger = json.loads((ROOT / "exports/unsolved-doublets.json").read_text(encoding="utf-8"))["page"]["occurrences"]
assert len(old_ledger) == 86
alphabet = {a["rune"] for a in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}


def category(s):
    if s == "":
        return "contiguous"
    if re.fullmatch(r"[/\r\n]+", s):
        return "row-wrap only"
    if re.fullmatch(r"['/\r\n]+", s):
        return "apostrophe/soft wrap"
    if "-" in s:
        return "hyphen"
    return "other separator"


events = []
all_count = Counter()
for number in range(56):
    page = f"lp2-{number:02d}"
    raw = (ROOT / f"text/{page}.txt").read_text(encoding="utf-8")
    positions = [(m.start(), m.group()) for m in re.finditer(r"[\u16a0-\u16ff]", raw)]
    assert all(rune in alphabet for _, rune in positions)
    for i in range(len(positions) - 1):
        (left, a), (right, b) = positions[i:i+2]
        mark = raw[left+1:right]
        kind = category(mark)
        all_count[kind] += 1
        if a == b:
            events.append((page, i, left, right, mark, kind))
assert len(events) == result["archived"]["doublets"] == 86
assert dict(all_count) == {k: v for k, v in result["archived"]["category_all_pairs"].items() if v}
assert Counter(event[-1] for event in events) == {
    k: v for k, v in result["archived"]["category_doublets"].items() if v}
for calculated, stored, earlier in zip(events, result["events"], old_ledger):
    page, index, left, right, mark, kind = calculated
    assert (stored["page"], stored["rune_index_zero_based"], stored["left_offset_zero_based"],
            stored["right_offset_zero_based"], stored["between"], stored["category"]) == calculated
    assert earlier["left"]["page"] == page
    assert earlier["left"]["source_offset_zero_based"] == left
    assert earlier["right"]["source_offset_zero_based"] == right
for page in result["reviewed_layer"]["pages_with_separate_layer"]:
    data = json.loads((ROOT / f"data/pages/{page}.json").read_text(encoding="utf-8"))
    raw = ''.join(re.findall(r"[\u16a0-\u16ff]", data["raw"]))
    reviewed = ''.join(re.findall(r"[\u16a0-\u16ff]", data["reviewed_text"]))
    assert raw == reviewed
assert result["reviewed_layer"]["doublets"] == 86
assert result["reviewed_layer"]["doublet_category_changes"] == []
print("PASS independent extraction, source offsets, separator counts and stored reviewed layers")
