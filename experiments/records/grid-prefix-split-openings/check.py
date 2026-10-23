#!/usr/bin/env python3
"""Independent source reconstruction and full fixed-opening result check."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE60 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx"


def main():
    pbytes = (HERE / "plan.json").read_bytes()
    plan = json.loads(pbytes)
    result = json.loads((HERE / "results.json").read_text(encoding="utf8"))
    assert hashlib.sha256(pbytes).hexdigest() == result["plan_sha256"]
    assert plan["base60_alphabet"] == BASE60
    for entry in [plan["source_grid"], plan["source_opening_plan"], plan["rune_alphabet"], *plan["pages"]]:
        b = (ROOT / entry["path"]).read_bytes()
        assert hashlib.sha256(b).hexdigest() == entry["sha256"]
        if "bytes" in entry:
            assert len(b) == entry["bytes"]
    prior = json.loads((ROOT / plan["source_opening_plan"]["path"]).read_text(encoding="utf8"))
    assert plan["openings"] == prior["openings"]
    alphabet = [r["rune"] for r in json.loads((ROOT / plan["rune_alphabet"]["path"]).read_text(encoding="utf8"))["alphabet"]]
    assert len(set(alphabet)) == 29
    idx = {r: i for i, r in enumerate(alphabet)}
    for opening in plan["openings"]:
        assert len(opening["indices"]) == 12
        assert hashlib.sha256((ROOT / opening["source"]).read_bytes()).hexdigest() == opening["sha256"]
    source = json.loads((ROOT / plan["source_grid"]["path"]).read_text(encoding="utf8"))["records"]
    assert len(source) == 256 and [r["sequence"] for r in source] == list(range(1, 257))
    streams = {str(n): "" for n in range(5)}
    for cell in source:
        tok = cell["token"]
        assert len(tok) == 2 and tok[0] in streams and tok[1] in BASE60
        streams[tok[0]] += tok[1]
    assert [len(streams[str(i)]) for i in range(5)] == [60, 58, 65, 56, 17]
    assert streams["4"] == "97DEF756B98A80EB9"
    assert [(x["prefix"], x["suffixes"]) for x in plan["channels"]] == list(streams.items())
    pages = []
    for p in plan["pages"]:
        runes = [idx[c] for c in (ROOT / p["path"]).read_text(encoding="utf8") if c in idx]
        assert len(runes) >= 12
        pages.append((p["id"], runes[:12]))
    assert len(pages) == 55 and "lp2-50" not in [pid for pid, _ in pages]
    assert [pid for pid, _ in pages] == [x for x in prior["pages"] if x != "lp2-50"]

    # A planted opening with an odd 17-value key and phase 16 crosses key wrap.
    planted = list(range(12))
    synthetic = [((7 * j + 2) % 29) for j in range(17)]
    for sign in (-1, 1):
        for phase in (0, 11, 16):
            cipher = [(v - sign * synthetic[(j + phase) % 17]) % 29 for j, v in enumerate(planted)]
            decoded = [(c + sign * synthetic[(j + phase) % 17]) % 29 for j, c in enumerate(cipher)]
            assert decoded == planted
    assert result["controls"] == {"odd_key_length": 17, "phases": [0, 11, 16], "signs": [-1, 1], "passed": 6}

    expected_groups = []
    hit_inventory = []
    for leading, suffixes in streams.items():
        for representation in (["base60-digit-mod29", "ascii-byte-mod29", "group4-hex-nibble"] if leading == "4" else ["base60-digit-mod29", "ascii-byte-mod29"]):
            if representation == "base60-digit-mod29":
                key = [BASE60.index(c) % 29 for c in suffixes]
            elif representation == "ascii-byte-mod29":
                key = [c % 29 for c in suffixes.encode("ascii")]
            else:
                assert all(c in "0123456789ABCDEF" for c in suffixes)
                key = [int(c, 16) for c in suffixes]
            best = -1
            tie_count = 0
            examples = []
            hits = []
            configs = 0
            for pid, ciphertext in pages:
                for phase in range(len(key)):
                    for sign in (-1, 1):
                        configs += 1
                        decoded = tuple((ciphertext[j] + sign * key[(j + phase) % len(key)]) % 29 for j in range(12))
                        for opening in plan["openings"]:
                            prefix = 0
                            for a, b in zip(decoded, opening["indices"]):
                                if a != b:
                                    break
                                prefix += 1
                            if prefix > best:
                                best, tie_count, examples = prefix, 0, []
                            if prefix == best:
                                tie_count += 1
                                if len(examples) < 5:
                                    examples.append({"page": pid, "phase": phase, "sign": sign, "opening": opening["id"]})
                            if prefix == 12:
                                hits.append({"page": pid, "phase": phase, "sign": sign, "opening": opening["id"]})
            expected_groups.append({"prefix": leading, "mapping": representation, "key_length": len(key),
                                    "key_indices": key, "configurations": configs,
                                    "opening_comparisons": configs * len(plan["openings"]),
                                    "max_prefix": best, "max_prefix_ties": tie_count,
                                    "max_prefix_examples": examples, "exact_matches": hits})
            hit_inventory.extend({"prefix": leading, "mapping": representation, **h} for h in hits)
    assert result["groups"] == expected_groups
    assert result["group_count"] == len(expected_groups) == 11
    assert result["configuration_count"] == sum(x["configurations"] for x in expected_groups) == 58190
    assert result["opening_comparison_count"] == 523710
    assert result["exact_matches"] == hit_inventory == []
    g4 = [g for g in result["groups"] if g["prefix"] == "4"]
    assert g4[0]["key_indices"] == g4[2]["key_indices"]
    print("Independent check passed: five source channels, 58,190 named page cases, 523,710 crib comparisons, zero exact openings")


if __name__ == "__main__":
    main()
