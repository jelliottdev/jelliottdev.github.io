"""Independent source-shape, control and saved-result check for G3."""
from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ALPHABET = "abcdefghijklmnopqrstuvwxyz234567"
PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
          53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109)


def original_style_run(text: str, width: int = 8) -> int:
    best = start = 0
    i = 0
    while i < len(text) - width:
        if len(set(text[i:i + width])) <= width // 2:
            j = i + width
            while j < len(text) and len(set(text[j - width:j])) <= width // 2:
                j += 1
            best = max(best, j - i)
            i = j
        else:
            i += 1
    return best


def score(indices: list[int], mode: str) -> dict:
    values = ([PRIMES[x] for x in indices] if mode == "value" else
              [x + 1 for x in indices] if mode == "pi" else
              [PRIMES[x] - 1 for x in indices])
    chars = "".join(ALPHABET[x % 32] for x in values)
    digits = "".join(str(x) for x in values)
    return {"v2_16": len(re.findall(r"[a-z2-7]{16}", chars)),
            "v3_56": len(re.findall(r"[a-z2-7]{56}", chars)),
            "b32_lowentropy_run": original_style_run(chars),
            "latlon_regex": len(re.findall(r"[+-]?\d{1,3}\.\d{3,}[ ,]+[+-]?\d{1,3}\.\d{3,}", digits)),
            "coord_pair_rate": sum(-60 < values[i] % 180 - 90 < 75 and
                                   -170 < values[i + 1] % 360 - 180 < 170
                                   for i in range(0, len(values) - 1, 2))}


def main() -> None:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    for fname, field in (("source-g3_coord_decode.py", "source_program_sha256"),
                         ("source-results.json", "source_results_sha256"),
                         ("input-indices.bin", "input_sha256")):
        assert hashlib.sha256((HERE / fname).read_bytes()).hexdigest() == plan[field]
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    idx = list((HERE / "input-indices.bin").read_bytes())
    assert len(idx) == 12956
    assert result["rune_count"] == 12956
    for mode in plan["streams"]:
        assert score(idx, mode) == result["streams"][mode]["real"]
        sampled = []
        for k in range(plan["null_replicates"]):
            sh = idx.copy()
            random.Random(plan["seed_start"] + k).shuffle(sh)
            sampled.append(score(sh, mode)["b32_lowentropy_run"])
        assert max(sampled) == result["streams"][mode]["null"]["b32_lowentropy_run"]["max"]
        assert abs(sum(sampled) / len(sampled) - result["streams"][mode]["null"]["b32_lowentropy_run"]["mean"]) < 1e-10
        assert result["streams"][mode]["real"]["v2_16"] == 12956 // 16
        assert result["streams"][mode]["real"]["v3_56"] == 12956 // 56
        assert result["streams"][mode]["real"]["latlon_regex"] == 0
    assert result["pointer_found"] is False and result["flagged_pointers"] == []
    print("PASS: independent source detector and all 600 low-entropy controls")


if __name__ == "__main__":
    main()
