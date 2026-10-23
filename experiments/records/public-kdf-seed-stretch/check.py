"""Check the pinned KDF grid, source inputs and deterministic replay outputs."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
LP = HERE / "source/liber-primus"
KDF = Path("analysis/round15/KDF")
EXPECTED_DICTIONARY = "8c324143df959e5446a34e0d2d0703b7aea781ee0452dcff24e3a6f023c6f347"
EXPECTED_GRID = 534 * 27 * 3 * 2 * 2 * 2 * 2


def read(root: Path, name: str) -> dict:
    return json.loads((root / KDF / name).read_text(encoding="utf-8"))


def secret_dictionary_hash() -> tuple[int, str]:
    """Rebuild ordered seeds from the packaged, exact source code and inputs."""
    script = LP / KDF / "sweep.py"
    spec = importlib.util.spec_from_file_location("archived_kdf_sweep", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    seeds = module.build_secrets()
    raw = json.dumps([(label, value.hex()) for label, value in seeds],
                     separators=(",", ":")).encode()
    return len(seeds), hashlib.sha256(raw).hexdigest()


def verify_k1_console(output: str, positive_control: dict) -> None:
    """Check the live D3 output: the source executable does not write JSON."""
    checks = (
        ("English plaintext eng_norm target", "english_target", False),
        ("RIGID decode, CORRECT seed", "rigid_correct_seed", False),
        ("BEAM  decode, CORRECT seed", "beam_correct_seed", False),
        ("BEAM  decode, WRONG seed", "beam_wrong_seed", False),
        ("null (shuffled P, N=200)", "null_max_N200", True),
        ("char-recovery of planted plaintext", "char_recovery", False),
    )
    for marker, key, use_last in checks:
        line = next((line for line in output.splitlines() if marker in line), None)
        assert line is not None, f"Missing live K1 line: {marker}"
        values = re.findall(r"(?<![A-Za-z0-9])-?\d+\.\d+", line)
        assert values, f"Missing live K1 measurement: {marker}"
        measured = float(values[-1] if use_last else values[0])
        assert math.isclose(measured, positive_control[key], abs_tol=0.0005), key
    gate_line = next((line for line in output.splitlines()
                      if line.startswith("GATE (beam recovers correct seed")), "")
    assert gate_line.endswith(": PASS"), "The live K1 gate did not pass"


def verify(root: Path = LP) -> dict:
    count, digest = secret_dictionary_hash()
    assert (count, digest) == (534, EXPECTED_DICTIONARY)
    # This is the actual per-target Stage A grid. K2 runs the same grid on a
    # planted ciphertext first; it is a power control, not extra LP2 coverage.
    assert EXPECTED_GRID == 692064

    saved_a = read(root, "results_A.json")
    saved_g = read(root, "results_gates.json")
    saved_s = read(root, "results_summary.json")
    original_a = read(LP, "original_results_A.json")
    original_g = read(LP, "original_results_gates.json")
    original_s = read(LP, "original_results_summary.json")

    d3 = json.loads((LP / "analysis/round12/D3/original_results.json").read_text(encoding="utf-8"))
    verify_k1_console((HERE / "k1_control_output.txt").read_text(encoding="utf-8"),
                      d3["positive_control"])

    assert saved_g == original_g, "The positive controls changed"
    assert saved_g["K1"]["passed"] is True and saved_g["K2"]["passed"] is True
    assert saved_g["K1"]["char_recovery"] >= .90
    assert saved_g["K2"]["rank1"]["secret_hex"] == b"THE PRIMES ARE SACRED".hex()
    assert saved_g["K2"]["rank1"]["kdf"] == "pbkdf2_sha256_10000"
    assert saved_g["K2"]["rank1"]["salt"] == "3301"
    assert saved_g["K2"]["rank1"]["score"] > -5.5

    for field in ("stage", "n_decodes", "best_score", "bar", "hit", "over_bar", "sample_n"):
        assert saved_a[field] == original_a[field], f"Stage A mismatch: {field}"
    # imap_unordered can exchange rows with exactly equal scores. Preserve the
    # complete selected set and its winning row, not incidental tie order.
    canonical = lambda rows: sorted(json.dumps(row, sort_keys=True) for row in rows)
    assert canonical(saved_a["top50"]) == canonical(original_a["top50"])
    assert saved_a["top50"][0] == original_a["top50"][0]
    for field in ("sample_mean", "sample_sd"):
        assert math.isclose(saved_a[field], original_a[field], abs_tol=1e-10)
    assert saved_a["n_decodes"] == EXPECTED_GRID
    assert len(saved_a["top50"]) == 50
    assert saved_a["best_score"] == saved_a["top50"][0]["score"]
    assert saved_a["best_score"] < -5.5 and not saved_a["over_bar"]
    assert all(row["score"] < -5.5 for row in saved_a["top50"])

    for field in ("verdict", "smoke_limit", "gates", "gates_passed", "best_score",
                  "bar", "null_mean", "null_max", "n_over_bar", "over_bar",
                  "secrets", "kdfs", "total_decodes"):
        assert saved_s[field] == original_s[field], f"Summary mismatch: {field}"
    assert saved_s["total_decodes"] == EXPECTED_GRID
    assert saved_s["verdict"] == "NEGATIVE" and saved_s["n_over_bar"] == 0
    assert saved_s["stages"][0]["stage"] == "A"
    assert saved_s["stages"][0]["n_decodes"] == EXPECTED_GRID
    return {"secrets": count, "dictionary_sha256": digest, "kdfs": saved_s["kdfs"],
            "lp2_decodes": saved_s["total_decodes"], "best_score": saved_a["best_score"],
            "bar": saved_s["bar"], "controls_passed": saved_s["gates_passed"],
            "matches_pinned_source": True}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
