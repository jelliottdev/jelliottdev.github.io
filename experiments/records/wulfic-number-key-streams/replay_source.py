"""Optional complete AG/AH replay against a separately cloned pinned source.

Usage: python replay_source.py --source-dir PATH_TO_WULFIC_CLONE
Outputs are written only to a temporary folder and compared byte-for-byte.
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
    "tools/run_stage_ag.py": "46262fbf32c882fc3c6fef37937326e5cf27763e8aa430dafae338da25b6317b",
    "tools/run_stage_ah.py": "d6471ef1511252883a6813755a72a9e888712ecc06d4b449c56fa57d0c090a5d",
    "tools/lpcore/fastdetect.py": "b98c876e2963ac257164141f0100e5cf0e034070f16628816e2544ba493530d4",
    "tools/lpcore/detect.py": "fc0f0fb715e888f9ffe0ee434f786f273a0ee939ab050d54ff4e369a8f301eeb",
    "tools/lpcore/keys.py": "551f5c0c4746c934b2317b22562fd95db969600dda2bfbe2a3ab7c359255cafc",
    "tools/lpcore/ciphers.py": "80876bc3f4a9b22fdfeb459fcb6500ed1d4fe3ee346afc26ac04d38c3052c566",
    "data/canonical/liber_primus_master.txt": "df7eaaa0c92243946803a7a90a7bfdcb36c0eba73f964f3a093c238ab01a5746",
    "data/canonical/liber_primus_translation.txt": "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--verify-output-dir", type=Path,
                        help="Validate an already completed full replay without running it again")
    args = parser.parse_args()
    root = args.source_dir.resolve()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if commit != COMMIT:
        raise SystemExit(f"source revision differs: {commit}")
    for name, expected in PINNED.items():
        actual = sha(root / name)
        if actual != expected:
            raise SystemExit(f"source input differs: {name}: {actual}")

    def verify(folder: Path) -> None:
        for stage in ("ag", "ah"):
            for kind in ("candidates", "controls"):
                name = f"stage_{stage}_{kind}.tsv"
                actual = sha(folder / name)
                expected = sha(HERE / f"source-{name}")
                if actual != expected:
                    raise SystemExit(f"replayed {name} differs: {actual} vs {expected}")

    if args.verify_output_dir:
        verify(args.verify_output_dir.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="liberpedia-wulfic-number-keys-") as directory:
            folder = Path(directory)
            for stage in ("ag", "ah"):
                code = (
                    f"from pathlib import Path; import tools.run_stage_{stage} as m; "
                    "m.CANDIDATES_PATH=Path(__import__('sys').argv[1]); "
                    "m.CONTROLS_PATH=Path(__import__('sys').argv[2]); "
                    "raise SystemExit(m.main([]))"
                )
                subprocess.run([sys.executable, "-c", code, str(folder / f"stage_{stage}_candidates.tsv"),
                                str(folder / f"stage_{stage}_controls.tsv")], cwd=root, check=True)
            verify(folder)
    print("Pinned Stage AG/AH source outputs reproduced byte-for-byte: OK")


if __name__ == "__main__":
    main()
