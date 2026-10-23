"""Optional full upstream Stage AB replay from a separately cloned, pinned source.

This script never overwrites the upstream repository's checked-in findings.
Usage: python replay_source.py --source-dir PATH_TO_WULFIC_CLONE
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMIT = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
PINNED = {
    "tools/run_stage_ab.py": "b9318f81b4c20f6b769aafd3a4f683946a5906eae2723ed43b8293a70648ad91",
    "tools/run_stage_z.py": "0dd32c394b50b6066bef16abfb21818ed61c8ca94ed47eb113446b00dad3a23a",
    "tools/lpcore/corpus.py": "e452ec79e0df2d6acc8eb5343bdfedf32e63dbaf5a5a9a6bfe1291d8b9e6c9f4",
    "tools/lpcore/keys.py": "551f5c0c4746c934b2317b22562fd95db969600dda2bfbe2a3ab7c359255cafc",
    "data/canonical/liber_primus_master.txt": "df7eaaa0c92243946803a7a90a7bfdcb36c0eba73f964f3a093c238ab01a5746",
    "data/canonical/liber_primus_translation.txt": "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47",
    "data/corpora/emerson_essays.txt": "a56d5bb419a8c28c4e0187a937c01991ea953817c036ee7f7f835ea2084c03a0",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.source_dir.resolve()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if commit != COMMIT:
        raise SystemExit(f"source revision differs: {commit}")
    for name, expected in PINNED.items():
        actual = sha(root / name)
        if actual != expected:
            raise SystemExit(f"source input differs: {name}: {actual}")
    with tempfile.TemporaryDirectory(prefix="liberpedia-stage-ab-") as temporary:
        tmp = Path(temporary)
        code = (
            "from pathlib import Path; import tools.run_stage_ab as m; "
            "m.RESULTS_PATH=Path(__import__('sys').argv[1]); "
            "m.CONTROLS_PATH=Path(__import__('sys').argv[2]); "
            "raise SystemExit(m.main([]))"
        )
        subprocess.run([sys.executable, "-c", code, str(tmp / "stage_ab_results.tsv"),
                        str(tmp / "stage_ab_controls.tsv")], cwd=root, check=True)
        for name in ("stage_ab_results.tsv", "stage_ab_controls.tsv"):
            actual = sha(tmp / name)
            expected = sha(HERE / f"source-{name}")
            if actual != expected:
                raise SystemExit(f"replayed {name} differs: {actual} vs {expected}")
    print("Pinned Stage AB source outputs reproduced byte-for-byte: OK")


if __name__ == "__main__":
    main()
