"""Check recorded doublets against source regex matches and exhaustive toy shuffles."""
from fractions import Fraction
from itertools import permutations
import json
from pathlib import Path
import re

from rune_doublets import summary

ROOT = Path(__file__).resolve().parents[1]
r = json.loads((ROOT/"exports/unsolved-doublets.json").read_text(encoding="utf-8"))
alphabet = r["alphabet"]
chars = "".join(a["rune"] for a in alphabet)
page_streams = {}
raws = {}
for number in range(56):
    page = f"lp2-{number:02d}"
    raw = (ROOT/f"text/{page}.txt").read_text(encoding="utf-8")
    raws[page] = raw
    page_streams[page] = "".join(re.findall(f"[{chars}]", raw))
for mode, streams in (("page", list(page_streams.values())),
                      ("joined", ["".join(page_streams.values())])):
    expected = {a["rune"]: sum(len(list(re.finditer(f"(?=({a['rune']}{a['rune']}))", s)))
                                for s in streams) for a in alphabet}
    assert r[mode]["count_vector"] == [expected[a["rune"]] for a in alphabet]
    assert r[mode]["windows"] == sum(max(0, len(s)-1) for s in streams)
    assert r[mode]["doublets"] == sum(expected.values()) == 86
    # Compare the full location set, not just the aggregate count.
    located = []
    for page, stream in page_streams.items():
        located.extend((page, m.start()) for m in re.finditer(r"(?=(.)\1)", stream))
    if mode == "page":
        assert located == [(e["left"]["page"], e["left"]["rune_index_zero_based"])
                           for e in r[mode]["occurrences"]]
    for e in r[mode]["occurrences"]:
        left, right = e["left"], e["right"]
        assert left["rune"] == right["rune"]
        for position in (left, right):
            raw = raws[position["page"]]
            offset = position["source_offset_zero_based"]
            assert raw[offset] == position["rune"]
            assert len(re.findall(f"[{chars}]", raw[:offset])) == position["rune_index_zero_based"]
            assert raw[:offset].count("\n")+1 == position["line_one_based"]
            assert offset-raw.rfind("\n", 0, offset) == position["column_one_based"]
        if left["page"] == right["page"]:
            assert right["rune_index_zero_based"] == left["rune_index_zero_based"]+1
assert r["page"]["occurrences"] == r["joined"]["occurrences"]
assert r["page"]["421_start_indices_zero_based"] == [3, 11, 22]

# Exact mean of every distinct toy ordering validates the finite-sample expectation.
for text in ("", "A", "AAAA", "AABC", "AABB"):
    orders = set(permutations(text))
    average = Fraction(sum(sum(a == b for a, b in zip(s, s[1:])) for s in orders), len(orders))
    measured = summary([[{"rune": c} for c in text]], [{"rune": c} for c in "ABC"])
    assert Fraction(measured["shuffle_expected_doublets"]) == average
    assert measured["doublets"] == sum(a == b for a, b in zip(text, text[1:]))
print("PASS all 86 source locations, both count vectors, overlap handling and exact toy shuffle expectations")

# Check the transition identity independently through modular inverses.
constraint = r['multiplicative_ea_constraint']
for key in range(1, 29):
    inverse = pow(key, -1, 29)
    decoded = [(difference * inverse + 28) % 29 for difference in range(29)]
    assert decoded[0] == 28 and 28 not in decoded[1:]
    assert len(set(decoded)) == 29
for row in constraint['rows']:
    assert row['keys_producing_repeat'] == (list(range(1, 29)) if row['plaintext_index'] == 28 else [])
assert constraint['transitions_checked'] == 23548
zero = constraint['zero_key_counterexample']
assert (zero['previous'] + zero['key'] * (zero['plaintext'] - 28)) % 29 == zero['current'] == zero['previous']
assert zero['plaintext'] != 28
composite = constraint['composite_modulus_counterexample']
assert (composite['previous'] + composite['key'] * (composite['plaintext'] - composite['offset'])) % composite['modulus'] == composite['current'] == composite['previous']
assert composite['plaintext'] != composite['offset']
print('PASS: nonzero-key inverse constraint and zero-key/composite-modulus counterexamples')
