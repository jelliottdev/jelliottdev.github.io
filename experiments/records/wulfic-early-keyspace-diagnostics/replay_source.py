"""Run the pinned Wulfic J/K/L tests and preserve their finite model inputs/results."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import types
import unittest

HERE = Path(__file__).resolve().parent
REV = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"


def blob(source: Path, name: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{REV}:{name}"], cwd=source)


def emit(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    args = ap.parse_args()
    source = args.source.resolve()
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source).decode().strip() != REV:
        raise SystemExit("source HEAD differs from pinned revision")
    test_bytes = blob(source, "tests/test_keyspace.py")
    source_paths = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))["source_paths"]
    source_hashes = {p: hashlib.sha256(blob(source, p)).hexdigest() for p in source_paths}
    source_hashes["tests/test_keyspace.py"] = hashlib.sha256(test_bytes).hexdigest()
    sys.path.insert(0, str(source))
    os.chdir(source)
    module = types.ModuleType("pinned_test_keyspace")
    module.__file__ = f"{REV}:tests/test_keyspace.py"
    exec(compile(test_bytes, module.__file__, "exec"), module.__dict__)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful() or result.testsRun != 13:
        raise SystemExit("source positive/control/verdict tests failed")

    from tools.lpcore import detect, keys, leak, stats
    from tools.lpcore.gematria import N
    streams = module.LP2
    sequence = [r for s in streams for r in s]
    cnt = module.counts(sequence)
    c10 = []
    for lam in (1.0, 0.5, 0.25):
        for name, mapping in module.MAPPINGS.items():
            for mode in detect.MODES:
                values = [stats.unigram_llr(cnt, stats.running_key_distribution(module.Q, mapping, mode, lam, offset))
                          for offset in range(N)]
                c10.append({"mixture": lam, "mapping": name, "mode": mode,
                            "best_llr": max(values), "best_offset": values.index(max(values))})
    c11 = []
    for lag in range(2, 1001):
        for sign in (1, -1):
            chi2, pairs = stats.lag_combination_chi2(streams, lag, sign)
            p = leak.chi2_sf_even_df(chi2, N - 1)
            c11.append({"lag": lag, "sign": sign, "pairs": pairs, "chi2": chi2, "p": p})
    c12 = []
    for lag in range(1, 1001):
        chi2, df = stats.transition_chi2(streams, lag)
        p = stats.chi2_sf_wilson_hilferty(chi2, df)
        c12.append({"lag": lag, "df": df, "chi2": chi2, "p": p})
    c13 = []
    arms = dict(module.TestC13KeyAlphabets.TESTABLE)
    arms["English as Latin letters"] = module.latin_letter_weights()
    for name, weights in arms.items():
        key = stats.values_distribution(weights)
        vals = [(stats.unigram_llr(cnt, stats.cipher_distribution(module.Q, key, mode, offset)), mode, offset)
                for mode in detect.MODES for offset in range(N)]
        best, mode, offset = max(vals)
        c13.append({"alphabet": name, "best_llr": best, "best_mode": mode,
                    "best_offset": offset, "weights": weights})
    wide = []
    for name, weights in module.TestC13KeyAlphabets.UNTESTABLE.items():
        key = stats.values_distribution(weights)
        predicted = stats.cipher_distribution(module.Q, key, "sub")
        import math
        expectation = len(sequence) * sum(x * math.log(N * x) for x in predicted)
        wide.append({"alphabet": name, "predicted_llr_if_true": expectation})
    emit(HERE / "inputs.json", {"source_revision": REV, "source_sha256": source_hashes,
                               "runes": sequence, "segments": [len(s) for s in streams],
                               "solved_model_q": module.Q})
    emit(HERE / "results.json", {"source_tests_passed": result.testsRun, "rune_count": len(sequence),
                                "c10": c10, "c11": c11, "c12": c12, "c13": c13,
                                "c13_underpowered": wide,
                                "source_decision_lines": {"c10_c13_llr": -10, "c11_bonferroni": .01/1998,
                                                          "c12_bonferroni": .01/1000}})
    print(f"source tests: {result.testsRun}; C10 {len(c10)}, C11 {len(c11)}, C12 {len(c12)}, C13 {len(c13)}")


if __name__ == "__main__":
    main()
