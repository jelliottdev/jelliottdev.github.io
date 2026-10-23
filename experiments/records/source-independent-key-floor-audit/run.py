#!/usr/bin/env python3
"""Replay pinned D2 and audit what its source actually proves."""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
MANIFEST = HERE / "source-manifest.json"
SCRIPT = SOURCE / "liber-primus/analysis/round12/D2/recompute.py"
OUT = HERE / "results.json"
TRACE = HERE / "source-replay.txt"


def verify_source() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["commit"] == "f08b20b632d91209ddbaa747e8e2f23df0c78ba1"
    for item in manifest["files"]:
        path = SOURCE / item["path"]
        assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    return manifest


def captured_source() -> str:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
    process = subprocess.run([sys.executable, str(SCRIPT)], cwd=HERE,
                             env=env, text=True, encoding="utf-8",
                             capture_output=True, check=True)
    return process.stdout.replace("\r\n", "\n")


def number(text: str, pattern: str) -> float:
    match = re.search(pattern, text)
    assert match is not None, pattern
    return float(match.group(1))


def finite_control() -> dict:
    """An independent, finite key generator can produce a sub-floor *realization*."""
    modulus = 3
    plaintext = (0, 0, 1, 0)  # differences: 0, 1, 2; each occurs once
    differences = [(b - a) % modulus for a, b in zip(plaintext, plaintext[1:])]
    assert Counter(differences) == {0: 1, 1: 1, 2: 1}
    floor = Fraction(min(Counter(differences).values()), len(differences))
    bins: Counter[int] = Counter()
    for key in itertools.product(range(modulus), repeat=len(plaintext)):
        ciphertext = [(p + k) % modulus for p, k in zip(plaintext, key)]
        count = sum(a == b for a, b in zip(ciphertext, ciphertext[1:]))
        bins[count] += 1
    assert sum(bins.values()) == modulus ** len(plaintext) == 81
    assert [bins[i] for i in range(4)] == [24, 36, 18, 3]
    assert Fraction(sum(i * n for i, n in bins.items()), 81 * 3) == floor
    return {"alphabet_size": modulus, "plaintext": list(plaintext),
            "plaintext_difference_counts": [1, 1, 1],
            "minimum_plaintext_difference_probability": str(floor),
            "independent_uniform_key_sequences": 81,
            "ciphertext_doublet_count_distribution": [bins[i] for i in range(4)],
            "probability_of_below_floor_realization": str(Fraction(bins[0], 81)),
            "expected_ciphertext_doublet_rate": str(floor)}


def calculate() -> tuple[dict, str]:
    verify_source()
    trace = captured_source()
    assert "CONTROL_OK = True" in trace
    control_english = number(trace, r"planted English score_norm =\s*([-\d.]+)")
    control_noise = number(trace, r"shuffled\s+noise score_norm =\s*([-\d.]+)")
    assert control_english >= -5.5 and control_noise <= -6.5
    assert control_english > control_noise + 1.5
    assert number(trace, r"repo 'unsolved' = pages\[:-2\] flattened: n = (\d+)") == 12956
    assert re.search(r"flattened:\s*86 doublets / 12955 adj pairs", trace)
    assert re.search(r"per-page\s*:\s*86 doublets / 12901 adj pairs", trace)
    assert re.search(r"cross-page joins:\s*54 pairs, 0 of them doublets", trace)
    assert re.search(r"F-rune count in stream:\s*458", trace)
    ioc = number(trace, r"IoC.N \(with F, flattened\)\s*=\s*([\d.]+)")
    entropy = number(trace, r"entropy \(with F\)\s*=\s*([\d.]+)")
    assert abs(ioc - 0.9999) < 0.0001 and abs(entropy - 4.8565) < 0.0001
    b4 = SOURCE / "liber-primus/analysis/round10b/B4-otp-steelman"
    prereg = (b4 / "PREREG.md").read_text(encoding="utf-8")
    code = (b4 / "b4_identifiability.py").read_text(encoding="utf-8")
    d2_code = SCRIPT.read_text(encoding="utf-8")
    assert "≥5 independent English-in-futhorc encodings of ≥100k runes each" in prereg
    assert '("kjv", "moby", "pride", "war")' in code
    missing = [name for name in ("kjv", "moby", "pride", "war")
               if not (SOURCE / f"liber-primus/data/{name}.txt").exists()]
    assert len(missing) == 4
    assert "min_d Pdp" not in d2_code and "diff_dist" not in d2_code
    b4_saved = json.loads((b4 / "b4_results.json").read_text(encoding="utf-8"))["G3"]
    l7_saved = json.loads((SOURCE / "liber-primus/analysis/round18/L7-redteam/out_c1.json")
                          .read_text(encoding="utf-8"))
    d2_saved = json.loads((SOURCE / "liber-primus/analysis/round12/D2/results.json")
                          .read_text(encoding="utf-8"))
    result = {
        "source_commit": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
        "d2_control": {"planted_english_score": control_english,
                       "shuffled_noise_score": control_noise, "passed": True},
        "measured_runes": 12956,
        "measured_within_page_doublets": 86,
        "measured_within_page_edges": 12901,
        "measured_flattened_edges": 12955,
        "measured_cross_page_join_doublets": 0,
        "measured_interrupter_count": 458,
        "measured_ioc_times_29": ioc,
        "measured_entropy_bits": entropy,
        "d2_script_recomputes_g3_floor": False,
        "d2_saved_g3_floor_is_reported_not_recomputed_here": d2_saved["recomputation"]["g3_doublet_floor_min_pdp_pct"],
        "b4_original_reported_large_corpus_min_pct": b4_saved["min_over_large_corpora_pct"],
        "l7_later_reported_floor": l7_saved["C2_g3_floor"],
        "b4_preregistered_minimum_large_corpora": 5,
        "b4_implemented_large_corpora": 4,
        "b4_large_corpus_inputs_absent": missing,
        "finite_independent_key_control": finite_control(),
        "interpretation": "The convolution floor bounds an expected rate under its independence assumptions, not every finite ciphertext realization. The D2 script confirms rune counts but does not rerun the reported corpus floor."
    }
    return result, trace


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result, trace = calculate()
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        OUT.write_text(payload, encoding="utf-8", newline="\n")
        TRACE.write_text(trace, encoding="utf-8", newline="\n")
    if args.check:
        assert OUT.read_text(encoding="utf-8") == payload
        assert TRACE.read_text(encoding="utf-8") == trace
    print("D2 control and counts pass; G3 corpus floor not rerun; finite counterexample passes")


if __name__ == "__main__":
    main()
