"""Run advertised examples from an isolated extraction, never the checkout."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="liberpedia-bundle-", dir=ROOT.parent) as folder:
        target = Path(folder).resolve()
        with zipfile.ZipFile(ROOT / "downloads/reference-data.zip") as bundle:
            for member in bundle.namelist():
                if not (target / member).resolve().is_relative_to(target):
                    raise ValueError("Bundle path escapes extraction directory")
            manifest = json.loads(bundle.read("CONTENTS.json"))
            for item in manifest:
                assert hashlib.sha256(bundle.read(item["path"])).hexdigest() == item["sha256"]
            bundle.extractall(target)
        for command in [
            ["scripts/test_reading_concordance.py"],
            ["scripts/reading_concordance.py", "circumference", "--prefix", "--json"],
            ["scripts/reproduce_reading.py", "--check-all"],
            ["scripts/reproduce_prime_sums.py"],
            ["scripts/rune_ioc.py", "--check"],
            ["scripts/reproduce_cover_chain.py"],
            ["scripts/reproduce_cover_rsa.py"],
            ["scripts/reproduce_emerson.py"],
            ["scripts/inspect_visual_records.py"],
        ]:
            result = subprocess.run([sys.executable, *command], cwd=target,
                                    capture_output=True, text=True, encoding="utf-8")
            if result.returncode:
                raise AssertionError(f"{command} failed:\n{result.stdout}\n{result.stderr}")
            print("PASS from extracted bundle:", " ".join(command))
        for flags, name in [([], "warning.txt"), (["--trace"], "warning.csv")]:
            command = [sys.executable, "scripts/reproduce_reading.py", "warning", *flags]
            expected = subprocess.run(command, cwd=target, capture_output=True, check=True).stdout
            saved = subprocess.run([*command, "--output", name], cwd=target,
                                   capture_output=True, check=True)
            assert (target / name).read_bytes() == expected
            expected.decode("utf-8")  # CSV contains original runes, not replacement characters.
            repeated = subprocess.run([*command, "--output", name], cwd=target,
                                      capture_output=True)
            assert repeated.returncode != 0 and b"Output already exists" in repeated.stderr
            assert (target / name).read_bytes() == expected
        for arguments in [["missing-section"], ["--check-all"], ["--list"]]:
            invalid = subprocess.run([sys.executable, "scripts/reproduce_reading.py",
                                      *arguments, "--output", "invalid.txt"],
                                     cwd=target, capture_output=True)
            assert invalid.returncode != 0
            assert not (target / "invalid.txt").exists()
        print("PASS: UTF-8 reading/trace files match stdout; existing files and invalid requests preserved.")
        assert (target / "data/evidence/signature-checks.json").is_file()
        assert (target / "downloads/REFERENCE-DATA-README.txt").is_file()


if __name__ == "__main__":
    main()
