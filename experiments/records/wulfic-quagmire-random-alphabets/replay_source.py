"""Optional exact Stage U replay from its pinned external checkout.

Usage: python experiments/records/wulfic-quagmire-random-alphabets/replay_source.py PATH_TO_WULFIC_CLONE
Writes only a temporary result file; does not change the checkout's tracked table.
"""
from __future__ import annotations

import hashlib
import importlib
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMIT = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
PINNED = {
    "tools/run_stage_u.py": "89e2377ecbea04a6a4699950589b6ffebf7ef0707d9daace69c038fb7498e469",
    "tools/lpcore/quagmire.py": "b8dfb95a688c21ec51a0896b9e0dd309574fa7eaffb6619273a0ea03247cc2b3",
    "data/canonical/liber_primus_master.txt": "df7eaaa0c92243946803a7a90a7bfdcb36c0eba73f964f3a093c238ab01a5746",
    "data/canonical/liber_primus_translation.txt": "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47",
}


def main(source: Path) -> None:
    source = source.resolve()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    assert commit == COMMIT
    for relative, digest in PINNED.items():
        assert hashlib.sha256((source / relative).read_bytes()).hexdigest() == digest, relative
    sys.path.insert(0, str(source))
    module = importlib.import_module("tools.run_stage_u")
    with tempfile.TemporaryDirectory(prefix="liberpedia-stage-u-") as directory:
        module.OUT_PATH = Path(directory) / "stage_u_results.tsv"
        argv = sys.argv
        try:
            sys.argv = ["run_stage_u.py"]
            assert module.main() == 0
        finally:
            sys.argv = argv
        assert module.OUT_PATH.read_bytes() == (HERE / "source-stage_u_results.tsv").read_bytes()
    print("Pinned source Stage U: complete output reproduced byte-for-byte")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Pass the pinned Wulfic checkout path")
    main(Path(sys.argv[1]))
