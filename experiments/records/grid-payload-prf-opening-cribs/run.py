"""Fixed-opening check of the complete pinned B-05 PRF candidate grid."""

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PARENT = HERE.parent / "grid-payload-prf-source-grid"
sys.path.insert(0, str(ROOT / "experiments/engines"))
from fixed_crib_skip import match_prefix  # noqa: E402


def source_grid():
    spec = importlib.util.spec_from_file_location("b05_source_grid", PARENT / "dedup_engine.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows, keys = module.enumerate_cases()
    module.seeded_scores(rows)  # Recheck the separately saved 3,840 Part 2a rows.
    return rows, keys


def inputs():
    page_manifest = json.loads((HERE / "page-inputs.json").read_text(encoding="utf-8"))
    for item in page_manifest["pages"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    alphabet = {x["rune"]: x["index"] for x in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
    crib_manifest = json.loads((ROOT / "experiments/suites/feedback-opening-census/manifest.json").read_text(encoding="utf-8"))
    assert len(crib_manifest["pages"]) == 55 and len(crib_manifest["cribs"]) == 9
    for crib in crib_manifest["cribs"]:
        assert hashlib.sha256((ROOT / crib["source"]).read_bytes()).hexdigest() == crib["sha256"]
    pages = []
    for page_id in crib_manifest["pages"]:
        raw = json.loads((ROOT / f"data/pages/{page_id}.json").read_text(encoding="utf-8"))["raw"]
        pages.append((page_id, tuple(alphabet[c] for c in raw if c in alphabet)[:12]))
    return pages, crib_manifest["cribs"]


def run():
    rows, keys = source_grid()
    assert len(rows) == 70680 and len(keys) == 59948
    # Verify every effective key hash/parameter row against the prior complete
    # source-grid receipt. This protects reverse/full-length and offset rules.
    receipt = PARENT / "cases.jsonl"
    with receipt.open(encoding="utf-8") as handle:
        for index, row in enumerate(rows):
            if row["part"] == "part2a":
                continue  # Saved in the earlier contested-mask record, not this JSONL.
            published = json.loads(next(handle))
            assert all(published[k] == v for k, v in row.items()), index
        assert not handle.read(1)
    pages, cribs = inputs()
    bucket = defaultdict(list)
    for page_id, cipher in pages:
        for crib in cribs:
            plain = tuple(crib["indices"])
            bucket[(plain[0] - cipher[0]) % 29].append((page_id, crib["id"], cipher, plain))
    unique = {}
    start = time.perf_counter()
    for digest, effective in keys.items():
        best, hits = 0, []
        for page_id, crib_id, cipher, plain in bucket[effective[0]]:
            length = match_prefix(cipher, plain, effective, sign=1, max_skip=3)
            best = max(best, length)
            if length == 12:
                hits.append([page_id, crib_id])
        unique[digest] = (best, hits)
    hist, part_hist = Counter(), defaultdict(Counter)
    exact, leaders = [], []
    case_digest = hashlib.sha256()
    for case_index, row in enumerate(rows):
        best, hits = unique[row["effective_key_sha256"]]
        hist[best] += 1
        part_hist[row["part"]][best] += 1
        if hits:
            exact.append({"case_index": case_index, "parameters": row, "matches": hits})
        if best >= 8 and len(leaders) < 80:
            leaders.append({"case_index": case_index, "parameters": row, "prefix": best})
        case_digest.update(f"{case_index}\t{row['effective_key_sha256']}\t{best}\t{json.dumps(hits,separators=(',',':'))}\n".encode())
    result = {
        "schema": "b05-source-grid-fixed-openings-v1",
        "source_commit": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
        "source_config_count": len(rows), "unique_effective_keys": len(keys),
        "page_count": len(pages), "crib_count": len(cribs),
        "exact_match_count": len(exact),
        "best_prefix_histogram": {str(k): hist[k] for k in sorted(hist)},
        "by_source_part": {p: {str(k): c[k] for k in sorted(c)} for p, c in sorted(part_hist.items())},
        "unique_key_prefix_histogram": {str(k): v for k, v in sorted(Counter(x[0] for x in unique.values()).items())},
        "exact_matches": exact, "long_prefix_examples": leaders,
        "case_digest_sha256": case_digest.hexdigest(),
        "prior_case_receipt_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
        "pages": [p for p, _ in pages], "cribs": cribs,
        "scope": "Exact structural feasibility of nine fixed 12-rune known-reading openings at 55 nonempty LP2-00–55 page starts under all 70,680 pinned B-05 source configurations, with up to three rejected key symbols. Separate from original English-beam scoring.",
    }
    return result, time.perf_counter() - start


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "results.json")
    args = parser.parse_args()
    result, seconds = run()
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{result['source_config_count']} source cases, {result['unique_effective_keys']} unique keys; {result['exact_match_count']} full openings; check {seconds:.2f}s after key enumeration")


if __name__ == "__main__":
    main()
