"""Optionally rerun the unmodified pinned Stage AE source into a temporary folder."""
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
    "tools/run_stage_ae.py": "31e5fd74bd991cbbb08ea0dba46eba3d541afd75594b3b73204602a889da252f",
    "tools/run_stage_ac.py": "1bf714c5d4f60e4b75ef297cad19cee58f99744fce6d3eaead6417828a2359ef",
    "data/canonical/liber_primus_master.txt": "df7eaaa0c92243946803a7a90a7bfdcb36c0eba73f964f3a093c238ab01a5746",
    "data/canonical/liber_primus_translation.txt": "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47",
    "data/corpora/emerson_essays.txt": "a56d5bb419a8c28c4e0187a937c01991ea953817c036ee7f7f835ea2084c03a0",
}
NAMES = ("stage_ae_lags.tsv", "stage_ae_controls.tsv")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--verify-output-dir", type=Path)
    args = parser.parse_args()
    root = args.source_dir.resolve()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip() == COMMIT
    for name, expected in PINNED.items():
        assert sha(root / name) == expected, name

    def verify(folder: Path) -> None:
        for name in NAMES:
            assert sha(folder / name) == sha(HERE / f"source-{name}"), name

    if args.verify_output_dir:
        verify(args.verify_output_dir.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="liberpedia-wulfic-stage-ae-") as directory:
            folder = Path(directory)
            code = ("from pathlib import Path; import tools.run_stage_ae as m; "
                    "p=Path(__import__('sys').argv[1]); "
                    "m.LAGS_PATH=p/'stage_ae_lags.tsv'; m.CONTROLS_PATH=p/'stage_ae_controls.tsv'; "
                    "raise SystemExit(m.main([]))")
            subprocess.run([sys.executable, "-c", code, str(folder)], cwd=root, check=True)
            verify(folder)
    print("Pinned Stage AE source output reproduced byte-for-byte: OK")
