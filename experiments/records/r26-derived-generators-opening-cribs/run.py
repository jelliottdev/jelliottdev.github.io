"""Check R26-A's exact generator/seed grid against fixed LP2 opening cribs.

This is a new acceptance test, not a replay of the source's language panel.
The generator implementations and ordered seed manifest are preserved in source/.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "engines"))
sys.path.insert(0, str(HERE / "source"))
from fixed_crib_skip import match_prefix  # noqa: E402
import gen_perl  # noqa: E402
import gen_py27  # noqa: E402
import gen_tex  # noqa: E402

N = 29
PREFIX = 12
KEY_LENGTH = 1 + (PREFIX - 1) * (8 + 1)
PRESETS = (("exact", 3, "single"), ("pair", 8, "pair"))


def load_inputs():
    manifest = json.loads((HERE / "seed-manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["dictionary"]) == 347
    assert manifest["dense_baseline"] == list(range(400))
    assert manifest["perl_reductions"] == ["r29", "r29_nodup", "r32_rej", "r256_mod", "r2p32_mod", "r26_lat", "raw48_mod", "lrand48_mod"]
    assert manifest["tex_generators"] == ["pgf_rnd29", "lcg_mod29", "randomtex_div29", "pdftex_u29"]
    assert manifest["py27_modes"] == ["grb5_mod", "grb5_rej", "shuffle29"]
    alphabet = {a["rune"]: a["index"] for a in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
    crib_manifest = json.loads((ROOT / "experiments/suites/feedback-opening-census/manifest.json").read_text(encoding="utf-8"))
    cribs = [(c["id"], tuple(c["indices"])) for c in crib_manifest["cribs"]]
    assert len(cribs) == 9 and all(len(p) == PREFIX for _, p in cribs)
    pages = []
    for page_id in crib_manifest["pages"]:
        page = json.loads((ROOT / "data/pages" / f"{page_id}.json").read_text(encoding="utf-8"))
        cipher = tuple(alphabet[r] for r in page["raw"] if r in alphabet)
        if cipher:
            pages.append((page_id, cipher[:PREFIX]))
    assert len(pages) == 55
    return manifest, crib_manifest, cribs, pages


def candidate_keys(manifest):
    """Preserve R26-A's order and integer-only Perl/TeX branches."""
    groups = (("prior_dense", manifest["dictionary"]),
              ("dense_baseline", [{"value": n, "type": "int", "kind": "dense0"} for n in manifest["dense_baseline"]]))
    for axis, entries in groups:
        for entry in entries:
            seed = entry["value"]
            tag = {"axis": axis, "seed": seed, "seed_type": entry["type"], "kind": entry["kind"]}
            if entry["type"] == "int":
                for reduction in manifest["perl_reductions"]:
                    yield {**tag, "generator": "perl", "variant": reduction, "offset": 0}, gen_perl.make_ks(reduction, seed, KEY_LENGTH)
                for generator in manifest["tex_generators"]:
                    yield {**tag, "generator": "tex", "variant": generator, "offset": 0}, gen_tex.make_ks(generator, seed, KEY_LENGTH)
            for mode in manifest["py27_modes"]:
                for offset in manifest["py27_offsets"]:
                    key = gen_py27.keystream(seed, mode, KEY_LENGTH,
                                             wordsize=manifest["py27_wordsize"],
                                             jump=None if offset == 0 else offset)
                    yield {**tag, "generator": "py27", "variant": mode, "offset": offset}, key


def run():
    manifest, crib_manifest, cribs, pages = load_inputs()
    by_key0 = defaultdict(list)
    for page_id, cipher in pages:
        for crib_id, plain in cribs:
            required = (cipher[0] - plain[0]) % N  # sign=-1: P0=C0-K0
            by_key0[required].append((page_id, crib_id, cipher, plain))

    hist = Counter()
    by_generator = defaultdict(Counter)
    exact = []
    leading = []
    digest = hashlib.sha256()
    key_count = 0
    unique_key_prefixes = set()
    row_count = 0
    start = time.perf_counter()
    for meta, key in candidate_keys(manifest):
        assert len(key) >= KEY_LENGTH and all(0 <= k < N for k in key)
        key_count += 1
        unique_key_prefixes.add(bytes(key[:KEY_LENGTH]))
        targets = by_key0[key[0]]
        for preset, max_skip, skip_mode in PRESETS:
            best = 0
            matches = []
            for page_id, crib_id, cipher, plain in targets:
                length = match_prefix(cipher, plain, key, -1, max_skip=max_skip,
                                      skip_mode=skip_mode)
                if length > best:
                    best = length
                if length == PREFIX:
                    matches.append([page_id, crib_id])
            row_count += 1
            hist[best] += 1
            by_generator[f'{meta["generator"]}/{meta["variant"]}/{preset}'][best] += 1
            if matches:
                exact.append({**meta, "preset": preset, "matches": matches})
            if best >= 7 and len(leading) < 100:
                leading.append({**meta, "preset": preset, "prefix": best})
            digest.update((json.dumps([meta, preset, best, matches], ensure_ascii=False,
                                      separators=(",", ":")) + "\n").encode("utf-8"))
        if key_count % 2000 == 0:
            print(f"{key_count} keys / {row_count} rows in {time.perf_counter()-start:.1f}s", flush=True)
    assert key_count == 24231 and row_count == 48462
    return {
        "schema": "r26-derived-generators-fixed-openings-v1",
        "source_commit": manifest["source_commit"],
        "source_grid_planned_rows": 49302,
        "actual_key_count": key_count,
        "unique_first_100_symbol_streams": len(unique_key_prefixes),
        "actual_preset_rows": row_count,
        "page_count": len(pages), "crib_count": len(cribs),
        "potential_exact_comparisons": row_count * len(pages) * len(cribs),
        "screened_by_first_symbol": True,
        "key_prefix_length": KEY_LENGTH,
        "best_prefix_histogram": {str(k): hist[k] for k in sorted(hist)},
        "by_generator_variant_preset": {k: {str(i): v[i] for i in sorted(v)}
                                        for k, v in sorted(by_generator.items())},
        "exact_matches": exact, "long_prefix_examples": leading,
        "case_digest_sha256": digest.hexdigest(),
        "pages": [p for p, _ in pages], "cribs": crib_manifest["cribs"],
        "scope": "R26-A ordered generator/seed grid, source sign -1, no Atbash, exact (single-skip max 3) and pair (pair-skip max 8), fixed nine 12-rune openings at the start of 55 LP2 pages. New bounded criterion; not the source language panel.",
    }


def main():
    out = run()
    (HERE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8", newline="\n")
    print("R26-A fixed-opening rows:", out["actual_preset_rows"],
          "exact:", len(out["exact_matches"]))


if __name__ == "__main__":
    main()
