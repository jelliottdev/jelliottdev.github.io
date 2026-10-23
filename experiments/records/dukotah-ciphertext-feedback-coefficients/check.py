"""Check the exact source grid, gate, printed winners and in-domain plants."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
PAGE = re.compile(r"page (\d+) \((\d+) runes, (\d+)s\): best=([-\d.]+)")
META = re.compile(r"meta k,coeffs,seed,sign,o = (.*)")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse(text):
    found = []
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        match = PAGE.match(line.strip())
        if not match:
            continue
        meta = META.match(lines[idx+1].strip())
        assert meta is not None
        page, length, elapsed, score = match.groups()
        k, coeffs, seed, sign, offset = ast.literal_eval(meta.group(1))
        found.append({"source_page": int(page), "rune_length": int(length),
                      "seconds": int(elapsed), "score_rounded": float(score),
                      "k": k, "coeffs": coeffs, "seed": seed,
                      "sign": sign, "offset": offset})
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    diag = json.loads((HERE / "diagnostic-results.json").read_text(encoding="utf-8"))
    source = args.source_root.resolve()
    assert subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip() == plan["source_revision"]
    lp = source / "liber-primus"
    for rel, digest in plan["source_sha256"].items():
        assert sha(lp / rel) == digest
    script = lp / "analysis/campaign18_skip/ctfeedback_coeffs.py"
    spec = importlib.util.spec_from_file_location("pinned_coeffs_check", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    counts = [len(module.coeff_grid(k)) for k in (1,2,3)]
    assert counts == [28, 840, 4204]
    assert sum(counts) * 2 * 2 * 3 == plan["source_domain"]["total_decodes"] == 60864
    stdout = (HERE / "source-replay-stdout.txt").read_text(encoding="utf-8")
    assert "GATE: PASS" in stdout and "VERDICT: NULL (noise floor)" in stdout
    pages = parse(stdout)
    assert [r["source_page"] for r in pages] == plan["source_pages"]
    assert [r["rune_length"] for r in pages] == plan["source_page_lengths"]
    source_pages = module.load_pages()
    rescored = []
    for row in pages:
        assert row["coeffs"] in module.coeff_grid(row["k"])
        assert row["seed"] in ("const0", "const1")
        assert row["sign"] in (-1,1) and row["offset"] == 0
        C = source_pages[row["source_page"]]
        # Independent feedback recurrence, passed directly to the pinned beam.
        terms = [0] * len(C)
        for i in range(row["k"], len(C)):
            terms[i] = sum(row["coeffs"][t] * C[i-t] for t in range(1,row["k"]+1)) % 29
        seed_value = int(row["seed"][-1])
        seed = module.const_seed(seed_value, 4000)
        check = module.SR._feedback_beam(C, seed, terms, row["sign"], 0, 250, 3)
        assert abs(check["score"] - row["score_rounded"]) <= 0.0051
        rescored.append(check["score"])
    assert all(case["true"]["plaintext_match"] == 1 for case in diag["cases"])
    assert all(case["true_rank"] == 1 for case in diag["cases"])
    assert all(case["true"]["score"] > -5.2 for case in diag["cases"])
    assert all(case["unit"]["score"] < -5.5 for case in diag["cases"])
    historical = [-6.86, -6.91, -6.89]  # pinned COVERAGE-MATRIX.md prose
    summary = {
        "schema": "dukotah-ctfeedback-coefficient-source-replay-results-v1",
        "plan_sha256": sha(HERE / "plan.json"),
        "diagnostic_plan_sha256": sha(HERE / "diagnostic-plan.json"),
        "stdout_sha256": sha(HERE / "source-replay-stdout.txt"),
        "source_grid_coefficients": counts,
        "source_grid_total_decodes": 60864,
        "source_gate_pass": True,
        "page_winners": [{**row, "rescored_exact": exact,
                          "source_prose_score_rounded": old,
                          "difference_from_source_prose": round(row["score_rounded"] - old,2)}
                         for row, exact, old in zip(pages, rescored, historical)],
        "all_below_source_signal_threshold": all(r["score_rounded"] < -5.2 for r in pages),
        "in_domain_plant_count": len(diag["cases"]),
        "in_domain_one_tap_cases": sum(len(c["all_rows"]) for c in diag["cases"]),
        "interpretation": "The current pinned executable supports no reading on three source pages. Two published prose maxima differ from this replay. In-domain plants pass, but constant seeds make key skips observationally irrelevant."
    }
    output = HERE / "results.json"
    if args.check:
        saved = json.loads(output.read_text(encoding="utf-8"))
        # A fresh full source run includes new wall times and stdout bytes.
        # Compare the scientific fields while retaining the original receipt.
        current = json.loads(json.dumps(summary))
        previous = json.loads(json.dumps(saved))
        current.pop("stdout_sha256")
        previous.pop("stdout_sha256")
        for rows in (current["page_winners"], previous["page_winners"]):
            for row in rows:
                row.pop("seconds")
        assert current == previous
        print("PASS: grid counts, source gate, three winners, two plants and score discrepancies")
    else:
        output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(summary["page_winners"], indent=2))


if __name__ == "__main__":
    main()
