"""Section rune profiles and an equal-length 40--53 versus 54--55 control."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    lookup = {item["rune"]: i for i, item in enumerate(index["alphabet"])}
    if len(lookup) != 29:
        raise ValueError("Expected 29 runes")
    pages, inputs = {}, {"data/index.json": sha(ROOT / "data/index.json")}
    for number in range(56):
        rel = f"text/lp2-{number:02d}.txt"
        path = ROOT / rel
        source = path.read_text(encoding="utf-8")
        unknown = {c for c in source if "\u16a0" <= c <= "\u16ff"} - lookup.keys()
        if unknown:
            raise ValueError(f"Unknown rune in {rel}: {unknown}")
        pages[number] = [lookup[c] for c in source if c in lookup]
        inputs[rel] = sha(path)
    return plan, pages, inputs


def score(stream, same_page):
    n = len(stream)
    counts = Counter(stream)
    equal_pairs = sum(v * (v - 1) for v in counts.values())
    possible_pairs = n * (n - 1)
    edges = sum(same_page)
    doublets = sum(a == b for a, b, keep in zip(stream, stream[1:], same_page) if keep)
    return {"runes": n, "ioc_equal_ordered_pairs": equal_pairs,
            "ioc_all_ordered_pairs": possible_pairs,
            "ioc": equal_pairs / possible_pairs if possible_pairs else None,
            "within_page_edges": edges, "doublets": doublets,
            "doublet_rate": doublets / edges if edges else None}


def group(pages, first, last):
    labels = [number for number in range(first, last + 1) for _ in pages[number]]
    stream = [r for number in range(first, last + 1) for r in pages[number]]
    same_page = [a == b for a, b in zip(labels, labels[1:])]
    return stream, same_page


def percentile(values, percent):
    ordered = sorted(values)
    return ordered[round(percent * (len(ordered) - 1))]


def report():
    plan, pages, hashes = load()
    groups = []
    for first, last in plan["groups"]:
        stream, same_page = group(pages, first, last)
        groups.append({"pages": f"LP2-{first:02d}–{last:02d}", **score(stream, same_page)})
    earlier, edges = group(pages, 40, 53)
    ending, end_edges = group(pages, 54, 55)
    n = len(ending)
    assert n == 308 and len(earlier) == 3008
    windows = [score(earlier[i:i+n], edges[i:i+n-1]) for i in range(len(earlier)-n+1)]
    observed = score(ending, end_edges)
    return {"schema": "liberpedia-sectionwise-rune-profile-results-v1",
            "plan_sha256": sha(HERE / "plan.json"), "input_sha256": hashes,
            "groups": groups,
            "comparison": {"ending": observed, "reference_pages": "LP2-40–53",
                           "window_runes": n, "overlapping_windows": len(windows),
                           "ioc": {"min": min(w["ioc"] for w in windows),
                                   "median": percentile([w["ioc"] for w in windows], .5),
                                   "central_95": [percentile([w["ioc"] for w in windows], .025), percentile([w["ioc"] for w in windows], .975)],
                                   "windows_at_least_ending": sum(w["ioc"] >= observed["ioc"] for w in windows)},
                           "doublet_rate": {"min": min(w["doublet_rate"] for w in windows),
                                            "median": percentile([w["doublet_rate"] for w in windows], .5),
                                            "central_95": [percentile([w["doublet_rate"] for w in windows], .025), percentile([w["doublet_rate"] for w in windows], .975)],
                                            "windows_at_least_ending": sum(w["doublet_rate"] >= observed["doublet_rate"] for w in windows)},
                           "window_edge_range": [min(w["within_page_edges"] for w in windows), max(w["within_page_edges"] for w in windows)]}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    path = HERE / "results.json"
    if args.check:
        saved = json.loads(path.read_text(encoding="utf-8"))
        if result != saved:
            raise SystemExit("Saved result differs from recomputation")
        print("PASS sectionwise profile")
    else:
        path.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        print(json.dumps({"groups": result["groups"], "comparison": result["comparison"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
