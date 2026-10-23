"""Offline G3 pointer-screen replay. Uses a separate implementation of source rules."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
B32 = "abcdefghijklmnopqrstuvwxyz234567"
PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
          53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109)
KEYS = ("v2_16", "v3_56", "b32_lowentropy_run", "latlon_regex", "coord_pair_rate")


def lowentropy_run(s: str, k: int = 8) -> int:
    """Qualified-window run, including the original detector's endpoint convention."""
    qualifies = [len(set(s[i:i + k])) <= k // 2 for i in range(max(0, len(s) - k))]
    best = i = 0
    while i < len(qualifies):
        if not qualifies[i]:
            i += 1
            continue
        end = i + 1
        while end < len(qualifies) and qualifies[end]:
            end += 1
        best = max(best, end - i + k)
        i = end + k
    return best


def metrics(values: list[int]) -> dict[str, int]:
    b32 = "".join(B32[v % 32] for v in values)
    digits = "".join(str(v) for v in values)
    return {
        "v2_16": len(b32) // 16,
        "v3_56": len(b32) // 56,
        "b32_lowentropy_run": lowentropy_run(b32),
        "latlon_regex": len(re.findall(r"[+-]?\d{1,3}\.\d{3,}[ ,]+[+-]?\d{1,3}\.\d{3,}", digits)),
        "coord_pair_rate": sum(-60 < values[i] % 180 - 90 < 75 and
                               -170 < values[i + 1] % 360 - 180 < 170
                               for i in range(0, len(values) - 1, 2)),
    }


def transform(indices: list[int], name: str) -> list[int]:
    if name == "value":
        return [PRIMES[x] for x in indices]
    if name == "pi":
        return [x + 1 for x in indices]
    if name == "phi":
        return [PRIMES[x] - 1 for x in indices]
    raise ValueError(name)


def site_parity(root: Path, indices: list[int]) -> None:
    alphabet = json.loads((root / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    lookup = {row["rune"]: i for i, row in enumerate(alphabet)}
    got = []
    runes = []
    pages = [f"lp2-{i:02d}" for i in range(50)] + [f"lp2-{i:02d}" for i in range(51, 56)]
    for page in pages:
        data = json.loads((root / f"data/pages/{page}.json").read_text(encoding="utf-8"))
        for line in data["lines"]:
            for c in line["raw"]:
                if c in lookup:
                    got.append(lookup[c])
                    runes.append(c)
    assert got == indices
    assert hashlib.sha256("".join(runes).encode("utf-8")).hexdigest() == (
        "79b14e630946b64cdca838f328e73904f506df576d15e21fcb46271d4b4c8040")


def replay(plan: dict, indices: list[int]) -> dict:
    rng = random.Random(3301)
    plant = [rng.randrange(29) for _ in range(300)]
    plant[120:152] = [0] * 32
    planted = metrics(transform(plant, "value"))["b32_lowentropy_run"]
    plant_null = []
    for k in range(200):
        shuffled = plant.copy()
        random.Random(3301 + k).shuffle(shuffled)
        plant_null.append(metrics(transform(shuffled, "value"))["b32_lowentropy_run"])
    assert planted > max(plant_null) and planted >= 16

    out = {"plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
           "input_sha256": hashlib.sha256(bytes(indices)).hexdigest(),
           "rune_count": len(indices),
           "controls": {"planted_lowentropy_run": planted,
                        "planted_null_max": max(plant_null),
                        "planted_flag": True,
                        "base32_counts_are_length_only": True,
                        "latlon_regex_unreachable_from_digit_only_values": True,
                        "coordinate_pair_rate_not_in_flag_rule": True},
           "streams": {}, "flagged_pointers": []}
    for name in plan["streams"]:
        real = metrics(transform(indices, name))
        null = {key: [] for key in KEYS}
        for k in range(plan["null_replicates"]):
            shuffled = indices.copy()
            random.Random(plan["seed_start"] + k).shuffle(shuffled)
            sample = metrics(transform(shuffled, name))
            for key in KEYS:
                null[key].append(sample[key])
        bands = {key: {"mean": statistics.fmean(values), "max": float(max(values))}
                 for key, values in null.items()}
        for key in ("b32_lowentropy_run", "latlon_regex"):
            if real[key] > bands[key]["max"] and (key != "b32_lowentropy_run" or real[key] >= 16):
                out["flagged_pointers"].append({"stream": name, "key": key,
                                                 "real": real[key], "null_max": bands[key]["max"]})
        out["streams"][name] = {"real": real, "null": bands}
    out["pointer_found"] = bool(out["flagged_pointers"])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--check-site", action="store_true")
    args = ap.parse_args()
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    index_bytes = (HERE / "input-indices.bin").read_bytes()
    assert hashlib.sha256(index_bytes).hexdigest() == plan["input_sha256"]
    indices = list(index_bytes)
    assert len(indices) == 12956 and all(0 <= n < 29 for n in indices)
    if args.check_site:
        site_parity(HERE.parents[2], indices)
    out = replay(plan, indices)
    archived = json.loads((HERE / "source-results.json").read_text(encoding="utf-8"))
    assert out["pointer_found"] == archived["pointer_found"]
    assert out["flagged_pointers"] == archived["flagged_pointers"]
    for name in plan["streams"]:
        assert out["streams"][name]["real"] == archived["streams"][name]["real"]
        for key in KEYS:
            got = out["streams"][name]["null"][key]
            want = archived["streams"][name]["null"][key]
            assert abs(got["mean"] - want["mean"]) < 1e-10 and got["max"] == want["max"]
    path = HERE / "results.json"
    if args.check:
        assert out == json.loads(path.read_text(encoding="utf-8"))
    else:
        path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("PASS: three streams, five measurements and 200 controls per stream match source")


if __name__ == "__main__":
    main()
