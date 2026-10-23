"""B-05 receipt accounting and planted PRF-key opening controls."""

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR = HERE.parent / "grid-payload-prf-source-grid"
sys.path.insert(0, str(ROOT / "experiments/engines"))
from fixed_crib_skip import match_prefix  # noqa: E402


def check():
    r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert r["source_config_count"] == 70680 and r["unique_effective_keys"] == 59948
    assert r["page_count"] == 55 and r["crib_count"] == 9
    assert r["exact_match_count"] == len(r["exact_matches"]) == 0
    assert sum(r["best_prefix_histogram"].values()) == 70680
    assert sum(r["unique_key_prefix_histogram"].values()) == 59948
    assert {p: sum(c.values()) for p, c in r["by_source_part"].items()} == {
        "part1": 40320, "shift": 3480, "part2a": 3840, "part2b": 23040}
    assert max(map(int, r["best_prefix_histogram"])) == 5
    assert hashlib.sha256((PRIOR / "cases.jsonl").read_bytes()).hexdigest() == r["prior_case_receipt_sha256"]

    # Construct a genuinely skipped-key opening from a pinned PRF key, rather
    # than choosing an arbitrary key unrelated to the tested family.
    spec = importlib.util.spec_from_file_location("source_prf", HERE.parent / "grid-payload-prf-seed-corner/source/liber-primus/analysis/round13/B05/prf.py")
    prf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prf)
    seed, _ = prf.load_payloads()
    raw_key = prf.keystream(seed, "sha256_ctr", "mod", 1600)
    key = [(-k) % 29 for k in raw_key]  # source sign -1 normalized to matcher sign +1
    if key[1] == key[2]:
        raise AssertionError("Planted skip control needs distinct adjacent key values")
    cipher = [5, (5 + key[1] - key[2]) % 29] + [(3 * i + 7) % 29 for i in range(2, 12)]
    plain = [(cipher[0] + key[0]) % 29, (cipher[1] + key[2]) % 29]
    plain += [(cipher[i] + key[i + 1]) % 29 for i in range(2, 12)]
    assert match_prefix(cipher, plain, key, sign=1, max_skip=3) == 12
    assert match_prefix(cipher, plain, key, sign=1, max_skip=0) < 12
    no_skip = [(cipher[i] + key[i]) % 29 for i in range(12)]
    assert match_prefix(cipher, no_skip, key, sign=1, max_skip=0) == 12
    print("B-05 opening checks pass: prior source case receipt, four part totals, planted PRF no-skip and forced-skip controls")


if __name__ == "__main__":
    check()
