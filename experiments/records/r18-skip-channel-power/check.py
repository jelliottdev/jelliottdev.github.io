"""Independent arithmetic check of the B5 source receipt and completed replay."""
import hashlib
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    original = json.loads((HERE / "source-b5_skipchannel.json").read_text(encoding="utf-8"))
    fresh = json.loads((HERE / "replayed-b5_skipchannel.json").read_text(encoding="utf-8"))
    assert sha(HERE / "source-b5_skipchannel.json") == plan["source_result_sha256"]["b5_skipchannel.json"]
    assert fresh["true_key_on_plant"] == original["true_key_on_plant"]
    # This one stored projection differs by 0.0077 skips from the pinned
    # executable. Keep that difference visible instead of masking it.
    assert abs(fresh["expected_skips_true_key"] -
               original["expected_skips_true_key_rho_L"]) < 0.01
    assert fresh["expected_skips_true_key"] != original["expected_skips_true_key_rho_L"]
    for old_name, new_name, key in (
        ("wrong_on_plant", "wrong_keys_on_plant", "plant"),
        ("wrong_on_real", "wrong_keys_on_real_ciphertext", "real"),
    ):
        rows = original[old_name]
        assert len(rows) == 40
        skips = [row[1] for row in rows]
        scores = [row[0] for row in rows]
        summary = original[new_name]
        replay = fresh[new_name]
        assert replay["n"] == summary["n"] == 40
        assert abs(statistics.mean(skips) - replay["mean_skips"]) < 1e-12
        assert abs(statistics.stdev(skips) - replay["sd_skips"]) < 1e-12
        assert min(skips) == replay["min"] and max(skips) == replay["max"]
        assert abs(statistics.mean(scores) - summary["mean_score"]) < 1e-12
        assert max(scores) == summary["max_score"]
    for key in ("wrong_keys_on_plant", "wrong_keys_on_real_ciphertext"):
        for field in ("n", "mean_skips", "sd_skips", "min", "max"):
            assert fresh[key][field] == original[key][field]
    plant = fresh["wrong_keys_on_plant"]
    real = fresh["wrong_keys_on_real_ciphertext"]
    assert abs((fresh["true_key_on_plant"]["n_skips"] - plant["mean_skips"]) /
               plant["sd_skips"] - fresh["separation_sd_true_vs_wrong"]) < 1e-12
    assert fresh["separation_sd_true_vs_wrong"] == original["separation_sd_true_vs_wrong"]
    candidates = fresh["real_candidates_full_book"]
    assert len(candidates) == 20
    assert all(abs((row["n_skips"] - real["mean_skips"]) / real["sd_skips"] -
                   row["skip_z_vs_wrong_null"]) < 1e-12 for row in candidates)
    assert all(a["skip_z_vs_wrong_null"] >= b["skip_z_vs_wrong_null"]
               for a, b in zip(candidates, candidates[1:]))
    assert max(row["skip_z_vs_wrong_null"] for row in candidates) < 3
    print("PASS: 40+40 saved wrong-key rows, source summaries, complete 20-candidate ranking")


if __name__ == "__main__":
    main()
