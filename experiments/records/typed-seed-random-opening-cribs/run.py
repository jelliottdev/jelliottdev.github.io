"""Fixed-reading opening check of the pinned typed-seed Python Random grid."""

import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "engines"))
from fixed_crib_skip import match_prefix  # noqa: E402


def source_grid():
    """Execute only the source's literal seed, date-loop and stream definitions."""
    original = (HERE / "source/string_seeds.py").read_text(encoding="utf-8")
    nodes = ast.parse(original).body
    selected = []
    names = {"N", "WORDS", "NUMS", "MODES"}
    for node in nodes:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets):
            selected.append(node)
        elif isinstance(node, ast.For) and isinstance(node.target, ast.Name) and node.target.id == "y":
            selected.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == "stream":
            selected.append(node)
    assert len(selected) == 6
    env = {"random": random}
    exec(compile(ast.Module(body=selected, type_ignores=[]), "pinned-string-seeds", "exec"), env)
    candidates = []
    for word in env["WORDS"]:
        candidates.extend((word, word.encode()))
    candidates.extend(env["NUMS"])
    candidates.extend(float(x) for x in (3301, 1033, 3.301))
    assert len(candidates) == 1284 and len(env["MODES"]) == 6
    return env["stream"], tuple(env["MODES"]), candidates


def masked_opening(stream, mask, count=12):
    """Copy source decode()'s first-two-F interrupter decision rule."""
    output, fi = [], 0
    for cipher in stream:
        if cipher == 0 and fi < 2:
            skip = (mask >> fi) & 1
            fi += 1
            if skip:
                continue
        output.append(cipher)
        if len(output) == count:
            return tuple(output)
    raise ValueError("Page too short after interrupter choices")


def inputs():
    manifest = json.loads((HERE / "page-inputs.json").read_text(encoding="utf-8"))
    for entry in manifest["pages"]:
        assert hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
    alphabet = {x["rune"]: x["index"] for x in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
    crib_manifest = json.loads((ROOT / "experiments/suites/feedback-opening-census/manifest.json").read_text(encoding="utf-8"))
    assert len(crib_manifest["pages"]) == 55 and len(crib_manifest["cribs"]) == 9
    for crib in crib_manifest["cribs"]:
        assert hashlib.sha256((ROOT / crib["source"]).read_bytes()).hexdigest() == crib["sha256"]
    pages = []
    for page_id in crib_manifest["pages"]:
        raw = json.loads((ROOT / f"data/pages/{page_id}.json").read_text(encoding="utf-8"))["raw"]
        pages.append((page_id, tuple(alphabet[c] for c in raw if c in alphabet)))
    return pages, crib_manifest["cribs"]


def target_index(pages, cribs):
    bucket = defaultdict(list)
    for mask in range(4):
        for page_id, page in pages:
            cipher = masked_opening(page, mask)
            for crib in cribs:
                plain = tuple(crib["indices"])
                for sign in (-1, 1):
                    first_key = ((plain[0] - cipher[0]) * sign) % 29
                    bucket[(mask, sign, first_key)].append((page_id, crib["id"], cipher, plain))
    return bucket


def run(seed_limit=None):
    stream, modes, candidates = source_grid()
    pages, cribs = inputs()
    bucket = target_index(pages, cribs)
    if seed_limit is not None:
        candidates = candidates[:seed_limit]
    hist, by_mode = Counter(), defaultdict(Counter)
    digest = hashlib.sha256()
    exact = []
    start = time.perf_counter()
    for seed_i, seed in enumerate(candidates):
        for mode in modes:
            key = stream(seed, mode, n=260)
            for sign in (-1, 1):
                for mask in range(4):
                    best, hits = 0, []
                    for page_id, crib_id, cipher, plain in bucket[(mask, sign, key[0])]:
                        length = match_prefix(cipher, plain, key, sign, max_skip=0)
                        best = max(best, length)
                        if length == 12:
                            hits.append([page_id, crib_id])
                    hist[best] += 1
                    by_mode[mode][best] += 1
                    if hits:
                        exact.append({"seed_index": seed_i, "mode": mode, "sign": sign, "mask": mask, "matches": hits})
                    digest.update(f"{seed_i}\t{mode}\t{sign}\t{mask}\t{best}\t{json.dumps(hits,separators=(',',':'))}\n".encode())
    result = {
        "schema": "typed-seed-random-openings-v1",
        "source_commit": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
        "source_script_sha256": hashlib.sha256((HERE / "source/string_seeds.py").read_bytes()).hexdigest(),
        "python_random_version": "CPython 3.12 Random.seed(version=2 default)",
        "seed_count": len(candidates), "seed_types": dict(Counter(type(c).__name__ for c in candidates)),
        "mode_count": len(modes), "source_config_count": len(candidates) * len(modes) * 2,
        "interrupter_masks_per_config": 4, "path_count": sum(hist.values()),
        "page_count": len(pages), "crib_count": len(cribs), "exact_match_count": len(exact),
        "best_prefix_histogram": {str(k): hist[k] for k in sorted(hist)},
        "by_stream_mode": {name: {str(k): c[k] for k in sorted(c)} for name, c in sorted(by_mode.items())},
        "exact_matches": exact, "case_digest_sha256": digest.hexdigest(),
        "pages": [name for name, _ in pages], "cribs": cribs,
        "scope": "Source typed seeds and six CPython Random modes, both decode signs, four first-two-F interrupter masks, fixed nine 12-rune openings at 55 nonempty LP2-00–55 page starts; no English scoring.",
    }
    return result, time.perf_counter() - start


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed-limit", type=int, help="Timing/control sample only")
    p.add_argument("--output", type=Path, default=HERE / "results.json")
    args = p.parse_args()
    result, elapsed = run(args.seed_limit)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{result['source_config_count']} source configs × 4 F masks = {result['path_count']} paths in {elapsed:.2f}s; exact={result['exact_match_count']}")


if __name__ == "__main__":
    main()
