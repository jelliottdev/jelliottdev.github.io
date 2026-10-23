"""Independent source-grid accounting and four-mask positive controls."""

import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from run import source_grid, masked_opening  # noqa: E402
sys.path.insert(0, str(ROOT / "experiments" / "engines"))
from fixed_crib_skip import match_prefix  # noqa: E402


def check():
    r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    source_receipt = json.loads((HERE / "source/string_seed_results.json").read_text(encoding="utf-8"))
    _, modes, candidates = source_grid()
    assert len(candidates) == 1284
    assert {type(c).__name__ for c in candidates} == {"str", "bytes", "int", "float"}
    assert len(candidates) * len(modes) * 2 == source_receipt["tested"] == r["source_config_count"] == 15408
    assert r["path_count"] == 15408 * 4 == 61632
    assert sum(r["best_prefix_histogram"].values()) == r["path_count"]
    assert sum(sum(v.values()) for v in r["by_stream_mode"].values()) == r["path_count"]
    assert r["exact_match_count"] == len(r["exact_matches"]) == 0
    assert max(map(int, r["best_prefix_histogram"])) == 5
    assert r["page_count"] == 55 and r["crib_count"] == 9

    # Independent first-two-F mask oracle. The fixture contains two genuine F
    # occurrences among its first twelve output positions in all four arms.
    cipher = [5, 0, 4, 2, 0, 9, 13, 20, 6, 2, 1, 18, 17, 25]
    explicit = {
        0: cipher[:12],
        1: [cipher[i] for i in range(13) if i != 1][:12],
        2: [cipher[i] for i in range(13) if i != 4][:12],
        3: [cipher[i] for i in range(14) if i not in (1, 4)][:12],
    }
    key = [random.Random(3301 + i).randrange(29) for i in range(260)]
    for mask in range(4):
        chosen = masked_opening(cipher, mask)
        assert list(chosen) == explicit[mask]
        for sign in (-1, 1):
            plain = [(c + sign * k) % 29 for c, k in zip(chosen, key)]
            assert match_prefix(chosen, plain, key, sign, max_skip=0) == 12
            altered = list(plain)
            altered[0] = (altered[0] + 1) % 29
            assert match_prefix(chosen, altered, key, sign, max_skip=0) == 0

    # Source stream() semantics are checked against a separately written
    # random.Random construction for representative typed seeds and modes.
    source_stream, _, _ = source_grid()
    for seed in (3301, "3301", b"3301", 20140109, 3.301):
        for mode in modes:
            expected_rng = random.Random(seed)
            if mode == "randrange":
                expected = [expected_rng.randrange(29) for _ in range(32)]
            elif mode == "randint":
                expected = [expected_rng.randint(0, 28) for _ in range(32)]
            elif mode == "random":
                expected = [int(expected_rng.random() * 29) for _ in range(32)]
            elif mode == "choice":
                expected = [expected_rng.choice(list(range(29))) for _ in range(32)]
            elif mode == "shuffle":
                pool, expected = list(range(29)), []
                while len(expected) < 32:
                    expected_rng.shuffle(pool)
                    expected.extend(pool)
                expected = expected[:32]
            else:
                expected = [expected_rng.getrandbits(5) % 29 for _ in range(32)]
            assert source_stream(seed, mode, n=32) == expected
    print("Typed seed controls pass: 15,408 source configs, four F masks, both signs, independent Random stream samples")


if __name__ == "__main__":
    check()
