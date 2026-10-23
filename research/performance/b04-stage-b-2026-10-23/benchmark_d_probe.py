"""Short synthetic timing only; does not extrapolate full Stage D runtime."""
import json
import pathlib
import time

import resumable_d as D

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = pathlib.Path(
    "C:/Users/ianex/Documents/Codex/2026-10-19/i-w/work/source-cache/dukotah-cicada3301")


def benchmark():
    H, S, ks, sk, _ = D.R.load_source(SOURCE)
    # Pinned source G2 plant: plausible skip-bearing ciphertext, no LP2 input.
    cipher = D.R.stage_inputs("A", H, S, ks, sk, g2_plant=True)[0][0][1]
    native = ks.make_ks("sha256_ctr", "mod29", b"THE PRIMES ARE SACRED",
                        len(cipher) + 512)
    kwargs = {"sign": -1, "o": 0, "beam_w": H.BEAM_W,
              "max_skip": H.MAX_SKIP}
    rounds = 200
    # Warm both paths once, then alternate order to reduce warm-cache bias.
    ordinary = sk.beam_decode(cipher, native, **kwargs)
    tracked = sk.beam_decode(cipher, D.ObservedKey(native, len(native)), **kwargs)
    assert ordinary == tracked
    plain_s = tracked_s = 0.0
    for i in range(rounds):
        if i % 2:
            t = time.perf_counter(); checked = sk.beam_decode(
                cipher, D.ObservedKey(native, len(native)), **kwargs)
            tracked_s += time.perf_counter() - t
            t = time.perf_counter(); direct = sk.beam_decode(cipher, native, **kwargs)
            plain_s += time.perf_counter() - t
        else:
            t = time.perf_counter(); direct = sk.beam_decode(cipher, native, **kwargs)
            plain_s += time.perf_counter() - t
            t = time.perf_counter(); checked = sk.beam_decode(
                cipher, D.ObservedKey(native, len(native)), **kwargs)
            tracked_s += time.perf_counter() - t
        assert direct == checked
    return {"schema": "b04-d-padding-probe-short-benchmark-v1",
            "source_revision": D.R.PIN, "synthetic_runes": len(cipher),
            "rounds_per_path": rounds, "beam_width": H.BEAM_W,
            "max_skip": H.MAX_SKIP,
            "ordinary_total_s": plain_s, "tracked_total_s": tracked_s,
            "tracked_over_plain_ratio": tracked_s / plain_s,
            "source_decode_parity": True,
            "limit": "Short synthetic input on a shared busy host; not a full-book runtime estimate."}


if __name__ == "__main__":
    result = benchmark()
    (HERE / "d-probe-short-benchmark.json").write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
