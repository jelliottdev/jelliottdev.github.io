"""Check every experiment archive and rerun representative scripts in isolation."""
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
            manifest = target / f"EXPERIMENT-{experiment_id}-CONTENTS.json"
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
            if experiment_id in ("lp2-word-order-reversal", "lp2-prime-openings", "lp2-trigram-repeats"):
                for script, args in (("run.py", ["--check"]), ("check.py", [])):
                    result = subprocess.run(
                        [sys.executable, str(target / f"experiments/records/{experiment_id}/{script}"), *args],
                        cwd=target, capture_output=True, text=True, encoding="utf-8", timeout=60)
                    assert result.returncode == 0, result.stdout + result.stderr
        print(f"PASS: all {len(records)} experiment bundles preserve declared files and hashes; "
              "segment-order, ordinary-prime and trigram runners/checkers pass in isolated extractions.")


if __name__ == "__main__":
    main()
