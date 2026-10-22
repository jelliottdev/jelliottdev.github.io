"""Check every experiment archive and rerun representative scripts in isolation."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from verify_bundle import verify

ROOT = Path(__file__).resolve().parents[1]


def main():
    records = json.loads((ROOT / "data/experiments.json").read_text(encoding="utf-8"))["records"]
    with tempfile.TemporaryDirectory(prefix="experiment-bundles-", dir=ROOT.parent) as folder:
        workspace = Path(folder).resolve()
        assert workspace.is_relative_to(ROOT.parent.resolve()) and workspace != ROOT
        for record in records:
            experiment_id = record["id"]
            target = workspace / experiment_id
            target.mkdir()
            with zipfile.ZipFile(ROOT / "downloads/experiments" / f"{experiment_id}.zip") as archive:
                for name in archive.namelist():
                    assert (target / name).resolve().is_relative_to(target.resolve()), name
                archive.extractall(target)
            instructions = (target / f"START-HERE-{experiment_id}.txt").read_text(encoding="utf-8")
            for field in ("question", "finding", "limitations", "outcome"):
                assert record[field] in instructions, (experiment_id, field)
            assert record["reproduction"]["command"] in instructions
            assert "Python 3.9 or later" in instructions
            manifest = target / f"EXPERIMENT-{experiment_id}-CONTENTS.json"
            assert f"python scripts/verify_bundle.py {manifest.name}" in instructions
            checked, problems = verify(manifest)
            assert checked and not problems, (experiment_id, problems)
            members = {item["path"]: item for item in json.loads(manifest.read_text())}
            image_manifest = target / f"EXPERIMENT-{experiment_id}-IMAGE-INPUTS.json"
            images = ({item["path"]: item for item in json.loads(image_manifest.read_text())}
                      if image_manifest.exists() else {})
            for item in record["reproduction"]["inputs"] + record["reproduction"]["outputs"]:
                actual = members.get(item["path"], images.get(item["path"]))
                assert actual and actual["sha256"] == item["sha256"], item["path"]
            assert members[record["reproduction"]["script"]]["sha256"] == record["script_sha256"]
            assert all(name.startswith("images/") for name in images)
            assert not set(members) & set(images)
            assert (target / f"experiments/records/{experiment_id}/record.json").is_file()
            plan_file = target / f"experiments/records/{experiment_id}/plan.json"
            if plan_file.exists():
                plan = json.loads(plan_file.read_text(encoding="utf-8"))
                results_file = plan_file.with_name("results.json")
                if results_file.exists():
                    result_record = json.loads(results_file.read_text(encoding="utf-8"))
                    if "plan_sha256" in result_record:
                        assert result_record["plan_sha256"] == hashlib.sha256(plan_file.read_bytes()).hexdigest(), experiment_id
                for dependency in plan.get("inputs", []):
                    name = dependency["path"]
                    if name in images:
                        # Original page JPEGs are supplied by the separate image bundle.
                        assert images[name]["sha256"] == dependency["sha256"], (experiment_id, name)
                    else:
                        data = (target / name).read_bytes()
                        assert hashlib.sha256(data).hexdigest() == dependency["sha256"], (experiment_id, name)
            if experiment_id in ("lp2-word-order-reversal", "lp2-prime-openings", "lp2-fibonacci-openings", "lp2-totient-openings", "lp2-trigram-repeats", "prime-distance-reverse-add"):
                for script, args in (("run.py", ["--check"]), ("check.py", [])):
                    result = subprocess.run(
                        [sys.executable, str(target / f"experiments/records/{experiment_id}/{script}"), *args],
                        cwd=target, capture_output=True, text=True, encoding="utf-8", timeout=60)
                    assert result.returncode == 0, (experiment_id, script, result.stdout + result.stderr)
        print(f"PASS: all {len(records)} experiment bundles preserve declared files and hashes; "
              "segment-order, ordinary-prime, Fibonacci, totient, trigram and reverse-add runners/checkers pass in isolated extractions.")


if __name__ == "__main__":
    main()
