"""Replay three pinned upstream finite-field scripts without redistributing them."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT.parent / "sources" / "emmanuel-p20-lf"
RUNS = ("33_boundary_complete_crossvalidation", "35_exact_null_independent_verifier",
        "38_positive_control_plant_and_recover")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args])


def report(source: Path) -> dict:
    plan_bytes = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_bytes)
    for item in plan["local_inputs"]:
        assert sha((ROOT / item["path"]).read_bytes()) == item["sha256"], item["path"]
    assert git(source, "rev-parse", "HEAD").decode().strip() == plan["source_revision"]
    originals = {}
    for item in plan["source_files"]:
        raw = git(source, "show", f"{plan['source_revision']}:{item['path']}")
        assert sha(raw) == item["sha256"], item["path"]
        originals[item["path"]] = raw
    manifest = originals["MANIFEST_SHA256.tsv"].decode("utf-8").splitlines()[1:]
    indexed = set(git(source, "ls-tree", "-r", "--name-only", "HEAD").decode().splitlines())
    missing = sorted(path for line in manifest for _, path in [line.split("\t", 1)] if path not in indexed)
    assert missing == [".github/workflows/verify.yml", ".gitignore"]
    regenerated = {}
    with tempfile.TemporaryDirectory(prefix="liberpedia-p20-") as folder:
        scratch = Path(folder)
        input_path = scratch / "analysis/evidence/boundary_numeric_evidence.json"
        input_path.parent.mkdir(parents=True)
        input_path.write_bytes(originals["analysis/evidence/boundary_numeric_evidence.json"])
        for name in RUNS:
            source_path = f"analysis/{name}.py"
            script_path = scratch / source_path
            script_path.write_bytes(originals[source_path])
            subprocess.run([sys.executable, str(script_path)], cwd=script_path.parent,
                           check=True, capture_output=True, text=True, timeout=180)
            result_path = scratch / f"analysis/{name}.json"
            current = json.loads(result_path.read_text(encoding="utf-8"))
            committed = json.loads(originals[f"analysis/{name}.json"])
            assert current == committed, name
            regenerated[name] = current
    main = regenerated[RUNS[0]]
    independent = regenerated[RUNS[1]]
    planted = regenerated[RUNS[2]]
    counts = main["global_joint_affine_fit_counts"]
    assert main["global_row_assignments"] == independent["global_row_assignments"] == 34020
    assert counts == independent["global_joint_affine_fit_counts"] == {
        "4,4":0,"4,5":0,"5,4":0,"5,5":0,"5,6":0,"6,5":0,"6,6":5}
    null = independent["c18_saturated"]
    assert null["observed_hits"] == 5 and null["training_assignments"] == 3780
    assert abs(null["exact_p_hits_ge_observed"] - .5523905497673823) < 1e-15
    assert planted["exact_planted_law_recovered"] == 2
    assert planted["mutated_control_exact_planted_law_recovered"] == 0
    return {
        "schema": "liberpedia-public-p20-static-boundary-v1",
        "plan_sha256": sha(plan_bytes),
        "source_revision": plan["source_revision"],
        "source_input_sha256": next(item["sha256"] for item in plan["source_files"]
                                    if item["path"].endswith("boundary_numeric_evidence.json")),
        "source_manifest_missing_git_tree": missing,
        "source_script_semantic_matches": {name: True for name in RUNS},
        "numeric_contexts": main["contexts"],
        "assignment_count": 34020,
        "fit_counts": counts,
        "leave_one": main["leave_one_summary"],
        "leave_two": main["leave_two_summary"],
        "exact_c18_null": {"training_assignments": null["training_assignments"],
                           "holdout_menu_size": null["holdout_menu_size"],
                           "observed_hits": null["observed_hits"],
                           "expected_hits": null["exact_uniform_distinct_menu_expected_hits"],
                           "exact_p_hits_ge_observed": null["exact_p_hits_ge_observed"],
                           "multiplicity_histogram": null["prediction_multiplicity_histogram"]},
        "planted_controls": {"exact_low_complexity_laws_recovered": 2,
                             "mutated_exact_laws_recovered": 0},
        "scope_note": "Conditional on the source's bundled normalized numeric menus; no original raw workspace or page plaintext is reconstructed."
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE,
                        help="Local clone of the pinned upstream Git repository")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report(args.source.resolve())
    path = HERE / "results.json"
    if args.check:
        assert result == json.loads(path.read_text(encoding="utf-8"))
        print("PASS: source scripts 33/35/38, committed outputs, exact null and planted controls")
    else:
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(result["fit_counts"], result["exact_c18_null"])
