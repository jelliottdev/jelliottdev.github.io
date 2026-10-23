"""Execute pinned H/O source assertions and preserve all finite manuscript diagnostics."""
from __future__ import annotations

import argparse
import hashlib
from itertools import islice
import json
import os
from pathlib import Path
import subprocess
import sys
import types
import unittest

HERE = Path(__file__).resolve().parent
REV = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"


def emit(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def source_blob(source: Path, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{REV}:{rel}"], cwd=source)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    args = ap.parse_args()
    source = args.source.resolve()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source).decode().strip() == REV
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    hashes = {p: hashlib.sha256(source_blob(source, p)).hexdigest() for p in plan["source_paths"]}
    sys.path.insert(0, str(source))
    os.chdir(source)
    module = types.ModuleType("pinned_test_leak")
    test_bytes = source_blob(source, "tests/test_leak.py")
    module.__file__ = f"{REV}:tests/test_leak.py"
    exec(compile(test_bytes, module.__file__, "exec"), module.__dict__)
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(getattr(module, name))
                               for name in plan["source_test_classes"])
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    assert result.wasSuccessful() and result.testsRun == 16

    from tools.lpcore import ciphers, leak, stats
    from tools.lpcore.gematria import N
    pairs = module.PAIRS
    plain = module.lp_plaintext()
    assert len(pairs) == 12947 and len(plain) == 2901
    pair_rows = [[p.segment, p.seg_pos, p.stream_pos, p.a, p.b, int(p.line_break), int(p.page_break)] for p in pairs]
    emit(HERE / "inputs.json", {"source_revision": REV, "source_sha256": hashes,
                                "pairs": pair_rows, "solved_plain": plain,
                                "divinity_key": module.DIVINITY, "circumferences_key": module.CIRCUMFERENCES,
                                "source_segment_lengths": [len(module.CORPUS.segment_runes(s)) for s in stats.UNSOLVED_SEGMENTS]})

    differences = leak.delta_counts(pairs)
    z = leak.delta_z_scores(pairs)
    periods = [{"clock": "joined" if along else "section", "period": m, "top": top, "p": p}
               for along in (False, True) for m in range(2, 33)
               for top, p in [leak.phase_test(pairs, m, along)]]
    chi, df, segment_p = leak.section_chi2(pairs)
    n = len(plain)
    prime = [k % N for k in islice(ciphers.primes(), n)]
    totient = [k % N for k in islice(ciphers.totient_prime_stream(), n)]
    key_pairs = {
        "DIVINITY/CIRCUMFERENCES": ([module.DIVINITY[i % len(module.DIVINITY)] for i in range(n)],
                                    [module.CIRCUMFERENCES[i % len(module.CIRCUMFERENCES)] for i in range(n)]),
        "phi(prime)/primes": (totient, prime),
    }
    switches = []
    for name, (k1, k2) in key_pairs.items():
        for kind, encrypt in (("ideal", leak.key_switch_ideal), ("literal", leak.key_switch_literal)):
            hits, total = leak.doublet_rate(encrypt(plain, k1, k2))
            switches.append({"keys": name, "kind": kind, "hits": hits, "pairs": total,
                             "lp2_upper_tail": leak.poisson_sf(86, hits / total * len(pairs)) if hits else 0.0})
    dp = stats.difference_distribution(plain)
    emit(HERE / "results.json", {
        "source_tests_passed": result.testsRun, "pairs": len(pairs), "doublets": differences[0],
        "H_L1": {"difference_counts": differences, "z": z},
        "H_L2": {"break_counts": leak.doublets_by_break(pairs)},
        "H_L3": {"periods": periods, "source_bonferroni": .01 / 62},
        "H_L4": {"chi2": chi, "df": df, "p": segment_p,
                 "dispersion_500": leak.dispersion_index(pairs, 500)},
        "H_L5": {"key_switches": switches},
        "O_C14": {"solved_plain_difference_model": dp, "repeat_rate": .19,
                  "lp2_llr": leak.skip_next_llr(pairs, dp)}
    })
    print(f"source H/O tests: {result.testsRun}; pairs {len(pairs)}; doublets {differences[0]}")


if __name__ == "__main__":
    main()
