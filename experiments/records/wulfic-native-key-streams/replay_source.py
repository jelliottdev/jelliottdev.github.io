"""Optional exact Stage I/M source replay from a pinned external checkout."""
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
    "tools/run_stage_i.py": "7582b46f446338780ed4e3c4429bf3b70a2e1feed061d11ef4cc7f5a2fc962d6",
    "tools/run_stage_m.py": "eefb61156135a799039452e67a4973cd28b22952fcd2c643630fedbd70a5a7bb",
    "tools/lpcore/detect.py": "fc0f0fb715e888f9ffe0ee434f786f273a0ee939ab050d54ff4e369a8f301eeb",
    "tools/lpcore/keys.py": "551f5c0c4746c934b2317b22562fd95db969600dda2bfbe2a3ab7c359255cafc",
    "data/canonical/liber_primus_master.txt": "df7eaaa0c92243946803a7a90a7bfdcb36c0eba73f964f3a093c238ab01a5746",
    "data/canonical/liber_primus_translation.txt": "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--verify-output-dir", type=Path,
                        help="Validate a completed rerun without repeating it")
    args = parser.parse_args()
    root = args.source_dir.resolve()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    assert commit == COMMIT, commit
    for name, expected in PINNED.items():
        assert sha(root / name) == expected, name

    def verify(folder: Path) -> None:
        for stage in ("i", "m"):
            name = f"stage_{stage}_candidates.tsv"
            assert sha(folder / name) == sha(HERE / f"source-{name}"), name

    if args.verify_output_dir:
        verify(args.verify_output_dir.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="liberpedia-wulfic-native-keys-") as directory:
            folder = Path(directory)
            for stage in ("i", "m"):
                code = (
                    f"from pathlib import Path; import tools.run_stage_{stage} as m; "
                    "m.OUT_PATH=Path(__import__('sys').argv[1]); "
                    + ("raise SystemExit(m.main([]))" if stage == "i" else "raise SystemExit(m.main())")
                )
                subprocess.run([sys.executable, "-c", code,
                                str(folder / f"stage_{stage}_candidates.tsv")], cwd=root, check=True)
            verify(folder)
    print("Pinned Stage I/M source grids reproduced byte-for-byte: OK")
