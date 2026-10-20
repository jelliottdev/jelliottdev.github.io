"""Independent cut-mask segmentation and two-point affine-key derivation."""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
lookup = {r["latin"]: (i, r["prime"]) for i, r in enumerate(alphabet)}
# Locate the lower block from the archived paragraph boundary, not line_index.
raw = (ROOT / "text/lp2-39.txt").read_text(encoding="utf-8")
header = raw.split("&", 1)[1].strip().split(".", 1)[0]
runes = {r["rune"]: i for i,r in enumerate(alphabet)}
cipher = [runes[c] for c in header]
assert cipher == result["ciphertext_indices"] == [27, 5, 15]
for row in result["rows"]:
    word = row["word"]
    expected = {}
    for mask in range(1 << (len(word)-1)):
        cuts = [0] + [i for i in range(1,len(word)) if mask & (1 << (i-1))] + [len(word)]
        labels = tuple(word[a:b] for a,b in zip(cuts,cuts[1:]))
        if not all(x in lookup for x in labels):
            continue
        indices = [lookup[x][0] for x in labels]
        keys = []
        if len(indices) == 3 and indices[0] != indices[1]:
            a = ((cipher[1]-cipher[0]) * pow((indices[1]-indices[0]) % 29, -1, 29)) % 29
            b = (cipher[0]-a*indices[0]) % 29
            if a and (a*indices[2]+b) % 29 == cipher[2]:
                keys = [{"a": a, "b": b}]
        expected[labels] = {"indices":indices,"sum":sum(lookup[x][1] for x in labels),"affine_keys":keys}
    assert set(expected) == {tuple(v["labels"]) for v in row["variants"]}
    for v in row["variants"]:
        assert all(v[k] == val for k,val in expected[tuple(v["labels"])].items())
        assert v["length"] == len(v["labels"])
        assert v["length_matches"] == (len(v["labels"]) == 3)
assert [r["word"] for r in result["rows"]] == plan["candidates"]
assert result["candidate_count"] == 20
assert result["segmentation_count"] == 22
assert result["eligible_segmentations"] == 17
assert result["affine_key_trials"] == 13804
assert result["matching_candidates"] == ["WHY"]
print("PASS: cut-mask segmentation, original-text header and algebraic affine keys agree")
