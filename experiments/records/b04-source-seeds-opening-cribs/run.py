"""Bounded fixed-opening check over the pinned B-04 source keystream grid.

This asks a new, narrower question of source-defined candidates. The original
B-04 campaign scored English on LP2-00; it did not use these nine opening cribs.
"""

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
sys.path.insert(0, str(ROOT / "experiments" / "engines"))
from fixed_crib_skip import match_prefix  # noqa: E402


def load_source_ks():
    spec = importlib.util.spec_from_file_location("b04_pinned_ks", HERE / "source" / "ks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if len(module.GEN_NAMES) != 16 or len(module.RED_NAMES) != 5:
        raise RuntimeError("All 16 source generators and five reductions are required")
    return module


def inputs():
    page_manifest = json.loads((HERE / "page-inputs.json").read_text(encoding="utf-8"))
    for item in page_manifest["pages"]:
        if hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
            raise RuntimeError(f"Page transcription changed: {item['path']}")
    alphabet = {x["rune"]: x["index"] for x in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
    crib_manifest = json.loads((ROOT / "experiments/suites/feedback-opening-census/manifest.json").read_text(encoding="utf-8"))
    cribs = [(x["id"], tuple(x["indices"])) for x in crib_manifest["cribs"]]
    assert len(cribs) == 9 and all(len(indices) == 12 for _, indices in cribs)
    for item in crib_manifest["cribs"]:
        if hashlib.sha256((ROOT / item["source"]).read_bytes()).hexdigest() != item["sha256"]:
            raise RuntimeError(f"Reading CSV changed: {item['source']}")
    page_ids = list(crib_manifest["pages"])
    pages = []
    for page_id in page_ids:
        obj = json.loads((ROOT / "data/pages" / f"{page_id}.json").read_text(encoding="utf-8"))
        stream = tuple(alphabet[r] for r in obj["raw"] if r in alphabet)
        if not stream:
            raise RuntimeError(f"Unexpected empty page: {page_id}")
        pages.append((page_id, stream[:12]))
    assert len(pages) == 55
    seed_manifest = json.loads((HERE / "seed-manifest.json").read_text(encoding="utf-8"))
    if hashlib.sha256((HERE / "source/seeds.py").read_bytes()).hexdigest() != seed_manifest["source_seed_script_sha256"]:
        raise RuntimeError("Pinned source seed script changed")
    seeds = seed_manifest["entries"]
    assert len(seeds) == 2165
    return alphabet, crib_manifest, pages, cribs, seeds


def targets(pages, cribs):
    by_first = defaultdict(list)
    for atbash in (False, True):
        for page_id, source_cipher in pages:
            cipher = tuple((28 - c) % 29 for c in source_cipher) if atbash else source_cipher
            for crib_id, plain in cribs:
                for sign in (-1, 1):
                    key_first = ((plain[0] - cipher[0]) * sign) % 29
                    by_first[(atbash, sign, key_first)].append((page_id, crib_id, cipher, plain))
    return by_first


def run(seed_limit=None):
    ks = load_source_ks()
    _, crib_manifest, pages, cribs, seeds = inputs()
    if seed_limit is not None:
        seeds = seeds[:seed_limit]
    by_first = targets(pages, cribs)
    digest = hashlib.sha256()
    hist = Counter()
    group_hist = defaultdict(Counter)
    exact = []
    leading = []
    total = 0
    start = time.perf_counter()
    nsym = 728  # Pinned B-04 MAX_SKIP=3 and 120-rune stage-A text.
    for seed_i, entry in enumerate(seeds):
        seed = bytes.fromhex(entry["hex"])
        for generator in ks.GEN_NAMES:
            raw = ks.make_bytes(generator, seed, int(nsym * 1.35) + 256)
            for reduction in ks.RED_NAMES:
                base = ks.make_ks(generator, reduction, seed, nsym, raw=raw)
                for direction in ("forward", "reverse"):
                    key = base if direction == "forward" else base[::-1]
                    for sign in (-1, 1):
                        for atbash in (False, True):
                            best = 0
                            matches = []
                            for page_id, crib_id, cipher, plain in by_first[(atbash, sign, key[0])]:
                                length = match_prefix(cipher, plain, key, sign)
                                if length > best:
                                    best = length
                                if length == 12:
                                    matches.append([page_id, crib_id])
                            total += 1
                            hist[best] += 1
                            group_hist[f"{generator}/{reduction}"][best] += 1
                            if best >= 8 and len(leading) < 80:
                                leading.append({"seed_index": seed_i, "generator": generator,
                                                "reduction": reduction, "direction": direction,
                                                "sign": sign, "atbash": atbash, "prefix": best})
                            if matches:
                                exact.append({"seed_index": seed_i, "generator": generator,
                                              "reduction": reduction, "direction": direction,
                                              "sign": sign, "atbash": atbash, "matches": matches})
                            digest.update(f"{seed_i}\t{generator}\t{reduction}\t{direction}\t{sign}\t{int(atbash)}\t{best}\t{json.dumps(matches,separators=(',',':'))}\n".encode())
        if seed_i and seed_i % 100 == 0:
            print(f"{seed_i}/{len(seeds)} seeds; {total} configs; {time.perf_counter()-start:.1f}s", flush=True)
    result = {
        "schema": "b04-fixed-opening-cribs-v1", "source_commit": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
        "seed_count": len(seeds), "generator_count": len(ks.GEN_NAMES),
        "reduction_count": len(ks.RED_NAMES), "page_count": len(pages), "crib_count": len(cribs),
        "config_count": total, "exact_match_count": len(exact),
        "best_prefix_histogram": {str(k): hist[k] for k in sorted(hist)},
        "by_generator_reduction": {k: {str(i): c[i] for i in sorted(c)} for k, c in sorted(group_hist.items())},
        "exact_matches": exact, "long_prefix_examples": leading,
        "case_digest_sha256": digest.hexdigest(),
        "scope": "Nine fixed 12-rune known-reading opening cribs at each of 55 nonempty LP2-00–55 page starts (LP2-50 is blank); source B-04 zero-offset generators and key-skip rule. New check, not the original English-score sweep.",
        "cribs": crib_manifest["cribs"], "pages": [p for p, _ in pages],
    }
    return result, time.perf_counter() - start


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-limit", type=int, help="Timing sample only; does not replace full experiment")
    parser.add_argument("--output", type=Path, default=HERE / "results.json")
    args = parser.parse_args()
    result, elapsed = run(args.seed_limit)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{result['config_count']} configs in {elapsed:.2f}s, exact={result['exact_match_count']}, output={args.output}")


if __name__ == "__main__":
    main()
