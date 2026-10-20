"""Audit reversal using regex spans and reflected positions, not runner grouping."""
import csv
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert result["plan_sha256"] == sha(HERE / "plan.json")
for item in plan["inputs"]:
    assert sha(ROOT / item["path"]) == item["sha256"]
alphabet = [r["rune"] for r in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]]
pattern = re.compile("[" + re.escape("".join(alphabet)) + "]+")
assert [page["page"] for page in result["pages"]] == plan["pages"]
for opening in plan["openings"]:
    with (ROOT / opening["source"]).open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert [int(row["output_index"]) for row in rows[:12]] == opening["indices"]

count = matches = distinct = 0
for page in result["pages"]:
    text = (ROOT / "text" / (page["page"] + ".txt")).read_bytes().decode("utf-8")
    source = [i for i, c in enumerate(text) if c in alphabet]
    assert page["rune_count"] == len(source)
    modes = plan["boundary_modes"] if source else []
    assert [case["boundary_mode"] for case in page["cases"]] == modes
    for case in page["cases"]:
        kept = [
            i for i, c in enumerate(text)
            if case["boundary_mode"] == "split-lines" or c not in "/\r\n"
        ]
        normalized = "".join(text[i] for i in kept)
        spans = [m.span() for m in pattern.finditer(normalized)]
        reflected = [
            kept[start + end - 1 - position]
            for start, end in spans for position in range(start, end)
        ]
        assert case["segment_lengths"] == [end - start for start, end in spans]
        assert case["source_character_offsets"] == reflected
        assert case["source_ordinals"] == [source.index(i) for i in reflected]
        assert sorted(reflected) == source
        output = [alphabet.index(text[i]) for i in reflected]
        assert case["output_indices"] == output
        expected = [o["id"] for o in plan["openings"] if output[:12] == o["indices"]]
        assert case["matching_openings"] == expected
        count += 1
        matches += bool(expected)
    distinct += len({tuple(case["output_indices"]) for case in page["cases"]})
assert result["case_count"] == count == 110
assert result["comparison_count"] == count * len(plan["openings"]) == 990
assert result["matching_case_count"] == matches
assert result["distinct_page_outputs"] == distinct == 110

# The production segmenter gets explicit, hand-calculated boundary controls too.
from run import segments
toy_lookup = {c: i for i, c in enumerate("ABCDEF")}
toy = "AB/C-D\nEF."
assert segments(toy, toy_lookup, False) == [[0, 1], [3], [5], [7, 8]]
assert segments(toy, toy_lookup, True) == [[0, 1, 3], [5, 7, 8]]
for joined, expected in [(False, "BACDFE"), (True, "CBAFED")]:
    assert "".join(toy[i] for group in segments(toy, toy_lookup, joined) for i in reversed(group)) == expected
print("All 110 regex/reflection traces, source hashes, opening vectors and hand controls pass.")
