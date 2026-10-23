"""Supplementary in-domain one-tap planted control; not source history."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    diagnostic = json.loads((HERE / "diagnostic-plan.json").read_text(encoding="utf-8"))
    assert diagnostic["source_replay_plan_sha256"] == sha(HERE / "plan.json")
    root = args.source_root.resolve()
    assert subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip() == plan["source_revision"]
    script = root / "liber-primus/analysis/campaign18_skip/ctfeedback_coeffs.py"
    assert sha(script) == plan["source_sha256"]["analysis/campaign18_skip/ctfeedback_coeffs.py"]
    spec = importlib.util.spec_from_file_location("pinned_coeffs", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    p = mod.eng_to_idx(diagnostic["plaintext"])
    cases = []
    for plant in diagnostic["plants"]:
        c0, a1, sign = plant["seed_constant"], plant["a1"], plant["sign"]
        cipher = []
        for i, value in enumerate(p):
            feedback = a1 * cipher[-1] if i else 0
            cipher.append((value - sign * (c0 + feedback)) % 29)
        # Independently constructed ciphertext must equal source encoder.
        source_cipher = mod.SR.encipher_ctfeedback(p, mod.const_seed(c0, len(p)*5),
                                                   k=1, coeffs=[0, a1], sign=sign,
                                                   supp=.83, seed=3301)
        assert cipher == source_cipher
        rows = []
        for coeff in mod.coeff_grid(1):
            for seed_constant in (0, 1):
                for direction in (-1, 1):
                    score, decoded = mod.decode_with_coeffs(cipher,
                        mod.const_seed(seed_constant, len(p)*5), 1, coeff, direction, 0)
                    rows.append({"coefficient": coeff[1], "seed_constant": seed_constant,
                                 "sign": direction, "score": score,
                                 "plaintext_match": sum(a == b for a, b in zip(decoded["plain_idx"], p))/len(p)})
        assert len(rows) == 112
        rows.sort(key=lambda r: -r["score"])
        true = next(r for r in rows if r["coefficient"] == a1 and r["seed_constant"] == c0 and r["sign"] == sign)
        unit = next(r for r in rows if r["coefficient"] == 1 and r["seed_constant"] == c0 and r["sign"] == sign)
        cases.append({"plant": plant, "rune_length": len(p), "cipher_sha256": hashlib.sha256(bytes(cipher)).hexdigest(),
                      "true": true, "unit": unit,
                      "true_rank": 1 + sum(r["score"] > true["score"] + 1e-12 for r in rows),
                      "best": rows[0], "all_rows": rows})
    report = {"schema": "dukotah-ctfeedback-in-domain-plant-results-v1",
              "plan_sha256": sha(HERE / "diagnostic-plan.json"), "cases": cases}
    output = HERE / "diagnostic-results.json"
    if args.check:
        assert report == json.loads(output.read_text(encoding="utf-8"))
        print("PASS: two source-domain plants and 224 one-tap decodes reproduce")
    else:
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
        for c in cases:
            print("seed", c["plant"]["seed_constant"], "true", c["true"]["score"],
                  "match", c["true"]["plaintext_match"], "rank", c["true_rank"],
                  "unit", c["unit"]["score"], "best", c["best"])


if __name__ == "__main__":
    main()
