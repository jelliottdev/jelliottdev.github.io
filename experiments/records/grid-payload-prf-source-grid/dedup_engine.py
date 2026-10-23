#!/usr/bin/env python3
"""Exact effective-key replay of the remaining pinned B-05 screen grids.

An effective key is sign*K[o:o+1597] modulo 29, after any direction,
Atbash or constant shift. B-05's beam can read no further than index 1596
while decoding 400 runes with at most three skips per step. Equal effective
keys therefore give identical beam inputs and scores; source case rows remain
separate in the output even when their work is shared.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PILOT = HERE.parent / "grid-payload-prf-seed-corner"
MASKS = HERE.parent / "grid-payload-prf-contested-masks"
LANE = PILOT / "source/liber-primus/analysis/round13/B05"
sys.path.insert(0, str(LANE))
import prf  # type: ignore[import-not-found]  # noqa: E402
import sweep  # type: ignore[import-not-found]  # noqa: E402

KEY_LEN = 1 + (sweep.HEAD - 1) * (sweep.MAX_SKIP + 1)
assert KEY_LEN == 1597 and len(sweep.HEADSEQ) == 400
PARTS = ("part1", "shift", "part2a", "part2b")
RESULTS = HERE / "results.json"
CASES = HERE / "cases.jsonl"


def effective(key: list[int], sign: int, offset: int = 0, atbash: bool = False,
              shift: int = 0) -> bytes:
    assert offset + KEY_LEN <= len(key)
    if atbash:
        return bytes((sign * ((28 - v + shift) % 29)) % 29 for v in key[offset:offset + KEY_LEN])
    return bytes((sign * ((v + shift) % 29)) % 29 for v in key[offset:offset + KEY_LEN])


def add(rows: list[dict], keys: dict[str, bytes], part: str, params: dict, value: bytes) -> None:
    digest = hashlib.sha256(value).hexdigest()
    keys.setdefault(digest, value)
    rows.append({"part": part, **params, "effective_key_sha256": digest})


def enumerate_cases() -> tuple[list[dict], dict[str, bytes]]:
    rows: list[dict] = []
    keys: dict[str, bytes] = {}
    # Part 1 uses a full-length key even for the 400-rune HEAD: reversing the
    # short key would change every source-defined reverse-direction candidate.
    representations = prf.representations()
    for rep in sorted(representations):
        seed = representations[rep]
        for gen in prf.GENERATORS:
            for red in sweep.REDUCTIONS:
                base = prf.keystream(seed, gen, red, sweep.TOTAL_KS)
                for direction in sweep.DIRECTIONS:
                    key = base if direction == "fwd" else base[::-1]
                    for atbash in sweep.ATBASH:
                        for sign in sweep.SIGNS:
                            for offset in sweep.OFFSETS:
                                add(rows, keys, "part1", {"rep": rep, "gen": gen, "red": red,
                                    "direction": direction, "atbash": atbash,
                                    "sign": sign, "offset": offset},
                                    effective(key, sign, offset, atbash))
    # Part 1b adds a constant to the forward, unmirrored raw keys.
    maj, dec = prf.load_payloads()
    need = sweep.HEAD * (sweep.MAX_SKIP + 1) + 64
    for rep, seed in (("maj.raw", maj), ("dec.raw", dec)):
        for gen in prf.GENERATORS:
            for red in sweep.REDUCTIONS:
                base = prf.keystream(seed, gen, red, need)
                for shift in range(29):
                    for sign in sweep.SIGNS:
                        add(rows, keys, "shift", {"rep": rep, "gen": gen,
                            "red": red, "shift": shift, "sign": sign},
                            effective(base, sign, shift=shift))
    # Part 2a is already replayed; include it here only to seed the score cache
    # and prove parity. It is excluded from the new record's case count.
    for mask in range(64):
        seed = bytearray(maj)
        for bit, idx in enumerate(prf.CONTESTED):
            if mask & (1 << bit):
                seed[idx] = dec[idx]
        for gen in prf.GENERATORS:
            for red in sweep.REDUCTIONS:
                base = prf.keystream(bytes(seed), gen, red, need)
                for sign in sweep.SIGNS:
                    add(rows, keys, "part2a", {"mask": mask, "gen": gen,
                        "red": red, "sign": sign}, effective(base, sign))
    # Part 2b: one arbitrary value at one contested position, holding the
    # other five bytes at their majority values.
    for idx in prf.CONTESTED:
        for val in range(256):
            seed = bytearray(maj)
            seed[idx] = val
            for gen in prf.GENERATORS:
                base = prf.keystream(bytes(seed), gen, "mod", need)
                add(rows, keys, "part2b", {"index": idx, "value": val,
                    "gen": gen}, effective(base, -1))
    assert len(rows) == 70680
    return rows, keys


def seeded_scores(rows: list[dict]) -> dict[str, float]:
    lookup = {(r["mask"], r["generator"], r["reduction"], r["sign"]): r["score"]
              for r in json.loads((MASKS / "cases.json").read_text(encoding="utf-8"))["cases"]}
    pilot = json.loads((PILOT / "results.json").read_text(encoding="utf-8"))["rows"]
    scores: dict[str, float] = {}
    for row in rows:
        if row["part"] != "part2a":
            continue
        score = lookup[(row["mask"], row["gen"], row["red"], row["sign"])]
        digest = row["effective_key_sha256"]
        if digest in scores and abs(scores[digest] - score) > 0.000001:
            raise AssertionError("same effective key received different source scores")
        scores[digest] = score
    by_corner = {(0 if r["representation"] == "maj.raw" else 63,
                  r["generator"], r["reduction"], r["sign"]): r["score"] for r in pilot}
    for key, value in by_corner.items():
        assert lookup[key] == value
    assert len(lookup) == 3840 and len(scores) == 2596 and len(by_corner) == 32
    return scores


def _score_item(item: tuple[str, bytes]) -> tuple[str, float]:
    digest, key = item
    score = sweep.sk.beam_decode(sweep.HEADSEQ, list(key), sign=1, o=0,
                                 beam_w=sweep.BEAM_W, max_skip=sweep.MAX_SKIP)["score"]
    return digest, round(score, 6)


def check_parity(rows: list[dict], keys: dict[str, bytes], seeded: dict[str, float]) -> None:
    seen = set()
    checked = 0
    for row in rows:
        if row["part"] != "part2a":
            continue
        digest = row["effective_key_sha256"]
        if digest in seen:
            continue
        seen.add(digest)
        actual = _score_item((digest, keys[digest]))[1]
        assert abs(actual - seeded[digest]) <= 0.000001, (row, actual, seeded[digest])
        checked += 1
        if checked == 32:
            break
    assert checked == 32
    # Compare transformed-key decoding with the unmodified source call on
    # representative directions, Atbash states, signs, offsets and subtests.
    selected = []
    for direction in sweep.DIRECTIONS:
        for atbash in sweep.ATBASH:
            for sign in sweep.SIGNS:
                for offset in (0, 3301):
                    selected.append(next(r for r in rows if r["part"] == "part1" and
                                         r["rep"] == "maj.raw" and r["gen"] == "sha256_ctr" and
                                         r["red"] == "mod" and r["direction"] == direction and
                                         r["atbash"] == atbash and r["sign"] == sign and
                                         r["offset"] == offset))
    for shift in (0, 1, 14, 28):
        selected.append(next(r for r in rows if r["part"] == "shift" and
                             r["rep"] == "dec.raw" and r["gen"] == "rc4" and
                             r["red"] == "reject" and r["sign"] == -1 and
                             r["shift"] == shift))
    for index in (25, 237):
        for value in (0, 255):
            selected.append(next(r for r in rows if r["part"] == "part2b" and
                                 r["index"] == index and r["value"] == value and
                                 r["gen"] == "aes128_ctr_k"))
    reps = prf.representations()
    majority, _ = prf.load_payloads()
    for row in selected:
        if row["part"] == "part1":
            base = prf.keystream(reps[row["rep"]], row["gen"], row["red"], sweep.TOTAL_KS)
            key = base if row["direction"] == "fwd" else base[::-1]
            if row["atbash"]:
                key = prf.atbash(key)
            sign, offset = row["sign"], row["offset"]
        elif row["part"] == "shift":
            base = prf.keystream(reps[row["rep"]], row["gen"], row["red"],
                                 sweep.HEAD * (sweep.MAX_SKIP + 1) + 64)
            key = [(v + row["shift"]) % 29 for v in base]
            sign, offset = row["sign"], 0
        else:
            seed = bytearray(majority)
            seed[row["index"]] = row["value"]
            key = prf.keystream(bytes(seed), row["gen"], "mod",
                                sweep.HEAD * (sweep.MAX_SKIP + 1) + 64)
            sign, offset = -1, 0
        source_score = round(sweep.sk.beam_decode(
            sweep.HEADSEQ, key, sign=sign, o=offset,
            beam_w=sweep.BEAM_W, max_skip=sweep.MAX_SKIP)["score"], 6)
        shared_score = _score_item((row["effective_key_sha256"],
                                   keys[row["effective_key_sha256"]]))[1]
        assert source_score == shared_score, (row, source_score, shared_score)


def checkpoint_path(root: Path) -> Path:
    source_manifest = (PILOT / "source-manifest.json").read_bytes()
    engine = Path(__file__).read_bytes()
    scope = json.dumps({"head": sweep.HEADSEQ, "beam": sweep.BEAM_W,
                        "max_skip": sweep.MAX_SKIP, "total_key": sweep.TOTAL_KS},
                       separators=(",", ":")).encode()
    digest = hashlib.sha256(source_manifest + engine + scope).hexdigest()[:20]
    root.mkdir(parents=True, exist_ok=True)
    return root / f"b05-scores-{digest}.jsonl"


def load_checkpoint(path: Path) -> dict[str, float]:
    scores: dict[str, float] = {}
    if not path.exists():
        return scores
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
            proof = hashlib.sha256(f"{item['key']}:{item['score']:.6f}".encode()).hexdigest()
            if len(item["key"]) == 64 and isinstance(item["score"], (int, float)) and item["proof"] == proof:
                scores[item["key"]] = float(item["score"])
        except (ValueError, KeyError, TypeError):
            # A process interrupted during the final append may leave a partial line.
            continue
    return scores


def save_final(rows: list[dict], scores: dict[str, float], seeded_count: int) -> None:
    for row in rows:
        assert row["effective_key_sha256"] in scores
    relevant = [row for row in rows if row["part"] != "part2a"]
    by_part = {}
    for part in ("part1", "shift", "part2b"):
        matches = [row for row in relevant if row["part"] == part]
        best = max(matches, key=lambda row: scores[row["effective_key_sha256"]])
        by_part[part] = {"cases": len(matches), "best": {**best,
            "score": scores[best["effective_key_sha256"]]},
            "hits": sum(scores[row["effective_key_sha256"]] >= -5.5 for row in matches)}
    with CASES.open("w", encoding="utf-8", newline="\n") as handle:
        for row in relevant:
            handle.write(json.dumps({**row, "score": scores[row["effective_key_sha256"]]},
                                    separators=(",", ":")) + "\n")
    summary = {"source_commit": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
               "source_parts": ["part1", "shift", "part2b"],
               "case_count": len(relevant), "prior_part2a_cases_reused": 3840,
               "unique_effective_keys_all_parts": len({r["effective_key_sha256"] for r in rows}),
               "seeded_unique_scores": seeded_count,
               "new_unique_scores": len(scores) - seeded_count,
               "by_part": by_part,
               "english_score_floor": -5.5,
               "source_null_max": json.loads((MASKS / "results.json").read_text(encoding="utf-8"))["null"]["max"]}
    RESULTS.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"saved {len(relevant)} remaining source rows; "
          f"{summary['new_unique_scores']} newly scored keys", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", action="store_true", help="enumerate and prove saved-score parity only")
    parser.add_argument("--run", action="store_true", help="score missing keys and save final rows")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit-new", type=int, default=0, help="internal benchmark: stop after this many new keys")
    parser.add_argument("--checkpoint-dir", type=Path, default=REPO.parent / "b05-grid-cache")
    args = parser.parse_args()
    started = time.perf_counter()
    rows, keys = enumerate_cases()
    prior = seeded_scores(rows)
    check_parity(rows, keys, prior)
    unique = len(keys)
    print(f"enumerated {len(rows)} source calls -> {unique} unique effective keys; "
          f"{len(prior)} prior keys verified", flush=True)
    if args.census and not args.run:
        return
    checkpoint = checkpoint_path(args.checkpoint_dir)
    saved = load_checkpoint(checkpoint)
    for digest, score in saved.items():
        if digest in prior and abs(prior[digest] - score) > 0.000001:
            raise AssertionError("checkpoint contradicts pinned prior result")
    saved = {digest: score for digest, score in saved.items() if digest in keys}
    scores = {**saved, **prior}
    missing = [(digest, key) for digest, key in keys.items() if digest not in scores]
    total_missing = len(missing)
    if args.limit_new:
        missing = missing[:args.limit_new]
    print(f"checkpoint {checkpoint.name}: {len(saved)} cached, "
          f"{total_missing} missing, scoring {len(missing)} now", flush=True)
    pool = ProcessPoolExecutor(max_workers=args.workers) if args.workers > 1 else None
    try:
        with checkpoint.open("a", encoding="utf-8", newline="\n") as handle:
            for start in range(0, len(missing), 1000):
                chunk = missing[start:start + 1000]
                if pool is None:
                    completed = map(_score_item, chunk)
                else:
                    futures = [pool.submit(_score_item, item) for item in chunk]
                    completed = (future.result() for future in as_completed(futures))
                for digest, score in completed:
                    scores[digest] = score
                    proof = hashlib.sha256(f"{digest}:{score:.6f}".encode()).hexdigest()
                    handle.write(json.dumps({"key": digest, "score": score, "proof": proof}) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
                done = min(start + len(chunk), len(missing))
                print(f"scored {done}/{len(missing)} in {time.perf_counter()-started:.1f}s", flush=True)
    finally:
        if pool is not None:
            pool.shutdown()
    if len(scores) == unique:
        save_final(rows, scores, len(prior))
    else:
        print(f"resume with the same command for {unique-len(scores)} remaining keys", flush=True)


if __name__ == "__main__":
    main()
