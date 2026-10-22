"""Independent source-window recount for the saved crib-difference results."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
data = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
by_rune = {x["rune"]: i for i, x in enumerate(alphabet)}
by_label = {x["latin"]: i for i, x in enumerate(alphabet)}
target = json.loads((ROOT / "data/pages/lp2-39.json").read_text(encoding="utf-8"))
ct = [by_rune[c] for c in target["lines"][6]["raw"].split(".")[0]]
assert ct == data["ciphertext_indices"]
wanted = {}
for candidate in data["cribs"]:
    assert "".join(candidate["labels"]) == candidate["word"]
    plain = [by_label[label] for label in candidate["labels"]]
    assert plain == candidate["plaintext_indices"]
    diff = tuple((ct[i] - plain[i]) % 29 for i in range(3))
    assert list(diff) == candidate["difference_indices"]
    wanted.setdefault(diff, []).append(candidate["word"] + " [" + ",".join(candidate["labels"]) + "]")
assert len(wanted) == data["distinct_difference_sequences"]

# Reconstruct page streams from individual line fields and use direct slices;
# the producer instead filters each page's combined raw field.
recount = []
pages = 0
runes = 0
for path in sorted((ROOT / "data/pages").glob("lp[12]-*.json")):
    if path.stem == "lp2-39":
        continue
    page = json.loads(path.read_text(encoding="utf-8"))
    if not page["rune_count"]:
        continue
    seq = [by_rune[c] for line in page["lines"] for c in line["raw"] if c in by_rune]
    assert len(seq) == page["rune_count"]
    pages += 1
    runes += len(seq)
    for i in range(len(seq) - 2):
        key = tuple(seq[i:i + 3])
        if key in wanted:
            recount.append({"page": path.stem, "rune_offset_0": i,
                            "difference_indices": list(key), "cribs": wanted[key]})
assert (pages, runes) == (data["source_page_count"], data["source_rune_count"])
assert recount == data["hits"]
assert len(recount) == data["observed_matching_windows"]
assert sum(data["control"]["histogram"].values()) == data["control"]["replicates"]
assert sum(int(k) * v for k, v in data["control"]["histogram"].items()) / 2000 == data["control"]["mean_matching_windows"]
print("PASS: all candidate differences and every observed source hit independently recounted")
