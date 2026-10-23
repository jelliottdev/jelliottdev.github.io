"""Independent full-grid check of the fixed-opening R26-A adapter.

This does not import the shared skip matcher or the producer. It uses a
separate, exhaustive path-state implementation, rebuilds the grid, and checks controls.
"""

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE / "source"))
import gen_perl  # noqa: E402
import gen_py27  # noqa: E402
import gen_tex  # noqa: E402


def prefix_oracle(cipher, plain, key, pair):
    """Existential DFS under the source's collision constraint; sign is -1."""
    assert len(cipher) == len(plain) and cipher
    if (cipher[0] - key[0]) % 29 != plain[0]:
        return 0
    limit = 8 if pair else 3
    positions = {0}
    for at in range(1, len(plain)):
        following = set()
        for previous_key in positions:
            for rejected_count in range(0, limit + 1, 2 if pair else 1):
                accepted = previous_key + rejected_count + 1
                if accepted >= len(key):
                    continue
                if (cipher[at] - key[accepted]) % 29 != plain[at]:
                    continue
                rejected = range(previous_key + 1, accepted, 2 if pair else 1)
                if all((plain[at] + key[j]) % 29 == cipher[at - 1] for j in rejected):
                    following.add(accepted)
        if not following:
            return at
        positions = following
    return len(plain)


def brute_prefix(cipher, plain, key, pair):
    """Tiny-case tree oracle without position-set aggregation."""
    if (cipher[0] - key[0]) % 29 != plain[0]:
        return 0

    def rec(at, previous_key):
        if at == len(plain):
            return at
        longest = at
        for rejected_count in range(0, (8 if pair else 3) + 1,
                                    2 if pair else 1):
            accepted = previous_key + rejected_count + 1
            if accepted >= len(key):
                continue
            if (cipher[at] - key[accepted]) % 29 != plain[at]:
                continue
            rejected = range(previous_key + 1, accepted, 2 if pair else 1)
            if all((plain[at] + key[j]) % 29 == cipher[at - 1] for j in rejected):
                longest = max(longest, rec(at + 1, accepted))
        return longest

    return rec(1, 0)


def generators(manifest):
    for axis, entries in (("prior_dense", manifest["dictionary"]),
                          ("dense_baseline", [{"value": i, "type": "int", "kind": "dense0"}
                                               for i in manifest["dense_baseline"]])):
        for entry in entries:
            seed = entry["value"]
            meta = dict(axis=axis, seed=seed, seed_type=entry["type"], kind=entry["kind"])
            if entry["type"] == "int":
                for red in manifest["perl_reductions"]:
                    yield dict(**meta, generator="perl", variant=red, offset=0), gen_perl.make_ks(red, seed, 100)
                for gen in manifest["tex_generators"]:
                    yield dict(**meta, generator="tex", variant=gen, offset=0), gen_tex.make_ks(gen, seed, 100)
            for mode in manifest["py27_modes"]:
                for offset in manifest["py27_offsets"]:
                    yield dict(**meta, generator="py27", variant=mode, offset=offset), gen_py27.keystream(
                        seed, mode, 100, wordsize=64, jump=None if offset == 0 else offset)


def check_controls():
    # Standalone arithmetic oracle for Perl r29 and lcg_mod29.
    x = (3301 << 16) | 0x330E
    perl = []
    for _ in range(20):
        x = (x * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
        perl.append((29 * x) >> 48)
    assert perl == gen_perl.make_ks("r29", 3301, 20)
    state = 3301
    tex = []
    for _ in range(20):
        state = (state * 16807) % 2147483647
        tex.append(state % 29)
    assert tex == gen_tex.make_ks("lcg_mod29", 3301, 20)
    # Source vector was captured from real CPython 2.7.3 and 2.7.18.
    py27 = [1, 28, 18, 23, 2, 25, 24, 10, 10, 25, 2, 21, 12, 16, 11, 20]
    assert py27 == gen_py27.keystream("CICADA3301", "grb5_rej", 16, wordsize=64)
    plain = [24, 7, 24, 4, 9, 21, 17, 18, 4, 7, 0, 10]
    for key in (gen_perl.make_ks("r29", 3301, 100),
                gen_tex.make_ks("pgf_rnd29", 3301, 100),
                gen_py27.keystream("CICADA3301", "grb5_mod", 100, wordsize=64)):
        cipher = [(p + k) % 29 for p, k in zip(plain, key)]
        assert prefix_oracle(cipher, plain, key, pair=False) == 12
        assert prefix_oracle(cipher, plain, key, pair=True) == 12
    # Forced single- and pair-skip paths, including a rejected first key.
    for pair in (False, True):
        key = [5, (plain[0] + 5 - plain[1]) % 29]
        if pair:
            key.append(8)  # second rejected key is unconstrained
        key.append((key[1] + 1) % 29)
        key.extend([7] * 20)
        cipher = [(plain[0] + key[0]) % 29,
                  (plain[1] + key[3 if pair else 2]) % 29]
        cipher.extend((p + 7) % 29 for p in plain[2:])
        assert prefix_oracle(cipher, plain, key, pair=pair) == 12
    rng = random.Random(3301)
    for pair in (False, True):
        for _ in range(200):
            short_plain = [rng.randrange(29) for _ in range(4)]
            short_key = [rng.randrange(29) for _ in range(28)]
            short_cipher = [rng.randrange(29) for _ in range(4)]
            short_cipher[0] = (short_plain[0] + short_key[0]) % 29
            assert prefix_oracle(short_cipher, short_plain, short_key, pair) == brute_prefix(
                short_cipher, short_plain, short_key, pair)


def check():
    check_controls()
    manifest = json.loads((HERE / "seed-manifest.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((HERE / "source/sweep.py").read_bytes()).hexdigest() == manifest["source_sweep_sha256"]
    assert len(manifest["dictionary"]) == 347
    assert sum(e["type"] == "str" for e in manifest["dictionary"]) == 35
    alphabet = {e["rune"]: e["index"] for e in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
    cribs = [(c["id"], tuple(c["indices"])) for c in result["cribs"]]
    targets = defaultdict(list)
    for page_id in result["pages"]:
        text = json.loads((ROOT / "data/pages" / f"{page_id}.json").read_text(encoding="utf-8"))["raw"]
        cipher = tuple(alphabet[r] for r in text if r in alphabet)[:12]
        for crib_id, plain in cribs:
            targets[(cipher[0] - plain[0]) % 29].append((page_id, crib_id, cipher, plain))
    assert len(result["pages"]) == 55 and len(cribs) == 9

    hist = Counter()
    groups = defaultdict(Counter)
    exact = []
    leaders = []
    dig = hashlib.sha256()
    key_count = 0
    unique_key_prefixes = set()
    for meta, key in generators(manifest):
        key_count += 1
        unique_key_prefixes.add(bytes(key[:100]))
        for preset, pair in (("exact", False), ("pair", True)):
            best = 0
            matches = []
            for page_id, crib_id, cipher, plain in targets[key[0]]:
                length = prefix_oracle(cipher, plain, key, pair)
                best = max(best, length)
                if length == 12:
                    matches.append([page_id, crib_id])
            hist[best] += 1
            groups[f'{meta["generator"]}/{meta["variant"]}/{preset}'][best] += 1
            if matches:
                exact.append({**meta, "preset": preset, "matches": matches})
            if best >= 7 and len(leaders) < 100:
                leaders.append({**meta, "preset": preset, "prefix": best})
            dig.update((json.dumps([meta, preset, best, matches], ensure_ascii=False,
                                   separators=(",", ":")) + "\n").encode("utf-8"))
    assert key_count == result["actual_key_count"] == 24231
    assert len(unique_key_prefixes) == result["unique_first_100_symbol_streams"] == 19986
    assert sum(hist.values()) == result["actual_preset_rows"] == 48462
    assert {str(k): hist[k] for k in sorted(hist)} == result["best_prefix_histogram"]
    assert {k: {str(i): c[i] for i in sorted(c)} for k, c in sorted(groups.items())} == result["by_generator_variant_preset"]
    assert exact == result["exact_matches"]
    assert leaders == result["long_prefix_examples"]
    assert dig.hexdigest() == result["case_digest_sha256"]
    print("Independent full-grid check passed:", key_count, "keys;", sum(hist.values()),
          "preset rows;", len(exact), "exact openings")


if __name__ == "__main__":
    check()
