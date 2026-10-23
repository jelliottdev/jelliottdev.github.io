"""Exact fixed-opening check over R21-L3's complete 45,975-word priority front.

The source's public English panel is unavailable, so this asks a new exact-crib
question using its actual seed order and four reducer/ABI configurations.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE / "source"))
sys.path.insert(0, str(ROOT / "experiments/engines"))
import gen_py27  # noqa: E402
from fixed_crib_skip import match_prefix  # noqa: E402

CONFIGS = (
    ("grb5_mod_i386", "grb5_mod", "i386"),
    ("grb5_rej_i386", "grb5_rej", "i386"),
    ("shuffle29_i386", "shuffle29", "i386"),
    ("random29_amd64", "random29", "amd64"),
)
KEY_LENGTH = 1 + 11 * 4  # 12 accepted runes, at most 3 rejected before each later one


def prior_words():
    prior = json.loads((HERE / "source/seedprior20.json").read_text(encoding="utf-8"))
    seen = set()
    ordered = []

    def add(value):
        value &= 0xFFFFFFFF
        if value not in seen:
            seen.add(value)
            ordered.append(value)

    for row in prior["order"]:
        add(int(row["seed"]))
    for row in prior["order"][:64]:
        seed = int(row["seed"])
        for delta in range(-512, 513):
            add(seed + delta)
    assert len(prior["order"]) == 433 and len(ordered) == 45975
    assert hashlib.sha256("".join(f"{w}\n" for w in ordered).encode()).hexdigest() == "061eb4dc5c72d4623d9350358bbbb8e545194602c39d0c5d98109c23f31772f3"
    return ordered


def source_key(word, mode, mapname):
    if mapname == "amd64":
        n64 = (word * 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        seed_words = [n64 & 0xFFFFFFFF, (n64 >> 32) & 0xFFFFFFFF]
    else:
        seed_words = [word] if word else [0]
    rng = gen_py27.MT19937()
    rng.init_by_array(seed_words)
    key = gen_py27.REDUCERS[mode](rng, KEY_LENGTH)
    assert len(key) == KEY_LENGTH and all(0 <= k < 29 for k in key)
    return key


def targets():
    manifest = json.loads((ROOT / "experiments/suites/feedback-opening-census/manifest.json").read_text(encoding="utf-8"))
    alphabet = {a["rune"]: a["index"] for a in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
    cribs = [(c["id"], tuple(c["indices"])) for c in manifest["cribs"]]
    assert len(cribs) == 9 and all(len(p) == 12 for _, p in cribs)
    lookup = defaultdict(list)
    pages = []
    for page_id in manifest["pages"]:
        raw = json.loads((ROOT / "data/pages" / f"{page_id}.json").read_text(encoding="utf-8"))["raw"]
        cipher = tuple(alphabet[r] for r in raw if r in alphabet)[:12]
        if not cipher:
            continue
        pages.append(page_id)
        for crib_id, plain in cribs:
            lookup[(cipher[0] - plain[0]) % 29].append((page_id, crib_id, cipher, plain))
    assert len(pages) == 55
    return lookup, pages, manifest["cribs"]


def run(word_limit=None):
    words = prior_words()
    if word_limit is not None:
        words = words[:word_limit]
    lookup, pages, cribs = targets()
    hist = Counter()
    per_config = defaultdict(Counter)
    full_matches = []
    leading = []
    unique_keys = set()
    digest = hashlib.sha256()
    start = time.perf_counter()
    rows = 0
    for name, mode, mapname in CONFIGS:
        for index, word in enumerate(words):
            key = source_key(word, mode, mapname)
            unique_keys.add(bytes(key))
            best = 0
            matches = []
            for page_id, crib_id, cipher, plain in lookup[key[0]]:
                length = match_prefix(cipher, plain, key, -1, max_skip=3)
                best = max(best, length)
                if length == 12:
                    matches.append([page_id, crib_id])
            rows += 1
            hist[best] += 1
            per_config[name][best] += 1
            if matches:
                full_matches.append({"config": name, "word_index": index, "word": word,
                                     "matches": matches})
            if best >= 7 and len(leading) < 100:
                leading.append({"config": name, "word_index": index, "word": word,
                                "prefix": best})
            digest.update((json.dumps([name, index, word, best, matches], separators=(",", ":")) + "\n").encode())
        print(name, len(words), "words in", f"{time.perf_counter()-start:.1f}s", flush=True)
    return {
        "schema": "py27-l3-prior-fixed-openings-v1",
        "source_commit": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
        "word_count": len(words), "config_count": len(CONFIGS), "rows": rows,
        "distinct_first_45_symbol_streams": len(unique_keys),
        "pages": pages, "cribs": cribs, "key_prefix_length": KEY_LENGTH,
        "best_prefix_histogram": {str(k): hist[k] for k in sorted(hist)},
        "per_config": {c: {str(k): v[k] for k in sorted(v)} for c, v in per_config.items()},
        "exact_matches": full_matches, "long_prefix_examples": leading,
        "case_digest_sha256": digest.hexdigest(),
        "scope": "R21-L3 full 45,975-word prior front and four exact reducer/ABI maps; nine fixed 12-rune readings at 55 LP2 page starts, source sign -1, keyskip1 max3, no Atbash or English panel.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--word-limit", type=int, help="Benchmark only; not a full result")
    parser.add_argument("--output", type=Path, default=HERE / "results.json")
    args = parser.parse_args()
    result = run(args.word_limit)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8", newline="\n")
    print("Rows", result["rows"], "exact", len(result["exact_matches"]))


if __name__ == "__main__":
    main()
