"""Synthetic-only timing of pinned B04's unchanged generator and beam scorer."""
import hashlib
import json
import math
import pathlib
import statistics
import sys
import time

import argparse

_parser = argparse.ArgumentParser(description=__doc__)
_parser.add_argument("--source-root", type=pathlib.Path, required=True)
_parser.add_argument("--output", type=pathlib.Path)
_args = _parser.parse_args()
SOURCE = _args.source_root.resolve()
sys.path.insert(0, str(SOURCE / "liber-primus/analysis/round13/B04"))
import harness as H  # noqa: E402
import ks  # noqa: E402
import skipdecode as sk  # noqa: E402

OUT = _args.output or pathlib.Path(__file__).with_name("b04-throughput-bench-20261023.json")
TEXT = ("THE PRIMES ARE SACRED AND THE TOTIENT FUNCTION IS SACRED "
        "THE PILGRIM SEEKS THE TRUTH AND THE TRUTH IS A JOURNEY ")
SEED = b"THE PRIMES ARE SACRED"


def bench(n, reps, matching_key, source_d_reserve=False):
    unit = sk.eng_to_idx(TEXT)
    plain = (unit * math.ceil(n / len(unit)))[:n]
    key = ks.make_ks("sha256_ctr", "mod29", SEED, 4 * n + 64)
    cipher, skips, _ = sk.encipher_keyskip(plain, key, sign=-1, supp=0.83, seed=3301)
    decode_length = n + 512 if source_d_reserve else 4 * n + 64
    decode_key = key if matching_key else ks.make_ks("sha256_ctr", "mod29", b"WRONG B04 SEED", decode_length)
    timings = []
    results = []
    for _ in range(reps):
        t0 = time.perf_counter()
        result = sk.beam_decode(cipher, decode_key, sign=-1, o=0,
                                beam_w=H.BEAM_W, max_skip=H.MAX_SKIP)
        timings.append(time.perf_counter() - t0)
        results.append(result)
    assert all(x["plain_idx"] == results[0]["plain_idx"] and
               x["score"] == results[0]["score"] for x in results)
    return {"length": n, "repetitions": reps, "matching_key": matching_key,
            "source_d_reserve": source_d_reserve,
            "times_s": timings, "median_s": statistics.median(timings),
            "score": results[0]["score"],
            "full_plain_recovery": results[0]["plain_idx"] == plain,
            "synthetic_skip_count": sum(skips),
            "accepted_key_end": results[0]["ptr_end"],
            "decoded_runes": len(results[0]["plain_idx"]),
            "keystream_length": len(decode_key),
            "translit_sha256": hashlib.sha256(results[0]["translit"].encode("ascii")).hexdigest(),
            "independent_final_score": sk.Q.score_norm(sk.idx_to_trans(results[0]["plain_idx"]))}


def main():
    rows = []
    for matching_key in (True, False):
        for n, reps in [(100, 5), (120, 5), (262, 3), (1024, 1)]:
            row = bench(n, reps, matching_key)
            rows.append(row)
            print(matching_key, n, row["median_s"], row["score"], row["full_plain_recovery"], flush=True)
    row = bench(12956, 1, False, source_d_reserve=True)
    rows.append(row)
    print("source-D-sized", row["length"], row["median_s"], row["accepted_key_end"], flush=True)
    payload = {"kind": "synthetic_only_b04_source_beam_timing_v1",
               "source_commit": "f08b20b", "generator": "sha256_ctr",
               "reduction": "mod29", "seed_hex": SEED.hex(),
               "beam_width": H.BEAM_W, "max_skip": H.MAX_SKIP,
               "cipher_construction": "source encipher_keyskip, supp=.83, seed=3301",
               "rows": rows}
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(OUT)


if __name__ == "__main__":
    main()
