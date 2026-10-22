"""Independent direct equation checks for the saved LP2-54 feedback census."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
alphabet = plan["alphabet"]
raw = (ROOT / "text/lp2-54.txt").read_text(encoding="utf-8")
cipher = [alphabet.index(ch) for ch in raw if ch in alphabet]
assert len(cipher) == 232 and cipher[:9] == [24, 19, 21, 23, 27, 2, 14, 10, 19]
assert result["cipher_indices"] == cipher
assert len(result["cases"]) == 58
seen = set()
for case in result["cases"]:
    mode, primer = case["mode"], case["primer"]
    assert mode in plan["modes"] and 0 <= primer < 29 and (mode, primer) not in seen
    seen.add((mode, primer))
    plain = case["plain_indices"]
    assert len(plain) == 232 and all(0 <= x < 29 for x in plain)
    for i in range(232):
        previous = primer if i == 0 else (cipher[i - 1] if mode == "ciphertext_feedback" else plain[i - 1])
        assert (plain[i] + previous) % 29 == cipher[i], (mode, primer, i)
    assert plain[:9] == case["header_indices"]
    assert case["header_labels"] == [plan["labels"][x] for x in plain[:9]]
    assert case["plain_runes"] == "".join(alphabet[x] for x in plain)
    expected_first = next((label for label in plan["first_plain_rune_candidates"] if plan["labels"][plain[0]] == label), None)
    assert case["first_plain_rune"] == expected_first
assert {p for _, p in seen} == set(range(29))
assert sum(bool(c["first_plain_rune"]) for c in result["cases"]) == 6
print("PASS: independent equations, six A/I/O openings, all 58 complete outputs")
