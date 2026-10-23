"""Replay the finite shared-key premises in three archived Wulfic scripts.

The script deliberately does not run the crib scorer when its asserted paired
positions do not exist or are not identical. Its pairwise IoC screen is a
separate, retrospective source component.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
INDEX = {r: i for i, r in enumerate(RUNES)}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(plan: dict) -> dict[int, list[int]]:
    for row in plan["inputs"]:
        assert digest(ROOT / row["path"]) == row["sha256"], row["path"]
    witness = json.loads((ROOT / plan["inputs"][0]["path"]).read_text(encoding="utf-8"))
    out = {}
    for scan in range(21, 55):
        lp2 = scan - 17
        text = (ROOT / f"text/lp2-{lp2:02}.txt").read_text(encoding="utf-8")
        letters = "".join(ch for ch in text if ch in INDEX)
        entry = witness["pages"][f"lp2-{lp2:02}"]
        assert entry["legacy_page"] == scan
        assert entry["runes"] == len(letters)
        assert entry["source_gp_sha256"] == hashlib.sha256(letters.encode("utf-8")).hexdigest()
        out[scan] = [INDEX[ch] for ch in letters]
    return out


def overlap(a: list[int], b: list[int], n: int) -> dict:
    n_actual = min(n, len(a), len(b))
    matches = sum(a[i] == b[i] for i in range(n_actual))
    first_difference = next((i for i in range(n_actual) if a[i] != b[i]), None)
    return {"requested_length": n, "compared_length": n_actual,
            "in_bounds": len(a) >= n and len(b) >= n,
            "equal_runes": matches, "first_difference": first_difference,
            "identical": n_actual == n and matches == n}


def ioc(values: list[int]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    freq = Counter(values)
    return 29 * sum(v * (v - 1) for v in freq.values()) / (n * (n - 1))


def screen(pages: dict[int, list[int]]) -> dict:
    seen = 0
    hits = []
    maximum = (0.0, None, None, None, None)
    numbers = sorted(pages)
    for ai, left in enumerate(numbers):
        a = pages[left]
        for right in numbers[ai + 1:]:
            b = pages[right]
            n = min(len(a), len(b))
            if n < 50:
                continue
            for sign, name in ((-1, "difference"), (1, "sum")):
                value = ioc([(a[k] + sign * b[k]) % 29 for k in range(n)])
                seen += 1
                row = (value, left, right, name, n)
                if value > maximum[0]:
                    maximum = row
                if value > 1.15:
                    hits.append(row)
    hits.sort(reverse=True)
    def row(item):
        value, a, b, mode, n = item
        return {"ioc": value, "scan_a": a, "scan_b": b,
                "page_a": f"lp2-{a-17:02}", "page_b": f"lp2-{b-17:02}",
                "operation": mode, "runes": n}
    return {"cases": seen, "hits_over_1_15": len(hits),
            "maximum": row(maximum), "hits": [row(item) for item in hits]}


def execute() -> dict:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    pages = load(plan)
    flat = [v for scan in range(21, 55) for v in pages[scan]]
    regions = []
    for source, target, length in plan["premise_checks"]["paired_regions"]:
        measured = overlap(flat[source:source+length], flat[target:target+length], length)
        regions.append({"source": source, "target": target, **measured})
    prefix = overlap(pages[27], pages[44], len(pages[27]))
    lp27 = [INDEX[ch] for ch in (ROOT / "text/lp2-27.txt").read_text(encoding="utf-8") if ch in INDEX]
    lp44 = [INDEX[ch] for ch in (ROOT / "text/lp2-44.txt").read_text(encoding="utf-8") if ch in INDEX]
    alternative_prefix = overlap(lp27, lp44, len(lp27))
    period = plan["premise_checks"]["period"]
    max_period_index = 2 * period - 1
    original_screen = screen(pages)

    rng = random.Random(plan["pair_screen"]["null"]["seed"])
    null = []
    for _ in range(plan["pair_screen"]["null"]["replicates"]):
        shuffled = {k: v.copy() for k, v in pages.items()}
        for seq in shuffled.values():
            rng.shuffle(seq)
        result = screen(shuffled)
        null.append({"maximum_ioc": result["maximum"]["ioc"],
                     "hits_over_1_15": result["hits_over_1_15"]})

    plain = []
    for num in range(10, 14):
        page = json.loads((ROOT / f"data/pages/lp1-{num:02}.json").read_text(encoding="utf-8"))
        assert page["reading"]["method"] == "direct"
        plain.extend(INDEX[ch] for ch in page["raw"] if ch in INDEX)
    length = plan["pair_screen"]["positive_control"]["window_length"]
    windows = [plain[k*length:(k+1)*length] for k in range(5)]
    assert all(len(w) == length for w in windows)
    key_rng = random.Random(3301)
    common_key = [key_rng.randrange(29) for _ in range(length)]
    independent_keys = [[key_rng.randrange(29) for _ in range(length)] for _ in windows]
    common_cipher = [[(v + common_key[i]) % 29 for i, v in enumerate(w)] for w in windows]
    distinct_cipher = [[(v + independent_keys[j][i]) % 29 for i, v in enumerate(w)] for j, w in enumerate(windows)]
    plants = []
    for a in range(5):
        for b in range(a + 1, 5):
            shared = ioc([(common_cipher[a][k] - common_cipher[b][k]) % 29 for k in range(length)])
            independent = ioc([(distinct_cipher[a][k] - distinct_cipher[b][k]) % 29 for k in range(length)])
            assert shared == ioc([(windows[a][k] - windows[b][k]) % 29 for k in range(length)])
            plants.append({"window_a": a, "window_b": b,
                           "same_key_difference_ioc": shared,
                           "independent_key_difference_ioc": independent,
                           "same_key_crosses_source_screen": shared > 1.15})
    observed = original_screen["maximum"]["ioc"]
    return {
        "schema": "liberpedia-wulfic-two-time-pad-premise-results-v1",
        "plan_sha256": digest(HERE / "plan.json"),
        "source_page_count": len(pages), "source_stream_runes": len(flat),
        "period": {"value": period, "largest_index_required": max_period_index,
                   "in_bounds": len(flat) > max_period_index},
        "source_prefix": {"scan_a": 27, "scan_b": 44,
                          "lp2_a": "lp2-10", "lp2_b": "lp2-27",
                          "length_a": len(pages[27]), "length_b": len(pages[44]), **prefix},
        "alternative_label_prefix": {"lp2_a": "lp2-27", "lp2_b": "lp2-44",
                                     "length_a": len(lp27), "length_b": len(lp44), **alternative_prefix},
        "paired_regions": regions,
        "pair_screen": original_screen,
        "null": {"replicates": len(null), "seed": plan["pair_screen"]["null"]["seed"],
                 "maximum_ioc": [x["maximum_ioc"] for x in null],
                 "hits_over_1_15": [x["hits_over_1_15"] for x in null],
                 "maxima_at_least_observed": sum(x["maximum_ioc"] >= observed for x in null)},
        "plants": plants,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = execute()
    path = HERE / "results.json"
    if args.check:
        assert result == json.loads(path.read_text(encoding="utf-8"))
        print("PASS: premise, 1,122 pair screens, 199 complete null searches and 10 plants")
    else:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"Saved {path}")


if __name__ == "__main__":
    main()
