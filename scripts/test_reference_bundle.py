"""Run advertised examples from an isolated extraction, never the checkout."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from urllib.parse import urljoin

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
        # Catch omission or staleness of discovery data independently of the
        # bundle manifest (which can consistently describe an outdated file).
        topics = json.loads((target / "data/topics.json").read_text(encoding="utf-8"))
        assert topics == json.loads((ROOT / "data/topics.json").read_text(encoding="utf-8"))
        topic_text = (target / "reference/topics.txt").read_text(encoding="utf-8")
        for topic in topics:
            assert topic["title"] in topic_text
            assert topic["summary"] in topic_text
            assert topic["basis"] in topic_text
            for link in topic["links"]:
                assert urljoin("https://jelliottdev.github.io/", link["href"]) in topic_text
        print("PASS: bundled topic records match current sources and retain evidence and links")
        for command in [
            ["scripts/test_verify_bundle.py"],
            ["scripts/reproduce_null_example.py"],
            ["scripts/test_enumerate_shifts.py"],
            ["scripts/plot_atbash_pairs.py", "--output", "test-atbash.svg"],
            ["scripts/verify_bundle.py", "REFERENCE-DATA-CONTENTS.json"],
            ["scripts/test_reading_concordance.py"],
            ["scripts/reading_concordance.py", "circumference", "--prefix", "--json"],
            ["scripts/reproduce_reading.py", "--check-all"],
            ["scripts/reproduce_prime_sums.py"],
            ["scripts/check_number_examples.py"],
            ["scripts/rune_ioc.py", "--check"],
            ["scripts/test_rune_entropy.py"],
            ["scripts/rune_entropy.py", "lp2-31"],
            ["scripts/test_rune_ngrams.py"],
            ["scripts/rune_ngrams.py", "lp2-31", "--length", "2"],
            ["scripts/reproduce_cover_chain.py"],
            ["scripts/reproduce_cover_rsa.py"],
            ["scripts/reproduce_emerson.py"],
            ["scripts/inspect_visual_records.py"],
            ["scripts/test_visual_report.py"],
            ["scripts/test_measure_region.py"],
        ]:
            result = subprocess.run([sys.executable, *command], cwd=target,
                                    capture_output=True, text=True, encoding="utf-8")
            if result.returncode:
                raise AssertionError(f"{command} failed:\n{result.stdout}\n{result.stderr}")
            print("PASS from extracted bundle:", " ".join(command))
        sums = json.loads(subprocess.check_output(
            [sys.executable, "scripts/reproduce_prime_sums.py", "--json"], cwd=target))
        compared = {row["page"]: row for row in sums["page_sums"]}
        assert len(compared) == 17
        published = json.loads((target / "data/evidence/known-reading-page-sums.json").read_text(encoding="utf-8"))
        assert published["records"] == sums["page_sums"]
        import csv
        with (target / "exports/known-reading-page-sums.csv").open(encoding="utf-8", newline="") as stream:
            csv_rows = list(csv.DictReader(stream))
        assert csv_rows == [{key: str(value) for key, value in row.items()} for row in sums["page_sums"]]
        assert [compared["lp1-01"][key] for key in
                ["rune_count", "archived_sum", "decoded_sum", "difference"]] == [184, 11417, 7409, -4008]
        assert compared["lp2-57"]["archived_sum"] == compared["lp2-57"]["decoded_sum"] == 3968
        print("PASS: archived and decoded whole-page sums reproduce from the extracted bundle")
        # A self-consistent ZIP can still contain an older script or page record.
        # The square guide now promises both manuscript calculations and token pairs.
        for path in ["scripts/check_number_examples.py", "data/pages/lp1-05.json",
                     "data/pages/lp1-16.json", "data/index.json"]:
            # Git may check text out with LF or CRLF; compare decoded text here.
            # The bundle manifest and reported source hashes still check exact bytes.
            assert (target / path).read_text(encoding="utf-8") == (ROOT / path).read_text(encoding="utf-8"), path
        numbers = json.loads(subprocess.check_output(
            [sys.executable, "scripts/check_number_examples.py"], cwd=target))
        mixed = numbers["lp1_05"]
        assert mixed["line_sums"] == [1033] * 12
        assert mixed["printed_tokens_half_turn_symmetric"] is False
        assert mixed["converted_values_half_turn_symmetric"] is True
        differing = [pair for pair in mixed["half_turn_pairs"]
                     if not pair["same_printed_token"]]
        assert len(mixed["half_turn_pairs"]) == 12 and len(differing) == 5
        assert [(pair["labels"], pair["values"]) for pair in differing] == [
            (["SHADOWS", "CABAL"], [341, 341]),
            (["BUFFERS", "MOURNFUL"], [199, 199]),
            (["CARNAL", "ANALOG"], [320, 320]),
            (["226", "MOBIUS"], [226, 226]),
            (["OBSCURA", "245"], [245, 245]),
        ]
        printed = numbers["lp1_16"]
        assert printed["row_sums"] + printed["column_sums"] + printed["diagonal_sums"] == [3301] * 12
        assert printed["total"] == 16505
        assert printed["half_turn_symmetric"] is True and printed["normal"] is False
        for page, result in [("lp1-05", mixed), ("lp1-16", printed)]:
            assert result["source_sha256"] == hashlib.sha256(
                (target / f"data/pages/{page}.json").read_bytes()).hexdigest()
        print("PASS: both manuscript squares and all five unequal-token pairs reproduce from current bundled inputs")
        csv_result = subprocess.check_output(
            [sys.executable, "scripts/rune_ioc.py", "--format", "csv"], cwd=target)
        assert csv_result.decode("utf-8").replace("\r\n", "\n") == (target / "exports/rune-ioc.csv").read_text(encoding="utf-8")
        print("PASS: recomputed CSV matches the bundled whole-page baseline")
        example = json.loads(subprocess.check_output(
            [sys.executable, "scripts/reproduce_null_example.py", "--json"], cwd=target))
        assert [row["arrangement"] for row in example["arrangements"]] == [
            "AABB", "ABAB", "ABBA", "BAAB", "BABA", "BBAA"]
        assert [row["equal"] for row in example["arrangements"]] == [2, 0, 1, 1, 0, 2]
        assert [row["selected"] for row in example["arrangements"]] == [2, 3, 2, 2, 3, 2]
        tails = example["upper_tails_including_ties"]
        assert tails["equal"] == dict(observed_score=2, at_least_observed=2, total=6, probability="1/3")
        assert tails["selected"] == dict(observed_score=2, at_least_observed=6, total=6, probability="1")
        print("PASS: exact six-arrangement teaching example and JSON tails")
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
        assert (target / "START-HERE.txt").read_bytes() == (
            target / "downloads/REFERENCE-DATA-README.txt").read_bytes()
        reference_manifest = (target / "REFERENCE-DATA-CONTENTS.json").read_bytes()
        with zipfile.ZipFile(ROOT / "downloads/original-images.zip") as images:
            # Check the manifest collision without extracting all images.
            (target / "CONTENTS.json").write_bytes(images.read("CONTENTS.json"))
            (target / "ORIGINAL-IMAGES-CONTENTS.json").write_bytes(
                images.read("ORIGINAL-IMAGES-CONTENTS.json"))
        assert (target / "REFERENCE-DATA-CONTENTS.json").read_bytes() == reference_manifest
        subprocess.run([sys.executable, "scripts/verify_bundle.py",
                        "REFERENCE-DATA-CONTENTS.json"], cwd=target,
                       capture_output=True, check=True)


if __name__ == "__main__":
    main()
