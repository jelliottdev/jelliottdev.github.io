"""Independent path oracle and planted controls for the B-04 opening batch."""

import importlib.util
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "engines"))
from fixed_crib_skip import match_prefix  # noqa: E402


def exhaustive_prefix(cipher, plain, key, sign, max_skip):
    """Enumerate all skip vectors recursively, independent of matcher DP."""
    if not cipher or not plain or not key or (cipher[0] + sign * key[0]) % 29 != plain[0]:
        return 0
    reachable = [(0, 1)]
    best = 1
    while reachable and best < min(len(cipher), len(plain)):
        nxt = []
        i = best
        for previous_key, _ in reachable:
            for skipped in range(max_skip + 1):
                accepted = previous_key + skipped + 1
                if accepted >= len(key):
                    continue
                trial = (cipher[i] + sign * key[accepted]) % 29
                if trial != plain[i]:
                    continue
                rejected = list(range(previous_key + 1, accepted))
                if any((trial - sign * key[k]) % 29 != cipher[i - 1] for k in rejected):
                    continue
                nxt.append((accepted, i + 1))
        if not nxt:
            break
        reachable = nxt
        best += 1
    return best


def check():
    r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert r["config_count"] == 2165 * 16 * 5 * 2 * 2 * 2 == 1_385_600
    assert r["page_count"] == 55 and r["crib_count"] == 9
    assert sum(r["best_prefix_histogram"].values()) == r["config_count"]
    assert r["exact_match_count"] == len(r["exact_matches"]) == 0
    assert max(map(int, r["best_prefix_histogram"])) == 6
    assert sum(sum(c.values()) for c in r["by_generator_reduction"].values()) == r["config_count"]

    rng = random.Random(3301)
    for _ in range(400):
        length = rng.randrange(1, 6)
        cipher = [rng.randrange(29) for _ in range(length)]
        plain = [rng.randrange(29) for _ in range(length)]
        key = [rng.randrange(29) for _ in range(20)]
        sign = rng.choice((-1, 1))
        bound = rng.randrange(4)
        assert match_prefix(cipher, plain, key, sign, bound) == exhaustive_prefix(cipher, plain, key, sign, bound)

    # Construct valid paths with rejected draws before asking both solvers to
    # recover them. This exercises the recurrence beyond first-rune misses.
    for _ in range(100):
        length = rng.randrange(2, 6)
        plain = [rng.randrange(29) for _ in range(length)]
        cipher = [rng.randrange(29) for _ in range(length)]
        sign = rng.choice((-1, 1))
        skips = [0] + [rng.randrange(4) for _ in range(length - 1)]
        if not any(skips):
            skips[1] = 1
        key = [rng.randrange(29) for _ in range(24)]
        pa = 0
        key[0] = ((plain[0] - cipher[0]) * sign) % 29
        for i in range(1, length):
            accepted = pa + 1 + skips[i]
            for rejected in range(pa + 1, accepted):
                key[rejected] = ((plain[i] - cipher[i - 1]) * sign) % 29
            key[accepted] = ((plain[i] - cipher[i]) * sign) % 29
            pa = accepted
        assert match_prefix(cipher, plain, key, sign) == length
        assert exhaustive_prefix(cipher, plain, key, sign, 3) == length
        mutated = list(plain)
        mutation_index = rng.randrange(length)
        mutated[mutation_index] = (mutated[mutation_index] + 1) % 29
        assert match_prefix(cipher, mutated, key, sign) == exhaustive_prefix(cipher, mutated, key, sign, 3)

    # A fixed twelve-rune opening under a *pinned source-generated* keystream.
    spec = importlib.util.spec_from_file_location("source_ks", HERE / "source/ks.py")
    ks = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ks)
    plain = r["cribs"][0]["indices"]
    key = ks.make_ks("sha256_ctr", "mod29", b"THE PRIMES ARE SACRED", 728)
    cipher = [(plain[i] + key[i]) % 29 for i in range(12)]  # sign -1, no skips
    assert match_prefix(cipher, plain, key, -1) == 12

    # Force a rejected-doublet key draw at the second symbol, then continue.
    forced_key = [3, (plain[0] + 3 - plain[1]) % 29, 8]
    forced_key += [(5 * i + 2) % 29 for i in range(3, 20)]
    forced_cipher = [(plain[0] + forced_key[0]) % 29,
                     (plain[1] + forced_key[2]) % 29]
    forced_cipher += [(plain[i] + forced_key[i + 1]) % 29 for i in range(2, 12)]
    assert forced_cipher[0] != forced_cipher[1]
    assert match_prefix(forced_cipher, plain, forced_key, -1) == 12
    assert match_prefix(forced_cipher, plain, forced_key, -1, max_skip=0) < 12

    # Reconstruct a small deterministic cross-section of full source candidates.
    seed_entries = json.loads((HERE / "seed-manifest.json").read_text(encoding="utf-8"))["entries"]
    for seed_i in (0, 41, 330, 1800, 2164):
        seed = bytes.fromhex(seed_entries[seed_i]["hex"])
        for generator in ("sha256_ctr", "md5_chain", "hmac_drbg_sha256", "chacha20"):
            raw = ks.make_bytes(generator, seed, int(728 * 1.35) + 256)
            for reduction in ks.RED_NAMES:
                stream = ks.make_ks(generator, reduction, seed, 728, raw=raw)
                assert len(stream) >= 728
                for direction in (stream, stream[::-1]):
                    assert match_prefix(cipher, plain, direction, -1) == exhaustive_prefix(cipher, plain, direction, -1, 3)
    print("B-04 checks passed: 400 random and 100 planted exhaustive oracle cases, source-key and skip controls, aggregate integrity")


if __name__ == "__main__":
    check()
