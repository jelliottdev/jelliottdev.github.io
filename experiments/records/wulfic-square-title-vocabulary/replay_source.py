"""Replay Stage I's title-only function from the pinned external source.

Usage: python experiments/records/wulfic-square-title-vocabulary/replay_source.py PATH_TO_WULFIC_CLONE
No source files are written and no code is redistributed.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib
import io
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMIT = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
PINNED = {
    "tools/run_stage_i.py": "7582b46f446338780ed4e3c4429bf3b70a2e1feed061d11ef4cc7f5a2fc962d6",
    "data/canonical/liber_primus_master.txt": "df7eaaa0c92243946803a7a90a7bfdcb36c0eba73f964f3a093c238ab01a5746",
    "data/canonical/liber_primus_translation.txt": "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47",
    "data/corpora/emerson_essays.txt": "a56d5bb419a8c28c4e0187a937c01991ea953817c036ee7f7f835ea2084c03a0",
    "data/corpora/self_reliance.txt": "db053efa73dbd6f7569a6b4459c292ce1e84e755415592de2a9d1db4d1c0cae6",
    "data/corpora/liber_al_vel_legis.txt": "aeadc7374e1aa34342763e3740515c92bfda5902f57b56067a06501bb0cbff66",
    "data/corpora/deor_poem.txt": "be03dbfbc8d02dd6348611c973dd38ba3960c7d06833461783876546171fd143",
}


def main(source: Path) -> None:
    source = source.resolve()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    assert commit == COMMIT
    for relative, digest in PINNED.items():
        assert hashlib.sha256((source / relative).read_bytes()).hexdigest() == digest, relative
    sys.path.insert(0, str(source))
    stage = importlib.import_module("tools.run_stage_i")
    translation = importlib.import_module("tools.lpcore.verify")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        stage.run_title(stage.english_vocabulary(translation.load_translation()))
    assert out.getvalue().encode("utf-8") == (HERE / "source-title-output.txt").read_bytes()
    print("Pinned Stage I title: all 30 source lines and random-key control reproduced byte-for-byte")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Pass the pinned Wulfic checkout path")
    main(Path(sys.argv[1]))
