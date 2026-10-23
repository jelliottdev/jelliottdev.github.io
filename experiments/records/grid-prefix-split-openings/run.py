#!/usr/bin/env python3
"""Run finite grid-suffix repeating-key opening comparisons."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key_values(suffixes, mapping, abc):
    if mapping == "base60-digit-mod29":
        return [abc.index(c) % 29 for c in suffixes]
    if mapping == "ascii-byte-mod29":
        return [ord(c) % 29 for c in suffixes]
    if mapping == "group4-hex-nibble":
        assert len(suffixes) == 17 and all(c in "0123456789ABCDEF" for c in suffixes)
        return [int(c, 16) for c in suffixes]
    raise ValueError(mapping)


def prefix_len(output, opening):
    return next((i for i, (a, b) in enumerate(zip(output, opening)) if a != b), 12)


def decode_first12(cipher, key, phase, sign):
    return [(cipher[j] + sign * key[(j + phase) % len(key)]) % 29 for j in range(12)]


def positive_controls():
    # A nonzero phase of an odd-length key exercises wrap and both orientations.
    key = [i * 7 % 29 for i in range(17)]
    plain = [3, 5, 8, 13, 21, 1, 2, 4, 9, 16, 25, 11]
    for sign in (-1, 1):
        for phase in (0, 11, 16):
            cipher = [(p - sign * key[(j + phase) % 17]) % 29 for j, p in enumerate(plain)]
            assert decode_first12(cipher, key, phase, sign) == plain
            assert prefix_len(decode_first12(cipher, key, phase, sign), plain) == 12
    return {"odd_key_length": 17, "phases": [0, 11, 16], "signs": [-1, 1], "passed": 6}


def run():
    plan_bytes = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_bytes)
    assert plan["schema"] == "liberpedia-grid-prefix-split-openings-plan-v1"
    for entry in [plan["source_grid"], plan["source_opening_plan"], plan["rune_alphabet"], *plan["pages"]]:
        assert sha(ROOT / entry["path"]) == entry["sha256"]
    for opening in plan["openings"]:
        assert sha(ROOT / opening["source"]) == opening["sha256"]
    grid = json.loads((ROOT / plan["source_grid"]["path"]).read_text(encoding="utf8"))["records"]
    assert len(grid) == 256
    for channel in plan["channels"]:
        assert channel["suffixes"] == "".join(r["token"][1] for r in grid if r["token"][0] == channel["prefix"])
    alphabet = [x["rune"] for x in json.loads((ROOT / "data/index.json").read_text(encoding="utf8"))["alphabet"]]
    assert len(set(alphabet)) == len(alphabet) == 29
    index = {c: j for j, c in enumerate(alphabet)}
    pages = {}
    for p in plan["pages"]:
        source = (ROOT / p["path"]).read_text(encoding="utf8")
        indices = [index[c] for c in source if c in index]
        assert len(indices) >= 12
        pages[p["id"]] = indices[:12]
    assert len(pages) == 55
    assert len(plan["openings"]) == 9
    controls = positive_controls()
    groups = []
    full_matches = []
    computed = {}
    for channel in plan["channels"]:
        prefix = channel["prefix"]
        mappings = plan["mappings"][:2] + (["group4-hex-nibble"] if prefix == "4" else [])
        for mapping in mappings:
            key = key_values(channel["suffixes"], mapping, plan["base60_alphabet"])
            assert key
            effective = tuple(key)
            if effective in computed:
                group = deepcopy(computed[effective])
                group["prefix"] = prefix
                group["mapping"] = mapping
                groups.append(group)
                full_matches.extend({"prefix": prefix, "mapping": mapping, **hit} for hit in group["exact_matches"])
                continue
            best = -1
            best_count = 0
            best_examples = []
            exact = []
            configs = 0
            for pid, cipher in pages.items():
                for phase in range(len(key)):
                    for sign in (-1, 1):
                        configs += 1
                        decoded = decode_first12(cipher, key, phase, sign)
                        for opening in plan["openings"]:
                            length = prefix_len(decoded, opening["indices"])
                            if length > best:
                                best = length
                                best_count = 0
                                best_examples = []
                            if length == best:
                                best_count += 1
                                if len(best_examples) < 5:
                                    best_examples.append({"page": pid, "phase": phase, "sign": sign, "opening": opening["id"]})
                            if length == 12:
                                exact.append({"page": pid, "phase": phase, "sign": sign, "opening": opening["id"]})
            group = {"prefix": prefix, "mapping": mapping, "key_length": len(key),
                     "key_indices": key, "configurations": configs,
                     "opening_comparisons": configs * len(plan["openings"]),
                     "max_prefix": best, "max_prefix_ties": best_count,
                     "max_prefix_examples": best_examples, "exact_matches": exact}
            groups.append(group)
            computed[effective] = group
            full_matches.extend({"prefix": prefix, "mapping": mapping, **hit} for hit in exact)
    assert len(groups) == 11
    return {"schema": "liberpedia-grid-prefix-split-openings-results-v1",
            "plan_sha256": hashlib.sha256(plan_bytes).hexdigest(),
            "controls": controls,
            "group_count": len(groups),
            "configuration_count": sum(g["configurations"] for g in groups),
            "opening_comparison_count": sum(g["opening_comparisons"] for g in groups),
            "duplicates": "Group 4 hex-nibble values equal group 4 base-60 digit values; both named routes are reported but are one effective key.",
            "exact_matches": full_matches, "groups": groups}


def main():
    result = run()
    (HERE / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(result["configuration_count"], "configs;", result["opening_comparison_count"], "comparisons;", len(result["exact_matches"]), "matches")


if __name__ == "__main__":
    main()
