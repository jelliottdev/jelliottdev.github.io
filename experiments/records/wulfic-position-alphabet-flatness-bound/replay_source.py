"""Optional complete Stage T replay from the pinned external checkout.

Usage: python experiments/records/wulfic-position-alphabet-flatness-bound/replay_source.py PATH_TO_WULFIC_CLONE
The source code is not redistributed; this writes its result only to a temporary file.
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
    "tools/run_stage_t.py": "a390194325bd8bc969200f37da86cfb341037042c3bad457fcfcde478e18477d",
    "tools/lpcore/flatness.py": "b404d3c76c930c171adfac1c40631a027a725cb82453fbb639a081417b676c79",
    "data/canonical/liber_primus_master.txt": "df7eaaa0c92243946803a7a90a7bfdcb36c0eba73f964f3a093c238ab01a5746",
    "data/canonical/liber_primus_translation.txt": "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47",
}


def main(source: Path) -> None:
    source = source.resolve()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    assert commit == COMMIT, (commit, COMMIT)
    for relative, digest in PINNED.items():
        assert hashlib.sha256((source / relative).read_bytes()).hexdigest() == digest, relative
    sys.path.insert(0, str(source))
    module = importlib.import_module("tools.run_stage_t")
    with tempfile.TemporaryDirectory(prefix="liberpedia-stage-t-") as directory:
        module.OUT_PATH = Path(directory) / "stage_t_results.tsv"
        original_argv = sys.argv
        try:
            sys.argv = ["run_stage_t.py"]
            assert module.main() == 0
        finally:
            sys.argv = original_argv
        assert module.OUT_PATH.read_bytes() == (HERE / "source-stage_t_results.tsv").read_bytes()
    print("Pinned source Stage T: all 45 rows reproduced byte-for-byte")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Pass the path to the pinned Wulfic checkout")
    main(Path(sys.argv[1]))
